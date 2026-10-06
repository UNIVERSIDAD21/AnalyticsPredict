"""Ejecuta pytest sobre una base PostgreSQL local, sintética y desechable."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/integracion/suite_global_fixture.sql"


def validar_admin_local(admin_url: str) -> None:
    """Impide que la suite cree bases de prueba en un servicio remoto."""
    config = conninfo_to_dict(admin_url)
    host = config.get("host") or ""
    if (host not in {"localhost", "127.0.0.1"} and not host.startswith("/tmp/")) or config.get("dbname") != "postgres":
        raise ValueError("Solo se admite PostgreSQL local y la base administradora postgres")


def main() -> int:
    admin_url = os.environ.get("TEST_PG_ADMIN_URL")
    if not admin_url:
        raise SystemExit("TEST_PG_ADMIN_URL es obligatoria para la suite global SQL")
    validar_admin_local(admin_url)

    nombre = f"ap_suite_test_{uuid4().hex}"
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nombre)))
        try:
            url_prueba = make_conninfo(admin_url, dbname=nombre, sslmode="disable")
            with psycopg.connect(url_prueba, autocommit=True) as conexion:
                conexion.execute(FIXTURE.read_text(encoding="utf-8"))
            entorno = os.environ.copy()
            entorno["DATABASE_URL"] = url_prueba
            print(f"Suite sobre base desechable {nombre}; esquema sintético local.", flush=True)
            return subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *sys.argv[1:]],
                cwd=ROOT,
                env=entorno,
                check=False,
            ).returncode
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(nombre)))


if __name__ == "__main__":
    raise SystemExit(main())
