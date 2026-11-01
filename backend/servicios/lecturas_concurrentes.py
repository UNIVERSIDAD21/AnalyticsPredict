"""Comparte solo lecturas idénticas EN CURSO; no guarda respuestas ni usa TTL.

Las ventanas reciben copias independientes. No se aplica a escrituras, análisis,
fuentes remotas ni llamadas fuera de un GET/HEAD protegido.
"""
from concurrent.futures import Future
from copy import deepcopy
from functools import wraps
from inspect import signature
from threading import Lock

from lecturas_http import solo_lectura_http


def compartir_lectura(funcion):
    firma = signature(funcion, eval_str=True)
    pendientes = {}
    lock = Lock()

    @wraps(funcion)
    def ejecutar(*args, **kwargs):
        if not solo_lectura_http.get():
            return funcion(*args, **kwargs)
        argumentos = firma.bind(*args, **kwargs)
        argumentos.apply_defaults()
        clave = repr(sorted(argumentos.arguments.items()))
        with lock:
            futuro = pendientes.get(clave)
            propietario = futuro is None
            if propietario:
                futuro = Future()
                pendientes[clave] = futuro
        if not propietario:
            return deepcopy(futuro.result())
        try:
            resultado = funcion(*args, **kwargs)
            futuro.set_result(resultado)
            return deepcopy(resultado)
        except BaseException as exc:
            futuro.set_exception(exc)
            raise
        finally:
            with lock:
                pendientes.pop(clave, None)

    # FastAPI debe resolver los tipos en el módulo original, no en este wrapper.
    ejecutar.__signature__ = firma
    return ejecutar
