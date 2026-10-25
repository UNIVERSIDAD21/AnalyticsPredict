"""Archivo inmutable por SHA-256 y escrituras atómicas; nunca usa PostgreSQL."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


class ArchivoError(RuntimeError):
    pass


def bytes_json(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomico(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp = tempfile.mkstemp(prefix=".wnba-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def guardar_json(path: Path, value) -> None:
    atomico(path, bytes_json(value))


def append_json(path: Path, value) -> None:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode() + b"\n"
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "ab") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


@contextmanager
def bloqueo(root: Path):
    """Lock del sistema operativo: también se libera al interrumpir el proceso."""
    import fcntl

    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(root / ".wnba.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ArchivoError("Otro scraper WNBA está usando esta carpeta") from exc
        yield
    finally:
        os.close(fd)


class Archivo:
    def __init__(self, root: Path):
        self.root = root

    def guardar(self, url: str, raw: bytes, observado: str) -> dict:
        digest = sha256(raw)
        path = self.root / "raw" / f"{digest}.json"
        if path.exists():
            if sha256(path.read_bytes()) != digest:
                raise ArchivoError("Raw existente alterado; no se sobrescribe")
        else:
            atomico(path, raw)
        meta = {"url": url, "sha256": digest, "observado_utc": observado,
                "bytes": len(raw), "http_status": 200}
        key = sha256(url.encode())
        # Conserva TODAS las observaciones, incluso si cambia una respuesta del proveedor.
        from uuid import uuid4
        guardar_json(self.root / "observaciones" / f"{key}-{uuid4().hex}.json", meta)
        guardar_json(self.root / "cache" / f"{key}.json", meta)
        return meta

    def cargar(self, url: str) -> tuple[dict, dict] | None:
        pointer = self.root / "cache" / f"{sha256(url.encode())}.json"
        if not pointer.exists():
            return None
        try:
            meta = json.loads(pointer.read_bytes())
            digest = meta["sha256"]
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("hash")
            raw = (self.root / "raw" / f"{digest}.json").read_bytes()
            if meta["url"] != url or meta["http_status"] != 200 or sha256(raw) != digest or len(raw) != meta["bytes"]:
                raise ValueError("integridad")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("contrato")
            return value, meta
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise ArchivoError("Caché incompleta o alterada; conservar e investigar, no sobrescribir") from exc
