# -*- coding: utf-8 -*-
"""
dependencias.py — Dependencias comunes para la API.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException, status


def obtener_usuario_id(x_usuario_id: str | None = Header(None, alias="X-Usuario-Id")) -> UUID:
    """Obtiene el UUID del usuario autenticado desde el header."""
    if not x_usuario_id:
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
