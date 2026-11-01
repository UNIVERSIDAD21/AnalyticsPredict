"""Restaurar la entrega en una BD local nueva; jamás sobrescribe bases existentes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
from urllib.parse import quote, urlencode

from psycopg import sql
from verificar_bd import comparar, conectar, host_local, huella, verificar_archivos

ADITIVAS = {"public.horarios_baloncesto", "public.horarios_futbol",
            "public.revisiones_agenda", "public.sincronizaciones_agenda"}


def crear_base_sql(base, role, provider='builtin', locale='C.UTF-8'):
    prefix=sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0 ENCODING 'UTF8' ").format(
        sql.Identifier(base),sql.Identifier(role))
    if provider=='builtin':
        return prefix+sql.SQL('LOCALE_PROVIDER builtin BUILTIN_LOCALE {}').format(sql.Literal(locale))
    if provider=='icu':
        return prefix+sql.SQL('LOCALE_PROVIDER icu ICU_LOCALE {}').format(sql.Literal(locale))
    if provider=='libc':
        return prefix+sql.SQL('LOCALE_PROVIDER libc LC_COLLATE {} LC_CTYPE {}').format(sql.Literal(locale),sql.Literal(locale))
    raise ValueError('Proveedor de locale no permitido')


def proteger(path):
    path.chmod(0o600 if path.is_file() else 0o700)
    if os.name == "nt":
        domain = os.environ.get("USERDOMAIN", "")
        user = getpass.getuser()
        principal = f"{domain}\\{user}" if domain else user
        subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", principal + ":(F)",
                        "*S-1-5-18:(F)"], check=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--puerto", type=int, required=True)
    parser.add_argument("--administrador", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument('--locale-provider',choices=('builtin','libc','icu'),default='builtin')
    parser.add_argument('--locale',default='C.UTF-8',help='Locale explícito; builtin C.UTF-8 conserva conversiones Unicode simples en Windows')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "MANIFIESTO.json").read_text(encoding="utf-8"))
    if (manifest['database']['kind'] != 'current_consistent_export'
            or not manifest['database'].get('current_neon_equivalent')):
        raise ValueError("Falta exportacion vigente verificada: el respaldo historico no esta autorizado")
    if not host_local(args.host) or not 1 <= args.puerto <= 65535:
        raise ValueError("Destino no local o puerto inválido")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,54}", args.base):
        raise ValueError("Nombre de base no válido")
    verificar_archivos(root, manifest)
    expected = json.loads((root / "SNAPSHOT_ESPERADO.json").read_text(encoding="utf-8"))
    receipt = json.loads((root / 'RECIBO_EXPORTACION_VIGENTE.json').read_text(encoding='utf-8'))
    if (not receipt.get('source_data_unchanged_at_verification')
            or receipt.get('cut') != manifest['database']['cut']
            or receipt.get('source_origin_kind') != manifest['source_identity']['origin_kind']
            or receipt.get('dump_sha256') != manifest['files'][manifest['database']['file']]):
        raise ValueError('No hay recibo consistente que acredite la copia vigente')
    executable = args.pg_bin / ("pg_restore.exe" if os.name == "nt" else "pg_restore")
    version = subprocess.run([str(executable), "--version"], capture_output=True, text=True, check=True)
    if not re.search(r"PostgreSQL\) 18\.", version.stdout):
        raise ValueError("Este paquete requiere pg_restore 18.x")
    dump = root / manifest["database"]["file"]
    subprocess.run([str(executable), "--list", str(dump)], capture_output=True, check=True)
    config = dict(host=args.host, port=args.puerto, user=args.administrador, dbname="postgres")
    # Las credenciales administrativas proceden de PGPASSFILE/PGPASSWORD o del mecanismo existente.
    with conectar(**config, autocommit=True) as admin:
        if int(admin.execute("SHOW server_version_num").fetchone()[0]) // 10000 != 18:
            raise ValueError("El servidor destino debe ser PostgreSQL 18.x")
        if admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (args.base,)).fetchone():
            raise ValueError("La base destino ya existe; no se sobrescribirá")
        data_directory = Path(admin.execute('SHOW data_directory').fetchone()[0])
        disk_path = data_directory.anchor if os.name == 'nt' else data_directory
        if shutil.disk_usage(disk_path).free < expected['database_bytes']*2+512*1024**2:
            raise ValueError('Margen de disco insuficiente en el volumen PostgreSQL destino')
        required = {"pgcrypto", "pg_trgm", "uuid-ossp"}
        available = {r[0] for r in admin.execute("SELECT name FROM pg_available_extensions")}
        if not required.issubset(available):
            raise ValueError("Faltan extensiones requeridas en el servidor local")
        role = "ap_" + args.base
        if admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
            raise ValueError("El rol destino ya existe; elige otro nombre de base")
        envfile = root / "producto/backend/.env"
        if envfile.exists():
            raise ValueError("Existe backend/.env: este asistente no sobrescribe configuraciones")
        run = root / "runtime" / args.base
        run.mkdir(parents=True, exist_ok=False)
        proteger(run)
        password = secrets.token_urlsafe(32)
        query = {"sslmode": "disable"}
        if args.host.startswith("/"):
            authority = ""
            query.update(host=args.host, port=str(args.puerto))
        else:
            host_uri = "[" + args.host + "]" if ":" in args.host else args.host
            authority = host_uri + ":" + str(args.puerto)
        uri = f"postgresql://{quote(role,safe='')}:{quote(password,safe='')}@{authority}/{args.base}?{urlencode(query)}"
        values = {"DATABASE_URL": uri,
                  "ANALYTICSPREDICT_MODELO_NBA_ACTIVO": str(root / "estado/modelo_nba_activo.npz"),
                  "ANALYTICSPREDICT_MODELO_EUROLIGA_ACTIVO": str(root / "estado/euroliga/activo.json"),
                  "ANALYTICSPREDICT_MODELO_WNBA_ACTIVO": str(root / "estado/wnba/activo.json"),
                  "ANALYTICSPREDICT_EUROLIGA_JOURNAL": str(root / "estado/euroliga/analisis"),
                  "AP_AGENDA_ESTADO": str(root / "estado/agenda-sinc-local")}
        pending = run / "credenciales_pendientes.env"
        with pending.open("x", encoding="utf-8", newline="\n") as dest:
            for key, value in values.items():
                dest.write(key + "=" + json.dumps(value, ensure_ascii=False) + "\n")
        proteger(pending)
        admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
            sql.Identifier(role), sql.Literal(password)))
        admin.execute(crear_base_sql(args.base,role,args.locale_provider,args.locale))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    for key in ("PGPASSWORD", "PGPASSFILE"):
        if key in os.environ:
            env[key] = os.environ[key]
    env.update(PGHOST=args.host, PGPORT=str(args.puerto), PGUSER=args.administrador,
               PGDATABASE=args.base, PGSSLMODE="disable", PGCHANNELBINDING="disable")
    log = run / "restauracion.log"
    with log.open("x", encoding="utf-8") as dest:
        proteger(log)
        subprocess.run([str(executable), "--exit-on-error", "--single-transaction", "--no-owner",
                        "--no-acl", "--role=" + role, "--dbname=" + args.base, str(dump)],
                       env=env, stdout=dest, stderr=subprocess.STDOUT, check=True)
    app = dict(host=args.host, port=args.puerto, user=role, dbname=args.base, password=password)
    with conectar(**app) as conn:
        restored = huella(conn, expected)
    failures = comparar(expected, restored)
    if failures:
        raise ValueError("La restauración no coincide con el snapshot; no se activará")
    # Solo DDL aditivo revisado, sin reaplicar el plan antiguo de 2.267 operaciones.
    migration = root / "producto/backend/migrations/2026-10-26_sincronizacion_agendas.sql"
    with conectar(**app) as conn:
        conn.execute(migration.read_text(encoding="utf-8"))
    with conectar(**app) as conn:
        upgraded = huella(conn, expected)
    if comparar(expected, upgraded, ADITIVAS):
        raise ValueError("La adecuación de esquema alteró datos del snapshot")
    with envfile.open("x", encoding="utf-8", newline="\n") as dest:
        proteger(envfile)
        dest.write(pending.read_text(encoding="utf-8"))
    pending.unlink()
    report = {"restore_verified": True, "windows_application_verified": False,
              "data_cut": manifest["database"]["cut"], "database": args.base,
              "source_origin_kind": manifest['source_identity']['origin_kind'],
              "host": args.host, "port": args.puerto,
              "snapshot_tables_verified": len(expected["tables"]),
              "snapshot_rows_verified": sum(t["rows"] for t in expected["tables"].values()),
              "tables_after_additive_schema": len(upgraded["tables"]),
              "database_bytes": upgraded["database_bytes"], "external_database_required": False,
              "completed_utc": datetime.now(timezone.utc).isoformat()}
    report['database_locale_provider']=args.locale_provider
    report['database_locale_requested']=args.locale
    (run / "RESULTADO_RESTAURACION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                    encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # No imprimir excepciones del driver ni cadenas que puedan contener credenciales.
        reason = str(exc) if isinstance(exc, ValueError) else "Consultar el registro privado de restauración"
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "reason": reason}, ensure_ascii=False))
        raise SystemExit(1)
