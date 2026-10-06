"""Migración real sobre PostgreSQL local efímera con dos dueños sintéticos."""
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo


ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).with_name("single_user_legacy_fixture.sql")
MIGRATION = ROOT / "migrations/2026-10-05_single_user.sql"


@pytest.fixture
def db_efimera():
    admin_url = os.environ.get("TEST_PG_ADMIN_URL")
    if not admin_url:
        pytest.skip("TEST_PG_ADMIN_URL no configurada; integración PostgreSQL separada")
    cfg = conninfo_to_dict(admin_url)
    if cfg.get("host") not in {"localhost", "127.0.0.1"} or cfg.get("dbname") != "postgres":
        pytest.fail("La integración solo admite servidor local y base administradora postgres")
    nombre = f"ap_single_user_test_{uuid4().hex}"
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nombre)))
        try:
            yield make_conninfo(admin_url, dbname=nombre)
        finally:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(nombre)))


def test_migracion_conserva_historial_y_elimina_identidad(db_efimera):
    with psycopg.connect(db_efimera, autocommit=True) as conn:
        conn.execute(BASELINE.read_text(encoding="utf-8"))
        antes = {
            tabla: conn.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(tabla))).fetchone()[0]
            for tabla in ("apuestas", "apuestas_futbol", "apuestas_combinadas", "selecciones_combinada",
                          "apuestas_analizadas", "predicciones_registradas", "predicciones_futbol",
                          "partidos_baloncesto", "partidos_futbol")
        }
        conn.execute(MIGRATION.read_text(encoding="utf-8"))
        for tabla, esperado in antes.items():
            assert conn.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(tabla))).fetchone()[0] == esperado
        assert conn.execute("SELECT count(*) FROM vista_bitacora_unificada").fetchone()[0] == 4
        assert conn.execute("SELECT preferencias->>'locale' FROM configuracion_sistema").fetchone()[0] == "es"
        assert conn.execute("SELECT count(*) FROM apuestas WHERE equipo_local = 'E'").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND column_name IN ('usuario_id','user_id','auth_user_id')").fetchone()[0] == 0
        assert conn.execute("SELECT to_regclass('public.usuarios'), to_regclass('public.auth_users'), to_regclass('public.payment_intents')").fetchone() == (None, None, None)


def test_migracion_rechaza_ganador_incorrecto_y_revierte(db_efimera):
    with psycopg.connect(db_efimera, autocommit=True) as conn:
        conn.execute(BASELINE.read_text(encoding="utf-8"))
        for n in range(4):
            conn.execute(
                "INSERT INTO apuestas (id, usuario_id, equipo_local) VALUES (%s, %s, 'OTRO')",
                (uuid4(), "00000000-0000-0000-0000-000000000002"),
            )
        with pytest.raises(psycopg.errors.RaiseException, match="ganador único"):
            conn.execute(MIGRATION.read_text(encoding="utf-8"))
        conn.rollback()
        assert conn.execute("SELECT count(*) FROM apuestas").fetchone()[0] == 7
        assert conn.execute("SELECT to_regclass('public.usuarios'), to_regclass('public.configuracion_sistema')").fetchone() == ("usuarios", None)
