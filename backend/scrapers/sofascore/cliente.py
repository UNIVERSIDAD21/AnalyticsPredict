# -*- coding: utf-8 -*-
"""
Cliente HTTP para la API de Sofascore.

Este módulo implementa un cliente HTTP robusto para comunicarse con la API
de Sofascore, con las siguientes características:

- Sesión HTTP persistente para reutilizar conexiones
- Headers que simulan un navegador real
- Rate limiting configurable para evitar bloqueos
- Reintentos automáticos con backoff exponencial
- Manejo específico de códigos de error (429, 404, 5xx)
- Logging completo de todas las operaciones

Ejemplo de uso:
    from scrapers.sofascore.cliente import SofascoreClient

    cliente = SofascoreClient()
    datos = cliente.get('/unique-tournament/8/seasons')
    if datos:
        for temporada in datos.get('seasons', []):
            print(f"Temporada: {temporada['name']}")
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Iterable, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .excepciones import (
    ErrorDeRed,
    RateLimitError,
    RecursoNoEncontrado,
    SofascoreError,
)

# Configuración del logger
logger = logging.getLogger(__name__)


class SofascoreClient:
    """
    Cliente HTTP para la API de Sofascore con rate limiting y reintentos.

    Este cliente es el punto central de comunicación con Sofascore.
    Implementa todas las medidas necesarias para hacer scraping responsable:
    rate limiting, reintentos con backoff, y headers correctos.

    Atributos:
        BASE_URL: URL base de la API de Sofascore.
        session: Sesión HTTP persistente de requests.
        timeout: Timeout en segundos para las peticiones.
        min_intervalo: Intervalo mínimo entre peticiones en segundos.
        max_reintentos: Número máximo de reintentos por petición.
        backoff_base: Base para el cálculo de backoff exponencial.

    Ejemplo:
        # Crear cliente con configuración por defecto
        cliente = SofascoreClient()

        # Obtener temporadas de La Liga
        datos = cliente.get('/unique-tournament/8/seasons')

        # Crear cliente con configuración personalizada
        cliente_lento = SofascoreClient(
            min_intervalo=2.0,
            max_reintentos=10
        )
    """

    BASE_URL = "https://api.sofascore.com/api/v1"

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    DEFAULT_SEC_CH_UA = (
        '"Not.A/Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
    )

    def __init__(
        self,
        timeout: float = 30.0,
        min_intervalo: Optional[float] = None,
        max_reintentos: Optional[int] = None,
        backoff_base: Optional[float] = None,
    ):
        """
        Inicializa el cliente de Sofascore.

        Los valores de configuración se pueden establecer mediante variables
        de entorno o parámetros del constructor. Los parámetros tienen
        prioridad sobre las variables de entorno.

        Args:
            timeout: Timeout en segundos para cada petición (default: 30.0).
            min_intervalo: Intervalo mínimo entre peticiones en segundos.
                          Variable de entorno: SOFASCORE_MIN_REQUEST_INTERVAL
                          Default: 0.5 (500ms)
            max_reintentos: Número máximo de reintentos por petición.
                           Variable de entorno: SOFASCORE_MAX_RETRIES
                           Default: 5
            backoff_base: Base para backoff exponencial en segundos.
                         Variable de entorno: SOFASCORE_BACKOFF_BASE
                         Default: 1.0

        Ejemplo:
            # Usar valores por defecto
            cliente = SofascoreClient()

            # Configuración más conservadora
            cliente = SofascoreClient(
                timeout=60.0,
                min_intervalo=1.0,
                max_reintentos=10,
                backoff_base=2.0
            )
        """
        self.timeout = timeout
        intervalo_configurado = min_intervalo or float(
            os.getenv("SOFASCORE_MIN_REQUEST_INTERVAL", "1.0")
        )
        self.min_intervalo = max(intervalo_configurado, 1.0)
        if self.min_intervalo != intervalo_configurado:
            logger.info(
                "Intervalo mínimo ajustado a %.1fs para respetar 1 req/seg.",
                self.min_intervalo,
            )
        self.max_reintentos = max_reintentos or int(
            os.getenv("SOFASCORE_MAX_RETRIES", "5")
        )
        self.backoff_base = backoff_base or float(
            os.getenv("SOFASCORE_BACKOFF_BASE", "1.0")
        )
        self.user_agent = os.getenv("SOFASCORE_USER_AGENT", self.DEFAULT_USER_AGENT)
        self.sec_ch_ua = os.getenv("SOFASCORE_SEC_CH_UA", self.DEFAULT_SEC_CH_UA)
        self._verbose_http = os.getenv("SOFASCORE_VERBOSE_HTTP", "0") == "1"
        self._cookie_strategy = os.getenv("SOFASCORE_COOKIE_STRATEGY", "auto").lower()
        self._browser_headless = os.getenv("SOFASCORE_BROWSER_HEADLESS", "1") != "0"

        # Timestamp de la última petición para rate limiting
        self._ultima_peticion: float = 0.0

        # Contador de peticiones totales para métricas
        self._contador_peticiones: int = 0
        self._contador_errores: int = 0
        self._contador_reintentos: int = 0

        # Crear sesión HTTP persistente
        self.session = self._crear_sesion()
        self._cookies_inicializadas = False
        self._configurar_proxy()
        self._inicializar_sesion()

        logger.debug(
            f"Cliente Sofascore inicializado: "
            f"timeout={self.timeout}s, "
            f"min_intervalo={self.min_intervalo}s, "
            f"max_reintentos={self.max_reintentos}, "
            f"backoff_base={self.backoff_base}s"
        )

    def _construir_headers_base(self) -> Dict[str, str]:
        """Construye headers base compartidos entre navegación y API."""
        return {
            "User-Agent": self.user_agent,
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
            "Sec-CH-UA": self.sec_ch_ua,
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
        }

    def _construir_headers_api(self) -> Dict[str, str]:
        """Headers que simulan llamadas XHR desde sofascore.com."""
        headers = self._construir_headers_base()
        headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.sofascore.com",
                "Referer": "https://www.sofascore.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )
        return headers

    def _construir_headers_navegacion(self) -> Dict[str, str]:
        """Headers de navegación real para obtener cookies iniciales."""
        headers = self._construir_headers_base()
        headers.update(
            {
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Referer": "https://www.sofascore.com/",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
        return headers

    def _actualizar_user_agent(self, user_agent: Optional[str]) -> None:
        """Sincroniza el User-Agent con la sesión si se obtiene desde navegador."""
        if not user_agent or user_agent == self.user_agent:
            return
        self.user_agent = user_agent
        self.session.headers["User-Agent"] = user_agent

    def _actualizar_cookies(self, cookies: Iterable[Dict[str, Any]]) -> None:
        """Carga cookies obtenidas externamente en la sesión requests."""
        for cookie in cookies:
            nombre = cookie.get("name")
            valor = cookie.get("value")
            if not nombre:
                continue
            self.session.cookies.set(
                nombre,
                valor,
                domain=cookie.get("domain"),
                path=cookie.get("path", "/"),
            )

    def _obtener_cookies_con_playwright(self) -> bool:
        """Obtiene cookies válidas usando Playwright."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.debug("Playwright no está instalado; se omite estrategia.")
            return False

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self._browser_headless)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                page.goto(
                    "https://www.sofascore.com/",
                    wait_until="domcontentloaded",
                    timeout=int(self.timeout * 1000),
                )
                page.wait_for_timeout(1500)
                user_agent = page.evaluate("() => navigator.userAgent")
                cookies = context.cookies()
                browser.close()

            self._actualizar_user_agent(user_agent)
            self._actualizar_cookies(cookies)
            return bool(self.session.cookies)
        except Exception as exc:
            logger.warning(
                "Falló la obtención de cookies con Playwright: %s", exc
            )
            return False

    def _obtener_cookies_con_curl_cffi(self) -> bool:
        """Obtiene cookies válidas usando curl_cffi con TLS impersonation."""
        try:
            from curl_cffi import requests as curl_requests
        except ImportError:
            logger.debug("curl_cffi no está instalado; se omite estrategia.")
            return False

        try:
            response = curl_requests.get(
                "https://www.sofascore.com/",
                headers=self._construir_headers_navegacion(),
                timeout=self.timeout,
                impersonate="chrome120",
            )
            for cookie in response.cookies:
                self.session.cookies.set(
                    cookie.name,
                    cookie.value,
                    domain=cookie.domain,
                    path=cookie.path,
                )
            return bool(self.session.cookies)
        except Exception as exc:
            logger.warning(
                "Falló la obtención de cookies con curl_cffi: %s", exc
            )
            return False

    def _crear_sesion(self) -> requests.Session:
        """
        Crea y configura una sesión HTTP persistente.

        La sesión reutiliza conexiones TCP para mejor rendimiento
        y configura los headers por defecto para todas las peticiones.

        Returns:
            Sesión requests configurada con headers y adaptadores.
        """
        session = requests.Session()
        session.headers.update(self._construir_headers_api())

        # Configurar adaptador con retry básico para conexiones
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=Retry(
                total=0,  # Los reintentos los manejamos nosotros
                connect=2,
                read=0,
                backoff_factor=0.5,
            ),
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _configurar_proxy(self) -> None:
        """Configura proxies desde variables de entorno si existen."""
        proxy_unico = os.getenv("SOFASCORE_PROXY")
        proxy_http = os.getenv("SOFASCORE_PROXY_HTTP")
        proxy_https = os.getenv("SOFASCORE_PROXY_HTTPS")

        proxies = {}
        if proxy_unico:
            proxies = {"http": proxy_unico, "https": proxy_unico}
        else:
            if proxy_http:
                proxies["http"] = proxy_http
            if proxy_https:
                proxies["https"] = proxy_https

        if proxies:
            self.session.proxies.update(proxies)
            logger.info("Proxy configurado para Sofascore: %s", list(proxies.keys()))

    def _inicializar_sesion(self) -> None:
        """
        Inicializa la sesión obteniendo cookies desde la web pública.

        Sofascore aplica protección anti-bot que puede bloquear peticiones
        directas al API. Esta llamada busca establecer cookies válidas y
        reducir respuestas 403.
        """
        if self._cookies_inicializadas:
            return

        try:
            cookies_obtenidas = False
            estrategia = self._cookie_strategy
            estrategia_usada = "none"
            response = None
            if estrategia in ("auto", "playwright"):
                cookies_obtenidas = self._obtener_cookies_con_playwright()
                estrategia_usada = "playwright"
            if not cookies_obtenidas and estrategia in ("auto", "curl_cffi"):
                cookies_obtenidas = self._obtener_cookies_con_curl_cffi()
                estrategia_usada = "curl_cffi"
            if not cookies_obtenidas and estrategia in ("auto", "requests"):
                response = self.session.get(
                    "https://www.sofascore.com/",
                    headers=self._construir_headers_navegacion(),
                    timeout=self.timeout,
                )
                cookies_obtenidas = bool(self.session.cookies)
                estrategia_usada = "requests"
            self._cookies_inicializadas = cookies_obtenidas
            status_code = response.status_code if response is not None else "n/a"
            logger.debug(
                "Inicialización de sesión Sofascore: status=%s, cookies=%s, estrategia=%s",
                status_code,
                bool(self.session.cookies),
                estrategia_usada,
            )
            if self._cookies_inicializadas:
                logger.debug(
                    "Cookies iniciales recibidas: %s",
                    list(self.session.cookies.get_dict().keys()),
                )
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"No se pudo inicializar sesión Sofascore: {e}. "
                "Se continuará sin cookies iniciales."
            )

    def _refrescar_sesion(self) -> None:
        """Fuerza la reinicialización de cookies y sesión."""
        self.session.cookies.clear()
        self._cookies_inicializadas = False
        self._inicializar_sesion()

    def _log_request_context(self, endpoint: str) -> None:
        """Loguea headers y cookies cuando el modo verbose está activo."""
        if not (self._verbose_http or logger.isEnabledFor(logging.DEBUG)):
            return

        headers = dict(self.session.headers)
        cookies = self.session.cookies.get_dict()
        headers_sin_cookie = {k: v for k, v in headers.items() if k.lower() != "cookie"}
        logger.debug(
            "Solicitud Sofascore %s | headers=%s | cookies=%s",
            endpoint,
            headers_sin_cookie,
            list(cookies.keys()),
        )

    def _aplicar_rate_limiting(self) -> None:
        """
        Aplica rate limiting esperando el tiempo necesario entre peticiones.

        Verifica el tiempo transcurrido desde la última petición y,
        si es menor al intervalo mínimo configurado, hace sleep del
        tiempo restante.
        """
        if self._ultima_peticion == 0:
            return

        tiempo_transcurrido = time.time() - self._ultima_peticion
        tiempo_restante = self.min_intervalo - tiempo_transcurrido

        if tiempo_restante > 0:
            logger.debug(
                f"Rate limiting: esperando {tiempo_restante:.3f}s "
                f"(intervalo mínimo: {self.min_intervalo}s)"
            )
            time.sleep(tiempo_restante)

    def _calcular_tiempo_espera(
        self,
        intento: int,
        es_rate_limit: bool = False
    ) -> float:
        """
        Calcula el tiempo de espera con backoff exponencial.

        Args:
            intento: Número de intento actual (0-based).
            es_rate_limit: Si el error fue un 429, aplicar backoff más agresivo.

        Returns:
            Tiempo de espera en segundos.
        """
        tiempo_base = self.backoff_base * (2 ** intento)

        # Para rate limit, duplicar el tiempo de espera
        if es_rate_limit:
            tiempo_base *= 2

        # Añadir un poco de jitter para evitar thundering herd
        import random
        jitter = random.uniform(0, 0.5)

        return tiempo_base + jitter

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza una petición GET a la API de Sofascore.

        Este método:
        1. Construye la URL completa
        2. Aplica rate limiting
        3. Realiza la petición con headers correctos
        4. Maneja errores y reintentos con backoff exponencial
        5. Retorna el JSON parseado o None/excepción según el caso

        Args:
            endpoint: Ruta del endpoint (ej: '/unique-tournament/8/seasons').
                     Puede incluir o no la barra inicial.
            params: Parámetros de query string opcionales.

        Returns:
            Diccionario con la respuesta JSON de Sofascore, o None si
            el recurso no fue encontrado (404).

        Raises:
            RateLimitError: Si se excedieron los reintentos por rate limiting.
            ErrorDeRed: Si hubo errores de red después de todos los reintentos.
            SofascoreError: Para otros errores de la API.

        Ejemplo:
            # Obtener temporadas
            temporadas = cliente.get('/unique-tournament/8/seasons')

            # Con parámetros
            partidos = cliente.get(
                '/unique-tournament/8/season/12345/events/last/0',
                params={'limit': 20}
            )
        """
        # Normalizar endpoint
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        url = f"{self.BASE_URL}{endpoint}"

        for intento in range(self.max_reintentos + 1):
            try:
                if not self._cookies_inicializadas:
                    self._inicializar_sesion()
                # Aplicar rate limiting antes de la petición
                self._aplicar_rate_limiting()

                # Registrar timestamp de la petición
                tiempo_inicio = time.time()
                self._ultima_peticion = tiempo_inicio

                # Realizar la petición
                logger.debug(
                    f"GET {endpoint} "
                    f"(intento {intento + 1}/{self.max_reintentos + 1})"
                )
                self._log_request_context(endpoint)

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                tiempo_respuesta = time.time() - tiempo_inicio
                self._contador_peticiones += 1

                # Log de la respuesta
                logger.debug(
                    f"Respuesta {response.status_code} en {tiempo_respuesta:.2f}s: "
                    f"{endpoint}"
                )

                # Manejar diferentes códigos de respuesta
                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 404:
                    # No encontrado - no reintentar
                    logger.warning(
                        f"Recurso no encontrado (404): {endpoint}"
                    )
                    return None

                elif response.status_code == 429:
                    # Rate limiting - backoff agresivo
                    self._contador_errores += 1
                    tiempo_espera = self._calcular_tiempo_espera(intento, es_rate_limit=True)

                    logger.warning(
                        f"Rate limit activado (429) en {endpoint}. "
                        f"Esperando {tiempo_espera:.1f}s antes de reintentar "
                        f"(intento {intento + 1}/{self.max_reintentos + 1})"
                    )

                    if intento < self.max_reintentos:
                        time.sleep(tiempo_espera)
                        self._contador_reintentos += 1
                        continue
                    else:
                        raise RateLimitError(
                            mensaje=f"Rate limit excedido después de {self.max_reintentos} reintentos",
                            tiempo_espera=tiempo_espera,
                            reintentos_realizados=intento + 1,
                            detalles={'endpoint': endpoint}
                        )

                elif response.status_code >= 500:
                    # Error del servidor - reintentar con backoff normal
                    self._contador_errores += 1
                    tiempo_espera = self._calcular_tiempo_espera(intento)

                    logger.warning(
                        f"Error del servidor ({response.status_code}) en {endpoint}. "
                        f"Esperando {tiempo_espera:.1f}s antes de reintentar"
                    )

                    if intento < self.max_reintentos:
                        time.sleep(tiempo_espera)
                        self._contador_reintentos += 1
                        continue
                    else:
                        raise SofascoreError(
                            mensaje=f"Error del servidor después de {self.max_reintentos} reintentos",
                            codigo=response.status_code,
                            detalles={'endpoint': endpoint, 'reintentos': intento + 1}
                        )

                else:
                    if response.status_code == 403:
                        self._contador_errores += 1
                        tiempo_espera = self._calcular_tiempo_espera(intento)
                        logger.warning(
                            "Acceso denegado (403) en %s. "
                            "Posible bloqueo anti-bot; refrescando cookies "
                            "y reintentando en %.1fs.",
                            endpoint,
                            tiempo_espera,
                        )

                        if intento < self.max_reintentos:
                            self._refrescar_sesion()
                            time.sleep(tiempo_espera)
                            self._contador_reintentos += 1
                            continue
                        else:
                            raise SofascoreError(
                                mensaje=(
                                    "Sofascore respondió 403 Forbidden. "
                                    "Puede requerir cookies o headers adicionales. "
                                    "Prueba ajustar el rate limiting o usar un proxy/residencial."
                                ),
                                codigo=403,
                                detalles={
                                    'endpoint': endpoint,
                                    'body': response.text[:500],
                                }
                            )

                    # Otros errores HTTP
                    self._contador_errores += 1
                    raise SofascoreError(
                        mensaje=f"Error HTTP inesperado: {response.status_code}",
                        codigo=response.status_code,
                        detalles={'endpoint': endpoint, 'body': response.text[:500]}
                    )

            except requests.exceptions.Timeout as e:
                # Timeout - reintentar
                self._contador_errores += 1
                tiempo_espera = self._calcular_tiempo_espera(intento)

                logger.warning(
                    f"Timeout ({self.timeout}s) en {endpoint}. "
                    f"Reintentando en {tiempo_espera:.1f}s"
                )

                if intento < self.max_reintentos:
                    time.sleep(tiempo_espera)
                    self._contador_reintentos += 1
                    continue
                else:
                    raise ErrorDeRed(
                        mensaje=f"Timeout después de {self.max_reintentos} reintentos",
                        excepcion_original=e,
                        reintentos_realizados=intento + 1,
                        timeout_usado=self.timeout,
                        endpoint=endpoint
                    )

            except requests.exceptions.ConnectionError as e:
                # Error de conexión - reintentar
                self._contador_errores += 1
                tiempo_espera = self._calcular_tiempo_espera(intento)

                logger.warning(
                    f"Error de conexión en {endpoint}: {e}. "
                    f"Reintentando en {tiempo_espera:.1f}s"
                )

                if intento < self.max_reintentos:
                    time.sleep(tiempo_espera)
                    self._contador_reintentos += 1
                    continue
                else:
                    raise ErrorDeRed(
                        mensaje=f"Error de conexión después de {self.max_reintentos} reintentos",
                        excepcion_original=e,
                        reintentos_realizados=intento + 1,
                        endpoint=endpoint
                    )

            except requests.exceptions.RequestException as e:
                # Otros errores de requests - reintentar
                self._contador_errores += 1
                tiempo_espera = self._calcular_tiempo_espera(intento)

                logger.warning(
                    f"Error de red en {endpoint}: {e}. "
                    f"Reintentando en {tiempo_espera:.1f}s"
                )

                if intento < self.max_reintentos:
                    time.sleep(tiempo_espera)
                    self._contador_reintentos += 1
                    continue
                else:
                    raise ErrorDeRed(
                        mensaje=f"Error de red después de {self.max_reintentos} reintentos",
                        excepcion_original=e,
                        reintentos_realizados=intento + 1,
                        endpoint=endpoint
                    )

        # No debería llegar aquí, pero por seguridad
        raise SofascoreError(
            mensaje="Error inesperado en el cliente",
            detalles={'endpoint': endpoint}
        )

    def obtener_metricas(self) -> Dict[str, int]:
        """
        Retorna métricas del cliente para monitoreo.

        Returns:
            Diccionario con contadores de peticiones, errores y reintentos.

        Ejemplo:
            metricas = cliente.obtener_metricas()
            print(f"Peticiones totales: {metricas['peticiones_totales']}")
        """
        return {
            'peticiones_totales': self._contador_peticiones,
            'errores_totales': self._contador_errores,
            'reintentos_totales': self._contador_reintentos,
            'tasa_exito': (
                (self._contador_peticiones - self._contador_errores)
                / max(self._contador_peticiones, 1)
                * 100
            ),
        }

    def reiniciar_metricas(self) -> None:
        """Reinicia los contadores de métricas a cero."""
        self._contador_peticiones = 0
        self._contador_errores = 0
        self._contador_reintentos = 0
        logger.debug("Métricas del cliente reiniciadas")

    def cerrar(self) -> None:
        """
        Cierra la sesión HTTP y libera recursos.

        Llamar a este método cuando se termina de usar el cliente
        para liberar las conexiones TCP mantenidas.
        """
        if self.session:
            self.session.close()
            logger.debug("Sesión HTTP cerrada")

    def __enter__(self) -> 'SofascoreClient':
        """Permite usar el cliente como context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cierra la sesión al salir del context manager."""
        self.cerrar()

    def __repr__(self) -> str:
        """Representación del cliente para debugging."""
        return (
            f"SofascoreClient("
            f"timeout={self.timeout}, "
            f"min_intervalo={self.min_intervalo}, "
            f"max_reintentos={self.max_reintentos}, "
            f"peticiones={self._contador_peticiones})"
        )
