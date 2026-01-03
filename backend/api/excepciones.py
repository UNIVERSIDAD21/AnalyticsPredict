# -*- coding: utf-8 -*-
"""
excepciones.py — Excepciones personalizadas del sistema.
"""


class ErrorBase(Exception):
    """Excepción base del sistema."""

    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ErrorEquipoNoEncontrado(ErrorBase):
    """Se lanza cuando un equipo no existe en el modelo."""

    def __init__(self, equipo: str, equipos_similares: list = None):
        self.equipo = equipo
        self.equipos_similares = equipos_similares or []

        mensaje = f'El equipo "{equipo}" no se encontró en el modelo.'
        if self.equipos_similares:
            sugerencias = ", ".join(self.equipos_similares[:3])
            mensaje += f" ¿Quisiste decir: {sugerencias}?"

        super().__init__(mensaje)


class ErrorValidacion(ErrorBase):
    """Se lanza cuando los datos de entrada son inválidos."""

    def __init__(self, mensaje: str, campo: str = None):
        self.campo = campo
        super().__init__(mensaje)


class ErrorAnalisis(ErrorBase):
    """Se lanza cuando ocurre un error durante el análisis."""


class ErrorModelo(ErrorBase):
    """Se lanza cuando hay problemas con el modelo de predicción."""


class ErrorDatos(ErrorBase):
    """Se lanza cuando hay problemas con los datos."""
