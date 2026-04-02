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
from psycopg.rows import dict_row

from db import obtener_pool
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth

# UUID de usuario de desarrollo (debe coincidir con setup_completo.py)
USUARIO_DESARROLLO = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class UsuarioActual:
    """Modelo simple para representar al usuario autenticado."""
    id: UUID
    email: Optional[str] = None


def _extraer_bearer_token(authorization: str | None) -> Optional[str]:
    if not authorization or not isinstance(authorization, str):
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return token or None


def _obtener_o_crear_usuario_uuid_por_email(email: str) -> UUID:
    email_normalizado = email.strip().lower()
    if not email_normalizado:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin email válido.")

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT id FROM usuarios WHERE lower(email) = lower(%s) LIMIT 1",
                [email_normalizado],
            )
            fila = cursor.fetchone()
            if fila and fila.get("id"):
                return UUID(str(fila["id"]))

            cursor.execute(
                """
                INSERT INTO usuarios (
                    email,
                    nombre,
                    password_hash,
                    fecha_creacion,
                    creado_en,
                    actualizado_en,
                    activo,
                    rol
                )
                VALUES (%s, %s, %s, NOW(), NOW(), NOW(), TRUE, 'usuario')
                RETURNING id
                """,
                [email_normalizado, (email_normalizado.split("@")[0] or "usuario")[:100], "NO_LOGIN_PLACEHOLDER"],
            )
            creada = cursor.fetchone()
            return UUID(str(creada["id"]))


def obtener_usuario_id(
    x_usuario_id: str | None = Header(None, alias="X-Usuario-Id"),
    authorization: str | None = Header(None, alias="Authorization"),
) -> UUID:
    """
    Obtiene UUID de usuario por prioridad:
    1) Header X-Usuario-Id
    2) Bearer token (email -> tabla usuarios)
    3) Fallback desarrollo
    """
    if x_usuario_id:
        try:
            return UUID(x_usuario_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-Usuario-Id debe ser un UUID válido.",
            ) from exc

    token = _extraer_bearer_token(authorization)
    if token:
        try:
            payload = decodificar_y_validar_token(token, obtener_secreto_auth())
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        email = payload.get("email")
        if isinstance(email, str) and email.strip():
            return _obtener_o_crear_usuario_uuid_por_email(email)

    entorno = os.getenv("ENTORNO", "desarrollo")
    if entorno == "desarrollo":
        return UUID(USUARIO_DESARROLLO)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Se requiere autenticación (Bearer o X-Usuario-Id).",
    )


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
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_usuario_email: Optional[str] = Header(None, alias="X-Usuario-Email"),
) -> UsuarioActual:
    """
    Devuelve el usuario autenticado como objeto UsuarioActual.
    """
    usuario_uuid = obtener_usuario_id(x_usuario_id=usuario_id, authorization=authorization)
    return UsuarioActual(id=usuario_uuid, email=x_usuario_email)
