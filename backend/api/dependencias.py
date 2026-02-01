# -*- coding: utf-8 -*-
"""
dependencias.py — Dependencias comunes para la API.

IMPORTANTE: Este archivo DEBE estar en backend/api/dependencias.py
"""

from __future__ import annotations

import os
from uuid import UUID

from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, status

# UUID de usuario de desarrollo (debe coincidir con setup_completo.py)
USUARIO_DESARROLLO = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class UsuarioActual:
    """Modelo simple para representar al usuario autenticado."""
    id: UUID
    email: Optional[str] = None


def obtener_usuario_id(
    x_usuario_id: str | None = Header(None, alias="X-Usuario-Id")
) -> UUID:
    """
    Obtiene el UUID del usuario autenticado desde el header.
    En desarrollo, usa usuario de prueba automáticamente.
    """
    if not x_usuario_id:
        entorno = os.getenv("ENTORNO", "desarrollo")
        if entorno == "desarrollo":
            return UUID(USUARIO_DESARROLLO)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere el header X-Usuario-Id.",
        )
    
    try:
        return UUID(x_usuario_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Usuario-Id debe ser un UUID válido.",
        ) from exc


def obtener_usuario_id_opcional(
    x_usuario_id: Optional[str] = Header(None, alias="X-Usuario-Id")
) -> Optional[UUID]:
    """Obtiene el UUID si viene en el header, sin fallback de desarrollo."""
    if not x_usuario_id:
        return None
    try:
        return UUID(x_usuario_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Usuario-Id debe ser un UUID válido.",
        ) from exc


def obtener_usuario_actual(
    usuario_id: Optional[str] = Header(None, alias="X-Usuario-Id"),
    x_usuario_email: Optional[str] = Header(None, alias="X-Usuario-Email"),
) -> UsuarioActual:
    """
    Devuelve el usuario autenticado como objeto UsuarioActual.
    """
    usuario_uuid = obtener_usuario_id(usuario_id)
    return UsuarioActual(id=usuario_uuid, email=x_usuario_email)
