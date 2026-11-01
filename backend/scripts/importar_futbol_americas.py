"""Importa exportaciones locales MLS/LATAM. Dry-run READ ONLY por defecto.

Aplicar/ensayar exige plan previamente verificado y respaldo con hash. No descarga,
no trunca, no entrena, no confirma nada fuera de la transacción delimitada.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, time, timedelta, timezone
import gzip
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg.rows import dict_row
from db import obtener_database_url
from ingesta_futbol_americas import ZONA, aplicar, cargar_lote, digest, planificar, preparar, sha


def guardar(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode()
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == ".gz" else data)
    path.chmod(0o600)


def leer(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reporte", type=Path, action="append", required=True)
    p.add_argument("--desde-fixtures", type=date.fromisoformat, required=True)
    p.add_argument("--hasta-fixtures", type=date.fromisoformat, required=True)
    p.add_argument("--salida", type=Path, required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--aplicar", action="store_true")
    mode.add_argument("--ensayar-rollback", action="store_true")
    p.add_argument("--plan-verificado", type=Path)
    p.add_argument("--respaldo", type=Path)
    p.add_argument("--sha256-respaldo")
    a = p.parse_args()
    repo = Path(__file__).resolve().parents[2]
    if a.salida.resolve() == repo or repo in a.salida.resolve().parents:
        p.error("La evidencia debe quedar fuera del repositorio")
    if a.hasta_fixtures < a.desde_fixtures:
        p.error("Ventana de fixtures invertida")
    escribir = a.aplicar or a.ensayar_rollback
    if escribir and (not a.plan_verificado or not a.respaldo or not a.sha256_respaldo
                     or sha(a.respaldo) != a.sha256_respaldo):
        p.error("Aplicación/ensayo requiere plan verificado y respaldo íntegro")
    if a.aplicar and (a.salida / "APLICACION_CONFIRMADA.json").exists():
        p.error("Aplicación ya confirmada: usar dry-run para comprobar idempotencia")
    inicio = datetime.combine(a.desde_fixtures, time.min, ZONA)
    fin = datetime.combine(a.hasta_fixtures + timedelta(days=1), time.min, ZONA)
    entrada = preparar([cargar_lote(r) for r in a.reporte], desde_fixtures=inicio, hasta_fixtures=fin)
    with psycopg.connect(obtener_database_url(), autocommit=True, row_factory=dict_row, connect_timeout=8) as conn:
        with conn.transaction(force_rollback=bool(a.ensayar_rollback)):
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            if not escribir:
                conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout='60s'; SET LOCAL lock_timeout='8s'")
            plan = planificar(conn, entrada)
            resumen = {"fecha_utc": datetime.now(timezone.utc).isoformat(), "modo": "APLICAR" if a.aplicar else "ENSAYO_ROLLBACK" if escribir else "READ_ONLY",
                       "acciones": plan["resumen_acciones"], "filas": len(plan["acciones"]), "apartados": len(plan["apartados"]),
                       "plan_sha256": digest(plan), "codigo_sha256": sha(Path(__file__).resolve().parents[1] / "ingesta_futbol_americas.py")}
            if escribir:
                if digest(leer(a.plan_verificado)) != digest(plan):
                    raise ValueError("Plan cambió desde su verificación; no se escribió")
                resumen["resultado"] = aplicar(conn, plan)
                resumen["respaldo_sha256"] = a.sha256_respaldo
                guardar(a.salida / "CANDADO_PRECOMMIT.json", resumen)
            else:
                guardar(a.salida / "PLAN_READONLY.json.gz", plan)
            guardar(a.salida / "RESUMEN.json", resumen)
        if a.aplicar:
            guardar(a.salida / "APLICACION_CONFIRMADA.json", resumen)
        elif a.ensayar_rollback:
            guardar(a.salida / "ENSAYO_REVERTIDO.json", resumen)
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
