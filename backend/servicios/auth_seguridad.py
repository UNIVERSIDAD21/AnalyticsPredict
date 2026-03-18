# -*- coding: utf-8 -*-
"""Utilidades de seguridad para autenticación (hash y tokens firmados)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def obtener_secreto_auth() -> str:
    secreto = os.getenv("AUTH_SECRET_KEY", "")
    if not secreto:
        # Fallback solo para desarrollo local
        secreto = "dev-auth-secret-cambiar-en-staging"
    return secreto


def hash_password(password: str, *, iteraciones: int = 120_000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iteraciones)
    return f"pbkdf2_sha256${iteraciones}${_b64url(salt)}${_b64url(dk)}"


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        algoritmo, iteraciones_str, salt_b64, hash_b64 = password_hash.split("$", 3)
        if algoritmo != "pbkdf2_sha256":
            return False
        iteraciones = int(iteraciones_str)
        salt = _b64url_decode(salt_b64)
        hash_esperado = _b64url_decode(hash_b64)
    except Exception:
        return False

    hash_real = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iteraciones)
    return hmac.compare_digest(hash_real, hash_esperado)


def crear_token(payload: dict[str, Any], secreto: str, exp_seconds: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    cuerpo = dict(payload)
    cuerpo["exp"] = int(time.time()) + exp_seconds

    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(cuerpo, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    firma = hmac.new(secreto.encode("utf-8"), signing_input, hashlib.sha256).digest()
    firma_b64 = _b64url(firma)
    return f"{header_b64}.{payload_b64}.{firma_b64}"


def decodificar_y_validar_token(token: str, secreto: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, firma_b64 = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Formato de token inválido") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    firma_real = hmac.new(secreto.encode("utf-8"), signing_input, hashlib.sha256).digest()
    firma_recibida = _b64url_decode(firma_b64)

    if not hmac.compare_digest(firma_real, firma_recibida):
        raise ValueError("Firma de token inválida")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("Token expirado")

    return payload
