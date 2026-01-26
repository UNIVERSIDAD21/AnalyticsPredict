# -*- coding: utf-8 -*-
"""
Excepciones personalizadas para el módulo de Sofascore.

Este módulo define todas las excepciones que pueden ocurrir durante
la extracción de datos desde Sofascore, permitiendo un manejo de
errores más preciso y específico.
"""

from typing import Optional, Dict, Any


class SofascoreError(Exception):
    """
    Excepción base para todos los errores relacionados con Sofascore.

    Todas las excepciones específicas del módulo heredan de esta clase,
    permitiendo capturar cualquier error de Sofascore con un solo except.

    Atributos:
        mensaje: Descripción del error.
        codigo: Código de error HTTP si aplica.
        detalles: Información adicional sobre el error.

    Ejemplo:
        try:
            cliente.get('/endpoint')
        except SofascoreError as e:
            logger.error(f"Error de Sofascore: {e.mensaje}")
    """

    def __init__(
        self,
        mensaje: str,
        codigo: Optional[int] = None,
        detalles: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción.

        Args:
            mensaje: Descripción del error.
            codigo: Código de error HTTP (opcional).
            detalles: Diccionario con información adicional (opcional).
        """
        self.mensaje = mensaje
        self.codigo = codigo
        self.detalles = detalles or {}
        super().__init__(self.mensaje)

    def __str__(self) -> str:
        """Representación en string del error."""
        partes = [self.mensaje]
        if self.codigo:
            partes.append(f"(código: {self.codigo})")
        return " ".join(partes)

    def __repr__(self) -> str:
        """Representación detallada del error."""
        return (
            f"{self.__class__.__name__}("
            f"mensaje={self.mensaje!r}, "
            f"codigo={self.codigo}, "
            f"detalles={self.detalles})"
        )


class RateLimitError(SofascoreError):
    """
    Error cuando Sofascore aplica rate limiting (HTTP 429).

    Esta excepción se lanza cuando se excede el límite de peticiones
    permitidas por Sofascore. El cliente debe esperar antes de
    reintentar la petición.

    Atributos:
        tiempo_espera: Segundos recomendados de espera antes de reintentar.
        reintentos_realizados: Número de reintentos ya realizados.

    Ejemplo:
        try:
            cliente.get('/endpoint')
        except RateLimitError as e:
            time.sleep(e.tiempo_espera)
    """

    def __init__(
        self,
        mensaje: str = "Rate limit excedido en Sofascore",
        tiempo_espera: float = 60.0,
        reintentos_realizados: int = 0,
        detalles: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción de rate limiting.

        Args:
            mensaje: Descripción del error.
            tiempo_espera: Segundos recomendados de espera.
            reintentos_realizados: Número de reintentos realizados.
            detalles: Información adicional.
        """
        self.tiempo_espera = tiempo_espera
        self.reintentos_realizados = reintentos_realizados
        super().__init__(mensaje, codigo=429, detalles=detalles)

    def __str__(self) -> str:
        """Representación en string del error."""
        return (
            f"{self.mensaje} - "
            f"Esperar {self.tiempo_espera:.1f}s "
            f"(reintentos: {self.reintentos_realizados})"
        )


class RecursoNoEncontrado(SofascoreError):
    """
    Error cuando un recurso no existe en Sofascore (HTTP 404).

    Esta excepción se lanza cuando se intenta acceder a un recurso
    que no existe (partido, equipo, liga, etc.). No se debe reintentar
    esta petición ya que el recurso definitivamente no existe.

    Atributos:
        tipo_recurso: Tipo de recurso no encontrado (partido, equipo, etc.).
        id_recurso: Identificador del recurso buscado.

    Ejemplo:
        try:
            estadisticas = obtener_estadisticas_partido(cliente, evento_id=99999)
        except RecursoNoEncontrado as e:
            logger.warning(f"Partido {e.id_recurso} no tiene estadísticas")
    """

    def __init__(
        self,
        mensaje: str = "Recurso no encontrado en Sofascore",
        tipo_recurso: Optional[str] = None,
        id_recurso: Optional[int] = None,
        endpoint: Optional[str] = None,
        detalles: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción de recurso no encontrado.

        Args:
            mensaje: Descripción del error.
            tipo_recurso: Tipo de recurso (partido, equipo, liga, temporada).
            id_recurso: ID del recurso buscado.
            endpoint: URL del endpoint consultado.
            detalles: Información adicional.
        """
        self.tipo_recurso = tipo_recurso
        self.id_recurso = id_recurso
        self.endpoint = endpoint

        detalles_completos = detalles or {}
        if tipo_recurso:
            detalles_completos['tipo_recurso'] = tipo_recurso
        if id_recurso is not None:
            detalles_completos['id_recurso'] = id_recurso
        if endpoint:
            detalles_completos['endpoint'] = endpoint

        super().__init__(mensaje, codigo=404, detalles=detalles_completos)

    def __str__(self) -> str:
        """Representación en string del error."""
        partes = [self.mensaje]
        if self.tipo_recurso:
            partes.append(f"[{self.tipo_recurso}]")
        if self.id_recurso is not None:
            partes.append(f"ID: {self.id_recurso}")
        return " - ".join(partes)


class ErrorDeRed(SofascoreError):
    """
    Error de conexión o red al comunicarse con Sofascore.

    Esta excepción se lanza cuando hay problemas de conectividad,
    timeouts, o errores de DNS. Estas peticiones pueden reintentarse
    ya que el error es potencialmente temporal.

    Atributos:
        excepcion_original: La excepción de red original.
        reintentos_realizados: Número de reintentos ya realizados.
        timeout_usado: Timeout configurado para la petición.

    Ejemplo:
        try:
            cliente.get('/endpoint')
        except ErrorDeRed as e:
            if e.reintentos_realizados < 3:
                # Reintentar con backoff
                time.sleep(2 ** e.reintentos_realizados)
    """

    def __init__(
        self,
        mensaje: str = "Error de red al conectar con Sofascore",
        excepcion_original: Optional[Exception] = None,
        reintentos_realizados: int = 0,
        timeout_usado: Optional[float] = None,
        endpoint: Optional[str] = None,
        detalles: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción de error de red.

        Args:
            mensaje: Descripción del error.
            excepcion_original: Excepción de requests/urllib que causó el error.
            reintentos_realizados: Número de reintentos realizados.
            timeout_usado: Timeout en segundos de la petición.
            endpoint: URL del endpoint consultado.
            detalles: Información adicional.
        """
        self.excepcion_original = excepcion_original
        self.reintentos_realizados = reintentos_realizados
        self.timeout_usado = timeout_usado
        self.endpoint = endpoint

        detalles_completos = detalles or {}
        if excepcion_original:
            detalles_completos['error_original'] = str(excepcion_original)
            detalles_completos['tipo_error'] = type(excepcion_original).__name__
        if timeout_usado:
            detalles_completos['timeout'] = timeout_usado
        if endpoint:
            detalles_completos['endpoint'] = endpoint

        super().__init__(mensaje, detalles=detalles_completos)

    def __str__(self) -> str:
        """Representación en string del error."""
        partes = [self.mensaje]
        if self.excepcion_original:
            partes.append(f"({type(self.excepcion_original).__name__})")
        if self.reintentos_realizados > 0:
            partes.append(f"[reintentos: {self.reintentos_realizados}]")
        return " ".join(partes)


class DatosIncompletos(SofascoreError):
    """
    Error cuando los datos recibidos de Sofascore están incompletos.

    Esta excepción se lanza cuando la respuesta de Sofascore no contiene
    todos los campos esperados o los datos no tienen el formato correcto.
    Puede indicar cambios en la API de Sofascore.

    Atributos:
        campos_faltantes: Lista de campos que faltan en la respuesta.
        campos_invalidos: Lista de campos con valores inválidos.
        tipo_datos: Tipo de datos esperados (partido, estadisticas, etc.).

    Ejemplo:
        try:
            partido = parsear_partido(evento_json)
        except DatosIncompletos as e:
            logger.warning(f"Partido incompleto, faltan: {e.campos_faltantes}")
    """

    def __init__(
        self,
        mensaje: str = "Datos incompletos recibidos de Sofascore",
        campos_faltantes: Optional[list] = None,
        campos_invalidos: Optional[list] = None,
        tipo_datos: Optional[str] = None,
        datos_recibidos: Optional[Dict[str, Any]] = None,
        detalles: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción de datos incompletos.

        Args:
            mensaje: Descripción del error.
            campos_faltantes: Lista de nombres de campos faltantes.
            campos_invalidos: Lista de nombres de campos con valores inválidos.
            tipo_datos: Tipo de estructura de datos esperada.
            datos_recibidos: Datos parciales recibidos (para debug).
            detalles: Información adicional.
        """
        self.campos_faltantes = campos_faltantes or []
        self.campos_invalidos = campos_invalidos or []
        self.tipo_datos = tipo_datos
        self.datos_recibidos = datos_recibidos

        detalles_completos = detalles or {}
        if campos_faltantes:
            detalles_completos['campos_faltantes'] = campos_faltantes
        if campos_invalidos:
            detalles_completos['campos_invalidos'] = campos_invalidos
        if tipo_datos:
            detalles_completos['tipo_datos'] = tipo_datos

        super().__init__(mensaje, detalles=detalles_completos)

    def __str__(self) -> str:
        """Representación en string del error."""
        partes = [self.mensaje]
        if self.tipo_datos:
            partes.append(f"[{self.tipo_datos}]")
        if self.campos_faltantes:
            partes.append(f"Faltan: {', '.join(self.campos_faltantes)}")
        if self.campos_invalidos:
            partes.append(f"Inválidos: {', '.join(self.campos_invalidos)}")
        return " - ".join(partes)


class ErrorConfiguracion(SofascoreError):
    """
    Error de configuración del cliente o módulo.

    Esta excepción se lanza cuando hay problemas con la configuración
    del sistema, como variables de entorno faltantes o valores inválidos.

    Atributos:
        parametro: Nombre del parámetro mal configurado.
        valor_actual: Valor actual del parámetro.
        valor_esperado: Descripción del valor esperado.
    """

    def __init__(
        self,
        mensaje: str = "Error de configuración del módulo Sofascore",
        parametro: Optional[str] = None,
        valor_actual: Optional[Any] = None,
        valor_esperado: Optional[str] = None,
        detalles: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción de configuración.

        Args:
            mensaje: Descripción del error.
            parametro: Nombre del parámetro problemático.
            valor_actual: Valor actual del parámetro.
            valor_esperado: Descripción del valor correcto esperado.
            detalles: Información adicional.
        """
        self.parametro = parametro
        self.valor_actual = valor_actual
        self.valor_esperado = valor_esperado

        detalles_completos = detalles or {}
        if parametro:
            detalles_completos['parametro'] = parametro
        if valor_actual is not None:
            detalles_completos['valor_actual'] = valor_actual
        if valor_esperado:
            detalles_completos['valor_esperado'] = valor_esperado

        super().__init__(mensaje, detalles=detalles_completos)

    def __str__(self) -> str:
        """Representación en string del error."""
        partes = [self.mensaje]
        if self.parametro:
            partes.append(f"Parámetro: {self.parametro}")
        if self.valor_esperado:
            partes.append(f"Esperado: {self.valor_esperado}")
        return " - ".join(partes)


class ErrorBaseDatos(SofascoreError):
    """
    Error al interactuar con la base de datos.

    Esta excepción se lanza cuando hay problemas al leer o escribir
    datos en PostgreSQL, como violaciones de constraints, conexiones
    fallidas, o errores de SQL.

    Atributos:
        operacion: Tipo de operación que falló (INSERT, UPDATE, SELECT).
        tabla: Nombre de la tabla involucrada.
        excepcion_original: Excepción de psycopg2 original.
    """

    def __init__(
        self,
        mensaje: str = "Error de base de datos en módulo Sofascore",
        operacion: Optional[str] = None,
        tabla: Optional[str] = None,
        excepcion_original: Optional[Exception] = None,
        detalles: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción de base de datos.

        Args:
            mensaje: Descripción del error.
            operacion: Tipo de operación SQL.
            tabla: Nombre de la tabla.
            excepcion_original: Excepción de psycopg2.
            detalles: Información adicional.
        """
        self.operacion = operacion
        self.tabla = tabla
        self.excepcion_original = excepcion_original

        detalles_completos = detalles or {}
        if operacion:
            detalles_completos['operacion'] = operacion
        if tabla:
            detalles_completos['tabla'] = tabla
        if excepcion_original:
            detalles_completos['error_original'] = str(excepcion_original)
            detalles_completos['tipo_error'] = type(excepcion_original).__name__

        super().__init__(mensaje, detalles=detalles_completos)

    def __str__(self) -> str:
        """Representación en string del error."""
        partes = [self.mensaje]
        if self.operacion and self.tabla:
            partes.append(f"[{self.operacion} en {self.tabla}]")
        elif self.tabla:
            partes.append(f"[{self.tabla}]")
        return " ".join(partes)
