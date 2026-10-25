"""Cliente HTTP serial, acotado, identificable y sin evasión de bloqueos."""
from __future__ import annotations

import json
import math
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode

import requests

from .archivo import Archivo, ArchivoError, append_json
from .contrato import LIMITE, identificador

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
MAX_BYTES = 8 * 1024 * 1024


class FuenteError(RuntimeError):
    """Error operativo: debe generar reporte incompleto y exit code no cero."""


def url_consulta(endpoint: str, parametro: str) -> str:
    if endpoint == "scoreboard":
        if len(parametro) != 8 or not parametro.isascii() or not parametro.isdigit():
            raise ValueError("dates debe ser YYYYMMDD")
        datetime.strptime(parametro, "%Y%m%d")
        params = {"dates": parametro, "limit": LIMITE}
    elif endpoint == "summary":
        params = {"event": identificador(parametro, "event")}
    else:
        raise ValueError("Endpoint WNBA no permitido")
    return f"{BASE}/{endpoint}?{urlencode(params)}"


class ClienteESPN:
    def __init__(self, archivo: Archivo, *, offline=False, refresh=False, intervalo=1.5,
                 max_requests=1000, intentos=3, session=None, dormir=time.sleep,
                 reloj=time.monotonic, ahora=None, jitter=None):
        if not math.isfinite(intervalo) or intervalo < 1.25:
            raise ValueError("Intervalo mínimo: 1.25 segundos")
        if not 1 <= intentos <= 3 or not 1 <= max_requests <= 20000:
            raise ValueError("Presupuesto/intentos fuera de límites")
        if offline and refresh:
            raise ValueError("Offline y refresh son incompatibles")
        self.archivo, self.offline, self.refresh = archivo, offline, refresh
        self.intervalo, self.max_requests, self.intentos = intervalo, max_requests, intentos
        self.dormir, self.reloj = dormir, reloj
        self.ahora = ahora or (lambda: datetime.now(timezone.utc))
        self.jitter = jitter or (lambda: random.uniform(0, 0.25))
        self.ultimo_inicio = None
        self.rate_limited = False
        self.contadores = {"requests": 0, "cache_hits": 0, "bytes_red": 0, "reintentos": 0}
        self.session = session or requests.Session()
        self.session.trust_env = False  # Sin proxies/credenciales implícitos del entorno.
        self.session.headers.update({"User-Agent": "AnalyticsPredict-WNBA/1.0", "Accept": "application/json"})

    def close(self):
        self.session.close()

    def _retry_after(self, raw: str | None) -> float:
        if raw is None:
            raise FuenteError("HTTP 429 sin Retry-After: fuente detenida")
        try:
            if raw.isdigit():
                seconds = float(raw)
            else:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    raise ValueError("timezone")
                seconds = (dt - self.ahora()).total_seconds()
        except (ValueError, TypeError, OverflowError) as exc:
            raise FuenteError("Retry-After inválido: fuente detenida") from exc
        if not math.isfinite(seconds) or not 0 <= seconds <= 60:
            raise FuenteError("Retry-After fuera del presupuesto de espera; reanudar más tarde")
        return seconds

    def obtener(self, endpoint: str, parametro: str, *, max_age=86400) -> tuple[dict, dict]:
        url = url_consulta(endpoint, parametro)
        cached = self.archivo.cargar(url)  # Verifica integridad incluso antes de refresh.
        if cached:
            try:
                observed = datetime.fromisoformat(cached[1]["observado_utc"])
                if observed.tzinfo is None:
                    raise ValueError("timezone")
                age = (self.ahora() - observed).total_seconds()
                if age < 0:
                    raise ValueError("futuro")
            except (ValueError, KeyError, TypeError) as exc:
                raise ArchivoError("Fecha de observación de caché inválida") from exc
            if self.offline or (not self.refresh and age <= max_age):
                self.contadores["cache_hits"] += 1
                return cached
        if self.offline:
            raise FuenteError("OFFLINE: falta una respuesta archivada para la ventana solicitada")
        for attempt in range(self.intentos):
            if self.contadores["requests"] >= self.max_requests:
                raise FuenteError("Presupuesto HTTP agotado; reanudación disponible")
            if self.ultimo_inicio is not None:
                self.dormir(max(0, self.intervalo - (self.reloj() - self.ultimo_inicio)))
            self.ultimo_inicio = self.reloj()
            self.contadores["requests"] += 1
            if attempt:
                self.contadores["reintentos"] += 1
            observado = self.ahora().isoformat()
            response = None
            delay = None
            try:
                response = self.session.get(url, timeout=(5, 20), allow_redirects=False, stream=True)
                code = response.status_code
                append_json(self.archivo.root / "http.jsonl", {"url": url, "observado_utc": observado,
                            "intento": attempt + 1, "http_status": code})
                if code in (401, 403) or 300 <= code < 400:
                    raise FuenteError(f"HTTP {code}: acceso/redirect detenido, sin evasión")
                if code == 429:
                    if self.rate_limited:
                        raise FuenteError("HTTP 429 repetido: fuente detenida")
                    self.rate_limited = True
                    delay = self._retry_after(response.headers.get("Retry-After"))
                elif code in (500, 502, 503, 504):
                    delay = 2 ** attempt + self.jitter()
                elif code != 200:
                    raise FuenteError(f"HTTP {code}: respuesta no utilizable")
                else:
                    ctype = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
                    if ctype != "application/json" and not ctype.endswith("+json"):
                        raise FuenteError("HTTP 200 sin Content-Type JSON")
                    chunks, size = [], 0
                    for chunk in response.iter_content(chunk_size=65536):
                        size += len(chunk)
                        self.contadores["bytes_red"] += len(chunk)
                        if size > MAX_BYTES or self.reloj() - self.ultimo_inicio > 60:
                            raise FuenteError("Respuesta excede el límite de bytes/tiempo")
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                    try:
                        value = json.loads(raw)
                    except (ValueError, UnicodeError) as exc:
                        raise FuenteError("JSON inválido; no reintentar como si fuera vacío") from exc
                    if not isinstance(value, dict):
                        raise FuenteError("Raíz JSON distinta de objeto")
                    meta = self.archivo.guardar(url, raw, self.ahora().isoformat())
                    return value, meta
            except (requests.Timeout, requests.ConnectionError) as exc:
                append_json(self.archivo.root / "http.jsonl", {"url": url, "observado_utc": observado,
                            "intento": attempt + 1, "error": type(exc).__name__})
                delay = 2 ** attempt + self.jitter()
            except requests.RequestException as exc:
                raise FuenteError(f"Error HTTP {type(exc).__name__}") from exc
            finally:
                if response is not None:
                    response.close()
            if attempt + 1 < self.intentos and delay is not None:
                self.dormir(delay)
        raise FuenteError("Intentos HTTP agotados; no se considera ventana vacía")
