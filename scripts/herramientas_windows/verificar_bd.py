"""Verificación agregada de un snapshot PostgreSQL, sin exportar valores de filas."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path

import psycopg
from psycopg import sql


def host_local(host: str) -> bool:
    if os.name != "nt" and host.startswith("/"):
        return Path(host).is_dir()
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def conectar(*, host: str, port: int, user: str, dbname: str, password=None, autocommit=False):
    if not host_local(host):
        raise ValueError("Solo se permiten IP de loopback o socket Unix local")
    for key in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS"):
        os.environ.pop(key, None)
    return psycopg.connect(host=host, port=port, user=user, dbname=dbname,
                           password=password, sslmode="disable", channel_binding="disable",
                           connect_timeout=5, autocommit=autocommit,
                           application_name="analyticspredict_traspaso_local")


def huella(conn, esperado=None):
    conn.read_only = True
    conn.execute("SET LOCAL timezone='UTC'; SET LOCAL datestyle='ISO,YMD'; "
                 "SET LOCAL extra_float_digits=3; SET LOCAL bytea_output='hex'; "
                 "SET LOCAL intervalstyle='postgres'; SET LOCAL statement_timeout='60s'")
    tables = conn.execute("""SELECT schemaname,tablename FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog','information_schema')
        AND schemaname NOT LIKE 'pg_toast%' ORDER BY schemaname,tablename""").fetchall()
    result = {"tables": {}, "sequences": {}, "database_bytes": conn.execute(
        "SELECT pg_database_size(current_database())").fetchone()[0]}
    for schema, table in tables:
        key = f"{schema}.{table}"
        columns = [r[0] for r in conn.execute("""SELECT column_name
            FROM information_schema.columns WHERE table_schema=%s AND table_name=%s
            ORDER BY ordinal_position""", (schema, table))]
        selected = esperado["tables"][key]["columns"] if esperado and key in esperado["tables"] else columns
        if not set(selected).issubset(columns):
            raise ValueError(f"Faltan columnas del snapshot: {key}")
        query = sql.SQL("""SELECT count(*),md5(COALESCE(string_agg(h,'' ORDER BY h COLLATE "C"),''))
            FROM (SELECT md5(to_jsonb(r)::text) h FROM
            (SELECT {cols} FROM {schema}.{table}) r) hashes""").format(
                cols=sql.SQL(",").join(map(sql.Identifier, selected)),
                schema=sql.Identifier(schema), table=sql.Identifier(table))
        count, digest = conn.execute(query).fetchone()
        result["tables"][key] = {"columns": selected, "rows": count, "rows_md5": digest}
    for schema, name in conn.execute("SELECT schemaname,sequencename FROM pg_sequences ORDER BY 1,2"):
        last, called = conn.execute(sql.SQL("SELECT last_value,is_called FROM {}.{}").format(
            sql.Identifier(schema), sql.Identifier(name))).fetchone()
        result["sequences"][f"{schema}.{name}"] = {"last_value": last, "is_called": called}
    result["large_objects"] = conn.execute("""SELECT count(*),
        COALESCE(sum(octet_length(lo_get(oid))),0),
        md5(COALESCE(string_agg(md5(lo_get(oid)),'' ORDER BY oid),''))
        FROM pg_largeobject_metadata""").fetchone()
    result["large_objects"] = list(result["large_objects"])
    result["extensions"] = dict(conn.execute("SELECT extname,extversion FROM pg_extension ORDER BY extname"))
    return result


def comparar(esperado, actual, tablas_aditivas=()):
    fallos = []
    for name, entry in esperado["tables"].items():
        if actual["tables"].get(name) != entry:
            fallos.append("tabla:" + name)
    extras = set(actual["tables"]) - set(esperado["tables"])
    if not extras.issubset(set(tablas_aditivas)):
        fallos.append("tablas_no_previstas")
    for name in extras:
        if actual["tables"][name]["rows"] != 0:
            fallos.append("tabla_nueva_no_vacia:" + name)
    if actual["sequences"] != esperado["sequences"]:
        fallos.append("secuencias")
    if actual["large_objects"] != esperado["large_objects"]:
        fallos.append("objetos_grandes")
    if set(actual["extensions"]) != set(esperado["extensions"]):
        fallos.append("extensiones")
    return fallos


def verificar_archivos(root: Path, manifest):
    for relative, expected in manifest["files"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("Archivo ausente o ruta no permitida: " + relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("SHA distinto: " + relative)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--puerto", type=int, required=True)
    parser.add_argument("--usuario", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--esperado", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    esperado = json.loads(args.esperado.read_text(encoding="utf-8"))
    with conectar(host=args.host, port=args.puerto, user=args.usuario, dbname=args.base) as conn:
        actual = huella(conn, esperado)
    fallos = comparar(esperado, actual)
    args.salida.write_text(json.dumps({"ok": not fallos, "fallos": fallos, "actual": actual},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1 if fallos else 0)


if __name__ == "__main__":
    main()
