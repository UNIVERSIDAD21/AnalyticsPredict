# -*- coding: utf-8 -*-
"""
excepciones.py — Excepciones específicas del motor de fútbol.

Este módulo define todas las excepciones personalizadas utilizadas
en el motor de predicción de fútbol.
"""


class MotorFutbolError(Exception):
    """Excepción base para errores del motor de fútbol."""

    def __init__(self, mensaje: str, codigo: str = "MOTOR_ERROR"):
        self.mensaje = mensaje
        self.codigo = codigo
        super().__init__(mensaje)

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.mensaje}"


class PartidoNoEncontrado(MotorFutbolError):
    """Excepción cuando no se encuentra un partido en la base de datos."""

    def __init__(self, partido_id: str):
        super().__init__(
            mensaje=f"Partido con ID '{partido_id}' no encontrado.",
            codigo="PARTIDO_NO_ENCONTRADO"
        )
        self.partido_id = partido_id


class EquipoNoEncontrado(MotorFutbolError):
    """Excepción cuando un equipo no está en el modelo."""

    def __init__(self, nombre_equipo: str, equipos_disponibles: int = 0):
        mensaje = f"Equipo '{nombre_equipo}' no está en el modelo."
        if equipos_disponibles > 0:
            mensaje += f" El modelo contiene {equipos_disponibles} equipos."
        super().__init__(
            mensaje=mensaje,
            codigo="EQUIPO_NO_ENCONTRADO"
        )
        self.nombre_equipo = nombre_equipo
        self.equipos_disponibles = equipos_disponibles


class DatosInsuficientes(MotorFutbolError):
    """Excepción cuando no hay suficientes datos históricos."""

    def __init__(
        self,
        mensaje: str,
        partidos_disponibles: int = 0,
        partidos_requeridos: int = 0
    ):
        mensaje_completo = mensaje
        if partidos_disponibles > 0 or partidos_requeridos > 0:
            mensaje_completo += (
                f" Disponibles: {partidos_disponibles}, "
                f"Requeridos: {partidos_requeridos}."
            )
        super().__init__(
            mensaje=mensaje_completo,
            codigo="DATOS_INSUFICIENTES"
        )
        self.partidos_disponibles = partidos_disponibles
        self.partidos_requeridos = partidos_requeridos


class ModeloNoEntrenado(MotorFutbolError):
    """Excepción cuando el modelo no ha sido entrenado."""

    def __init__(self, tipo_modelo: str = ""):
        mensaje = "El modelo no ha sido entrenado."
        if tipo_modelo:
            mensaje = f"El modelo de {tipo_modelo} no ha sido entrenado."
        super().__init__(
            mensaje=mensaje,
            codigo="MODELO_NO_ENTRENADO"
        )
        self.tipo_modelo = tipo_modelo


class ErrorEntrenamiento(MotorFutbolError):
    """Excepción cuando falla el entrenamiento del modelo."""

    def __init__(self, mensaje: str, causa: Exception = None):
        super().__init__(
            mensaje=mensaje,
            codigo="ERROR_ENTRENAMIENTO"
        )
        self.causa = causa


class ErrorPrediccion(MotorFutbolError):
    """Excepción cuando falla la generación de predicción."""

    def __init__(self, mensaje: str, partido_id: str = None):
        super().__init__(
            mensaje=mensaje,
            codigo="ERROR_PREDICCION"
        )
        self.partido_id = partido_id


class ErrorValidacion(MotorFutbolError):
    """Excepción cuando falla la validación de datos."""

    def __init__(self, mensaje: str, campo: str = None):
        super().__init__(
            mensaje=mensaje,
            codigo="ERROR_VALIDACION"
        )
        self.campo = campo


class ErrorBaseDatos(MotorFutbolError):
    """Excepción para errores de base de datos."""

    def __init__(self, mensaje: str, query: str = None):
        super().__init__(
            mensaje=mensaje,
            codigo="ERROR_BD"
        )
        self.query = query


class FechaCorteInvalida(MotorFutbolError):
    """Excepción cuando la fecha de corte no es válida."""

    def __init__(self, fecha_corte: str, razon: str = ""):
        mensaje = f"Fecha de corte inválida: {fecha_corte}"
        if razon:
            mensaje += f". {razon}"
        super().__init__(
            mensaje=mensaje,
            codigo="FECHA_CORTE_INVALIDA"
        )
        self.fecha_corte = fecha_corte


class CacheError(MotorFutbolError):
    """Excepción para errores de cache."""

    def __init__(self, mensaje: str):
        super().__init__(
            mensaje=mensaje,
            codigo="ERROR_CACHE"
        )
