# -*- coding: utf-8 -*-
"""B5 fase 2: interfaz desacoplada de proveedor de chat.

Permite cambiar entre proveedor local (default) y proveedores externos
sin romper contrato de rutas/API.
"""

from __future__ import annotations

import os
from typing import Protocol

from servicios.chat_contexto import generar_respuesta_local


class ChatProvider(Protocol):
    name: str

    def responder(self, mensaje_usuario: str, ventana: list[dict], contexto_negocio: dict | None = None) -> str: ...


class LocalChatProvider:
    name = "local-mock"

    def responder(self, mensaje_usuario: str, ventana: list[dict], contexto_negocio: dict | None = None) -> str:
        return generar_respuesta_local(mensaje_usuario, ventana, contexto_negocio=contexto_negocio)


class DisabledExternalChatProvider:
    """Proveedor placeholder para modo externo aún no configurado.

    Se mantiene para desacoplar arquitectura hoy y conectar LLM real después.
    """

    name = "external-placeholder"

    def responder(self, mensaje_usuario: str, ventana: list[dict], contexto_negocio: dict | None = None) -> str:
        base = (
            "El proveedor externo de chat aún no está configurado en este entorno. "
            "Se requiere definir credenciales e implementación del adaptador para habilitarlo."
        )
        return f"{base}\n\n⚠️ Este asistente ofrece información orientativa y educativa."


def obtener_chat_provider() -> ChatProvider:
    mode = os.getenv("CHAT_PROVIDER_MODE", "local").strip().lower()

    if mode == "external":
        # Placeholder explícito: mantiene contrato estable para fase 2 sin acoplar proveedor.
        return DisabledExternalChatProvider()

    return LocalChatProvider()
