"""Audita y, bajo ``--apply`` explícito, incorpora dos filas DataHub verificadas.

El modo predeterminado es READ ONLY. La identidad requiere competición,
participantes/localía, fecha local exacta, FT y candidato canónico único. Una
transacción aplica solo seis columnas que continúen NULL por partido y registra
procedencia verificable del CSV. La migración amplía únicamente el CHECK de fuente.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from psycopg import connect, sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from servicios.resolucion_multifuente_futbol import (
    CAMPOS_RECUPERABLES,
    EvidenciaCampo,
    EvidenciaNoValida,
    construir_plan_resolucion,
    extraer_evidencia_datahub_football_data_csv,
    sha256_json,
)


RAIZ_REPO = Path(__file__).resolve().parents[2]
MIGRACION = RAIZ_REPO / "backend/migrations/2026-10-20_fuente_datahub_football_data.sql"
DIRECTORIO_EVIDENCIA = Path(
    "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/"
    "RECUPERACION_MULTIFUENTE_SEGUIMIENTO_2026-10-20/DATAHUB_FOOTBALL_CSV"
)
ARCHIVO_REPORTE = DIRECTORIO_EVIDENCIA / "readonly_datahub_top5_match_audit.json"
ARCHIVO_MANIFIESTO = DIRECTORIO_EVIDENCIA / "manifest.json"
ARCHIVO_PAQUETES = DIRECTORIO_EVIDENCIA / "datapackages_manifest.json"
FUENTE = "DATAHUB_FOOTBALL_DATA"
CAMPOS_OBJETIVO = (
    "local_corners_total",
    "visitante_corners_total",
    "local_disparos_total",
    "visitante_disparos_total",
    "local_disparos_arco",
    "visitante_disparos_arco",
)
COLUMNAS_ESTADISTICAS = {
    "HC": "local_corners_total",
    "AC": "visitante_corners_total",
    "HS": "local_disparos_total",
    "AS": "visitante_disparos_total",
    "HST": "local_disparos_arco",
    "AST": "visitante_disparos_arco",
}
CODIGOS = {
    "ENG_PREMIER": "english-premier-league",
    "ESP_LALIGA": "spanish-la-liga",
    "GER_BUNDESLIGA": "german-bundesliga",
    "ITA_SERIEA": "italian-serie-a",
    "FRA_LIGUE1": "french-ligue-1",
}
ALIAS_CORTO_DATAHUB = {
    ("ESP_LALIGA", "2223", "Betis"): "Real Betis",
    ("ESP_LALIGA", "2223", "Espanol"): "Espanyol",
    ("ESP_LALIGA", "2223", "Sociedad"): "Real Sociedad",
}
DERIVADOS_PERMITIDOS = {
    "actualizado_en",
    "datos_completos",
    "datos_corners_completos",
    "datos_disparos_completos",
}
COLUMNAS_BACKUP = (
    "id", "competicion_id", "temporada_id", "equipo_local_id", "equipo_visitante_id",
    "fecha_partido", "fecha_partido_local", "jornada", "ronda", "estado",
    "local_goles_1t", "local_goles_2t", "local_goles_et", "local_goles_total",
    "visitante_goles_1t", "visitante_goles_2t", "visitante_goles_et", "visitante_goles_total",
    "local_penales", "visitante_penales", "hubo_penales", "hubo_tiempo_extra",
    "local_corners_1t", "local_corners_2t", "local_corners_total",
    "visitante_corners_1t", "visitante_corners_2t", "visitante_corners_total",
    "local_disparos_total", "local_disparos_arco", "local_disparos_fuera",
    "local_disparos_bloqueados", "visitante_disparos_total", "visitante_disparos_arco",
    "visitante_disparos_fuera", "visitante_disparos_bloqueados", "local_posesion",
    "visitante_posesion", "local_faltas", "visitante_faltas", "local_tarjetas_amarillas",
    "local_tarjetas_rojas", "visitante_tarjetas_amarillas", "visitante_tarjetas_rojas",
    "local_fueras_juego", "visitante_fueras_juego", "local_xg", "visitante_xg",
    "local_xg_1t", "visitante_xg_1t", "ganador_id", "resultado_final", "diferencia_goles",
    "fuente_datos", "sofascore_match_id", "api_football_fixture_id", "flashscore_match_id",
    "datos_completos", "datos_corners_completos", "datos_disparos_completos",
    "valido", "notas", "actualizado_en",
)


def _normalizar_nombre(value: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(value or ""))
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return "".join(char.lower() for char in texto if char.isalnum())


def _nombre_canonico_reportado(
    provider_name: str, canonical_name: str, comp_code: str, season: str
) -> tuple[bool, str]:
    """Acepta normalización directa o un crosswalk corto DataHub predeclarado."""
    if _normalizar_nombre(provider_name) == _normalizar_nombre(canonical_name):
        return True, "EXACT_NORMALIZED_CANONICAL_ALIAS"
    expected = ALIAS_CORTO_DATAHUB.get((comp_code, season, provider_name))
    return (
        expected is not None and _normalizar_nombre(expected) == _normalizar_nombre(canonical_name),
        "DATAHUB_EXPLICIT_TEAM_SHORT_NAME_CROSSWALK",
    )


def _hash_archivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _guardar_nuevo(path: Path, contenido: bytes, modo: int = 0o600) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, modo)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contenido)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        raise


def _guardar_json_nuevo(path: Path, data: Any) -> str:
    payload = (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n").encode()
    _guardar_nuevo(path, payload)
    return hashlib.sha256(payload).hexdigest()


def _leer_cohorte(evidence_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evidence_dir = evidence_dir.expanduser().resolve()
    if evidence_dir == RAIZ_REPO or RAIZ_REPO in evidence_dir.parents:
        raise EvidenciaNoValida("La evidencia debe quedar fuera del repositorio")
    report_path = evidence_dir / ARCHIVO_REPORTE.name
    manifest_path = evidence_dir / ARCHIVO_MANIFIESTO.name
    packages_path = evidence_dir / ARCHIVO_PAQUETES.name
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packages = json.loads(packages_path.read_text(encoding="utf-8"))
    if report.get("status") not in {
        "READ_ONLY_DATAHUB_TOP5_MATCH_AUDIT",
        "READ_ONLY_DATAHUB_RESIDUAL_CROSSWALK_AUDIT",
    } or not report.get("database_read_only"):
        raise EvidenciaNoValida("El reporte no acredita la auditoría READ ONLY esperada")
    if report.get("source_manifest_sha256") != _hash_archivo(manifest_path):
        raise EvidenciaNoValida("El hash del manifiesto CSV no concilia con la auditoría")
    if report.get("license") != "Open Data Commons Public Domain Dedication and License (ODC-PDDL 1.0)":
        raise EvidenciaNoValida("La licencia reportada no es ODC-PDDL")
    expected_packages = {"english-premier-league", "spanish-la-liga", "german-bundesliga", "italian-serie-a", "french-ligue-1"}
    if {item.get("slug") for item in packages.get("datasets", [])} != expected_packages:
        raise EvidenciaNoValida("El manifiesto de paquetes no contiene los cinco datasets esperados")
    if any(
        item.get("http_status") != 200
        or item.get("final_host", "").split(":")[0].split(".")[-2:] != ["datahub", "io"]
        or not any(lic.get("name") == "ODC-PDDL-1.0" for lic in item.get("license", []))
        for item in packages.get("datasets", [])
    ):
        raise EvidenciaNoValida("Metadatos/license DataHub no válidos")

    updates = [item for item in report.get("plans", []) if item.get("updates")]
    if len(updates) != 2:
        raise EvidenciaNoValida("La cohorte objetivo ya no contiene exactamente dos partidos con gaps")
    files = {
        (item.get("competition_code"), item.get("season")): item
        for item in manifest.get("files", [])
        if item.get("http_status") == 200
    }
    if len(files) != 40:
        raise EvidenciaNoValida("El manifiesto no conserva los 40 CSV esperados")
    results = []
    observed = datetime.now(timezone.utc)
    for plan_row in updates:
        source = plan_row["source"]
        canonical = plan_row["canonical"]
        if (
            set(plan_row.get("updates", {})) != set(CAMPOS_OBJETIVO)
            or plan_row.get("conflicts")
            or plan_row.get("equal_fields")
            or source["comp_code"] not in CODIGOS
            or source["date"] != canonical["local_date"]
            or canonical["estado"] != "FINALIZADO"
            or source["ft_home"] != canonical["local_goles_total"]
            or source["ft_away"] != canonical["visitante_goles_total"]
            or plan_row.get("team_name_match") not in {
                "EXACT_NORMALIZED_CANONICAL_ALIAS",
                "DATAHUB_EXPLICIT_TEAM_SHORT_NAME_CROSSWALK",
            }
            or plan_row.get("date_delta_days") != 0
        ):
            raise EvidenciaNoValida("Una fila candidata perdió identidad exacta o NULL-only")
        for side, provider_key, canonical_key in (
            ("home", "home", "home_name"),
            ("away", "away", "away_name"),
        ):
            valid, method = _nombre_canonico_reportado(
                source[provider_key], canonical[canonical_key], source["comp_code"], source["season"]
            )
            if not valid:
                raise EvidenciaNoValida("Nombre DataHub no es alias exacto ni crosswalk corto permitido")
            expected_method = plan_row.get("team_alias_methods", {}).get(side)
            if expected_method is None and plan_row.get("team_name_match") == "EXACT_NORMALIZED_CANONICAL_ALIAS":
                expected_method = "EXACT_NORMALIZED_CANONICAL_ALIAS"
            if expected_method != method:
                raise EvidenciaNoValida("El informe no documenta el método de alias aplicado")
        file_info = files.get((source["comp_code"], source["season"]))
        if file_info is None or file_info.get("sha256") != source["csv_sha256"]:
            raise EvidenciaNoValida("CSV de origen ausente o hash distinto")
        csv_path = evidence_dir / source["file"]
        raw_csv = csv_path.read_bytes()
        if _hash_archivo(csv_path) != source["csv_sha256"]:
            raise EvidenciaNoValida("Hash CSV no reproduce el manifiesto de descarga")
        reader = csv.DictReader(raw_csv.decode("utf-8-sig").splitlines())
        raw_row = None
        for line_number, row in enumerate(reader, start=2):
            if line_number == source["csv_row"]:
                raw_row = row
                break
        if raw_row is None or sha256_json(raw_row) != source["row_sha256"]:
            raise EvidenciaNoValida("La fila CSV no reproduce el hash de evidencia")
        event_id = str(plan_row["provider_event_id"])
        if event_id != f"FDATA/{source['comp_code']}/{source['season']}/{source['row_sha256'][:24]}":
            raise EvidenciaNoValida("ID determinista del evento CSV inválido")
        payload = {
            "event_id": event_id,
            "competition_code": source["comp_code"],
            "season": source["season"],
            "date": source["date"],
            "home": source["home"],
            "away": source["away"],
            "ft_home": source["ft_home"],
            "ft_away": source["ft_away"],
            "source_url": f"https://datahub.io/football/{CODIGOS[source['comp_code']]}/_r/-/season-{source['season']}.csv",
            "license": "ODC-PDDL-1.0",
            "source_file_sha256": source["csv_sha256"],
            "source_row_sha256": source["row_sha256"],
            "source_row_number": source["csv_row"],
            "raw_row": raw_row,
        }
        expected = {
            "event_id": event_id,
            "comp_code": source["comp_code"],
            "season": source["season"],
            "date": source["date"],
            "home": source["home"],
            "away": source["away"],
            "ft_home": source["ft_home"],
            "ft_away": source["ft_away"],
        }
        evidence = extraer_evidencia_datahub_football_data_csv(
            evento_id=event_id, payload=payload, esperado=expected, observado_en=observed
        )
        values = {item.campo: item.valor for item in evidence}
        if values != plan_row["updates"] or len(evidence) != 6:
            raise EvidenciaNoValida("Valores del CSV no reproducen el plan de seis columnas")
        results.append({"plan": plan_row, "payload": payload, "expected": expected, "evidence": evidence})
    return results, {"report_sha256": _hash_archivo(report_path), "manifest_sha256": _hash_archivo(manifest_path), "packages_manifest_sha256": _hash_archivo(packages_path)}


def _leer_estado(conn: Any, match_ids: list[str]) -> dict[str, dict[str, Any]]:
    columnas = list(COLUMNAS_BACKUP)
    query = sql.SQL(
        "SELECT {} FROM partidos_futbol WHERE id=ANY(%s::uuid[]) ORDER BY id"
    ).format(sql.SQL(",").join(sql.Identifier(campo) for campo in columnas))
    return {str(row["id"]): dict(row) for row in conn.execute(query, (match_ids,)).fetchall()}


def _leer_contexto(conn: Any, match_ids: list[str]) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """SELECT p.id::text AS id,c.codigo AS competition_code,p.estado::text AS state,
                  p.fecha_partido_local::date AS local_date,p.local_goles_total,p.visitante_goles_total,
                  p.competicion_id::text AS competition_id,p.equipo_local_id::text AS home_team_id,
                  p.equipo_visitante_id::text AS away_team_id,
                  el.nombre AS home_name,el.nombre_corto AS home_short,el.nombre_comun AS home_common,
                  el.abreviatura AS home_abbr,ev.nombre AS away_name,ev.nombre_corto AS away_short,
                  ev.nombre_comun AS away_common,ev.abreviatura AS away_abbr,
                  p.fuente_datos,p.sofascore_match_id,
                  p.local_corners_total,p.visitante_corners_total,p.local_disparos_total,
                  p.visitante_disparos_total,p.local_disparos_arco,p.visitante_disparos_arco
           FROM partidos_futbol p JOIN competiciones_futbol c ON c.id=p.competicion_id
           JOIN equipos_futbol el ON el.id=p.equipo_local_id
           JOIN equipos_futbol ev ON ev.id=p.equipo_visitante_id
           WHERE p.id=ANY(%s::uuid[])""",
        (match_ids,),
    ).fetchall()
    return {str(row["id"]): dict(row) for row in rows}


def _validar_contexto(read_conn: Any, cohort: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    ids = [str(item["plan"]["canonical"]["id"]) for item in cohort]
    rows = _leer_contexto(read_conn, ids)
    if len(rows) != 2:
        raise EvidenciaNoValida("El conjunto canónico difiere de los dos partidos candidatos")
    for item in cohort:
        plan = item["plan"]
        source = plan["source"]
        canonical = plan["canonical"]
        row = rows[str(canonical["id"])]
        home_aliases = {row[k] for k in ("home_name", "home_short", "home_common", "home_abbr") if row[k]}
        away_aliases = {row[k] for k in ("away_name", "away_short", "away_common", "away_abbr") if row[k]}
        home_match, home_method = _nombre_canonico_reportado(
            source["home"], row["home_name"], source["comp_code"], source["season"]
        )
        away_match, away_method = _nombre_canonico_reportado(
            source["away"], row["away_name"], source["comp_code"], source["season"]
        )
        if home_match and home_method == "EXACT_NORMALIZED_CANONICAL_ALIAS":
            home_match = _normalizar_nombre(source["home"]) in {_normalizar_nombre(x) for x in home_aliases}
        if away_match and away_method == "EXACT_NORMALIZED_CANONICAL_ALIAS":
            away_match = _normalizar_nombre(source["away"]) in {_normalizar_nombre(x) for x in away_aliases}
        if (
            row["competition_code"] != source["comp_code"]
            or row["home_team_id"] != canonical["equipo_local_id"]
            or row["away_team_id"] != canonical["equipo_visitante_id"]
            or row["home_name"] != canonical["home_name"]
            or row["away_name"] != canonical["away_name"]
            or row["state"] != "FINALIZADO"
            or row["local_date"].isoformat() != source["date"]
            or row["local_goles_total"] != source["ft_home"]
            or row["visitante_goles_total"] != source["ft_away"]
            or not home_match
            or not away_match
            or plan.get("team_alias_methods", {}).get(
                "home", "EXACT_NORMALIZED_CANONICAL_ALIAS"
                if plan.get("team_name_match") == "EXACT_NORMALIZED_CANONICAL_ALIAS" else None
            ) != home_method
            or plan.get("team_alias_methods", {}).get(
                "away", "EXACT_NORMALIZED_CANONICAL_ALIAS"
                if plan.get("team_name_match") == "EXACT_NORMALIZED_CANONICAL_ALIAS" else None
            ) != away_method
            or any(row[campo] is not None for campo in CAMPOS_OBJETIVO)
            or row["fuente_datos"] != "SOFASCORE"
        ):
            raise EvidenciaNoValida("Identidad o NULLs canónicos cambiaron desde el informe READ ONLY")
        unique = read_conn.execute(
            """SELECT count(*) AS n FROM partidos_futbol p
               WHERE p.competicion_id=%s AND p.estado='FINALIZADO'
                 AND p.fecha_partido_local::date=%s
                 AND p.equipo_local_id=%s AND p.equipo_visitante_id=%s
                 AND p.local_goles_total=%s AND p.visitante_goles_total=%s""",
            (row["competition_id"], source["date"], row["home_team_id"], row["away_team_id"], source["ft_home"], source["ft_away"]),
        ).fetchone()
        if unique["n"] != 1:
            raise EvidenciaNoValida("Identidad por fecha/equipos/FT no es única en Neon")
        if read_conn.execute(
            "SELECT 1 FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=%s",
            (FUENTE, item["payload"]["event_id"]),
        ).fetchone():
            raise EvidenciaNoValida("El ID DataHub ya está vinculado; se requiere nuevo postflight")
    return rows


def _leer_restricciones(conn: Any) -> dict[str, str]:
    rows = conn.execute(
        """SELECT conname,pg_get_constraintdef(oid) AS definition FROM pg_constraint
           WHERE conrelid IN ('vinculos_multifuente_partidos_futbol'::regclass,
                              'observaciones_multifuente_estadisticas_futbol'::regclass)
             AND conname IN ('vinculos_multifuente_partidos_futbol_fuente_check',
                             'observaciones_multifuente_estadisticas_futbol_fuente_check')"""
    ).fetchall()
    return {row["conname"]: row["definition"] for row in rows}


def _json_serializable(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value.isoformat() if hasattr(value, "isoformat") else str(value) if value is not None else None for key, value in row.items()}


def _backup_preaplicacion(
    conn: Any,
    before: dict[str, dict[str, Any]],
    cohort: list[dict[str, Any]],
    source_hashes: dict[str, str],
    backup_dir: Path,
) -> dict[str, Any]:
    backup_dir = backup_dir.expanduser().resolve()
    if backup_dir == RAIZ_REPO or RAIZ_REPO in backup_dir.parents:
        raise ValueError("El backup debe permanecer fuera del repositorio")
    if backup_dir.exists():
        raise FileExistsError("El directorio de backup ya existe; no se sobrescribe")
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(backup_dir, 0o700)
    match_ids = sorted(before)
    links = conn.execute(
        "SELECT fuente,id_evento_fuente,partido_id::text,registrado_en FROM vinculos_multifuente_partidos_futbol WHERE partido_id=ANY(%s::uuid[]) ORDER BY fuente,id_evento_fuente",
        (match_ids,),
    ).fetchall()
    observations = conn.execute(
        "SELECT fuente,id_evento_fuente,partido_id::text,campo,valor,clave_proveedor,periodo_proveedor,sha256_payload,contrato,evidencia_identidad,observado_en,registrado_en FROM observaciones_multifuente_estadisticas_futbol WHERE partido_id=ANY(%s::uuid[]) ORDER BY fuente,id_evento_fuente,campo,clave_proveedor,periodo_proveedor,sha256_payload,contrato",
        (match_ids,),
    ).fetchall()
    backup = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "database_url_stored": False,
        "matches": {match_id: _json_serializable(row) for match_id, row in before.items()},
        "source_links_before": [dict(row) for row in links],
        "source_observations_before": [dict(row) for row in observations],
        "source_constraints_before": _leer_restricciones(conn),
        "source_constraints_were_already_extended": all(
            FUENTE in definition for definition in _leer_restricciones(conn).values()
        ),
        "input_hashes": source_hashes,
        "target_updates": [
            {"partido_id": str(item["plan"]["canonical"]["id"]), "updates": item["plan"]["updates"]}
            for item in cohort
        ],
        "migration_sha256": _hash_archivo(MIGRACION),
        "rollback": "Restaurar snapshots de partidos y observaciones/vínculos bajo transacción; retirar DATAHUB_FOOTBALL_DATA de los CHECK solo tras eliminar sus filas de procedencia.",
    }
    compressed = gzip.compress((json.dumps(backup, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")) + "\n").encode(), mtime=0)
    backup_path = backup_dir / "estado_preaplicacion.json.gz"
    _guardar_nuevo(backup_path, compressed)
    backup_manifest = {
        "backup_file": backup_path.name,
        "backup_sha256": hashlib.sha256(compressed).hexdigest(),
        "directory_mode": "0700",
        "file_mode": "0600",
        "rows": len(before),
        "links_backed_up": len(links),
        "observations_backed_up": len(observations),
        "read_only_preflight": True,
        "database_url_stored": False,
    }
    _guardar_json_nuevo(backup_dir / "manifest.json", backup_manifest)
    if hashlib.sha256(backup_path.read_bytes()).hexdigest() != backup_manifest["backup_sha256"]:
        raise EvidenciaNoValida("La huella del backup privado no concilia")
    return {**backup_manifest, "directory": str(backup_dir), "source_constraints_before": backup["source_constraints_before"]}


def _ejecutar_migracion(conn: Any) -> None:
    if not MIGRACION.is_file():
        raise EvidenciaNoValida("Migración de fuente ausente")
    bloques = []
    for fragmento in MIGRACION.read_text(encoding="utf-8").split(";"):
        texto = re.sub(r"(?m)^\s*--.*$", "", fragmento).strip()
        if texto and texto.upper() not in {"BEGIN", "COMMIT"}:
            bloques.append(texto)
    for statement in bloques:
        conn.execute(statement)
    constraints = _leer_restricciones(conn)
    if len(constraints) != 2 or any(FUENTE not in value for value in constraints.values()):
        raise EvidenciaNoValida("Postflight DDL no habilitó la fuente esperada")


def _insertar_aplicacion(conn: Any, cohort: list[dict[str, Any]], before: dict[str, dict[str, Any]]) -> dict[str, Any]:
    applied = Counter()
    now = datetime.now(timezone.utc)
    for item in cohort:
        plan_row = item["plan"]
        source = plan_row["source"]
        canonical = plan_row["canonical"]
        match_id = str(canonical["id"])
        event_id = item["payload"]["event_id"]
        conn.execute(
            "INSERT INTO vinculos_multifuente_partidos_futbol (fuente,id_evento_fuente,partido_id) VALUES (%s,%s,%s)",
            (FUENTE, event_id, match_id),
        )
        alias_methods = plan_row.get("team_alias_methods", {
            "home": "EXACT_NORMALIZED_CANONICAL_ALIAS",
            "away": "EXACT_NORMALIZED_CANONICAL_ALIAS",
        })
        identity = {
            "metodo": "DATAHUB_FOOTBALL_DATA_EXACT_LOCAL_DATE_TEAM_ALIASES_FT_V1",
            "canonical_competition_code": source["comp_code"],
            "canonical_competition_id": str(before[match_id]["competicion_id"]),
            "provider_dataset": item["payload"]["source_url"],
            "provider_competition_code": source["comp_code"],
            "provider_season": source["season"],
            "provider_date_local": source["date"],
            "canonical_date_local": source["date"],
            "provider_home_name": source["home"],
            "provider_away_name": source["away"],
            "canonical_home_team_id": str(before[match_id]["equipo_local_id"]),
            "canonical_away_team_id": str(before[match_id]["equipo_visitante_id"]),
            "provider_ft": [source["ft_home"], source["ft_away"]],
            "canonical_ft": [source["ft_home"], source["ft_away"]],
            "provider_row_number": source["csv_row"],
            "provider_row_sha256": source["row_sha256"],
            "provider_file_sha256": source["csv_sha256"],
            "provider_license": item["payload"]["license"],
            "team_name_match": plan_row.get("team_name_match", "EXACT_NORMALIZED_CANONICAL_ALIAS"),
            "team_alias_methods": alias_methods,
            "identity_unique_in_database": True,
            "datahub_event_id": event_id,
        }
        json.dumps(identity, allow_nan=False)
        for evidence in item["evidence"]:
            conn.execute(
                """INSERT INTO observaciones_multifuente_estadisticas_futbol
                   (fuente,id_evento_fuente,partido_id,campo,valor,clave_proveedor,
                    periodo_proveedor,sha256_payload,contrato,evidencia_identidad,observado_en)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    evidence.fuente,
                    evidence.evento_id,
                    match_id,
                    evidence.campo,
                    evidence.valor,
                    evidence.clave_proveedor,
                    evidence.periodo_proveedor,
                    evidence.sha256_payload,
                    evidence.contrato,
                    Jsonb(identity),
                    evidence.observado_en,
                ),
            )
        assignments = [sql.SQL("{}=%s").format(sql.Identifier(campo)) for campo in sorted(plan_row["updates"])]
        values = [plan_row["updates"][campo] for campo in sorted(plan_row["updates"])]
        null_guard = sql.SQL(" AND ").join(sql.SQL("{} IS NULL").format(sql.Identifier(campo)) for campo in CAMPOS_OBJETIVO)
        query = sql.SQL("UPDATE partidos_futbol SET {} WHERE id=%s AND estado='FINALIZADO' AND local_goles_total=%s AND visitante_goles_total=%s AND {}").format(
            sql.SQL(",").join(assignments), null_guard
        )
        cursor = conn.execute(query, [*values, match_id, source["ft_home"], source["ft_away"]])
        if cursor.rowcount != 1:
            raise EvidenciaNoValida("Guardas de UPDATE no afectaron exactamente una fila")
        applied["matches"] += 1
        applied["values"] += len(values)
    return dict(applied)


def _validar_resultado(conn: Any, cohort: list[dict[str, Any]], before: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ids = sorted(before)
    after = _leer_estado(conn, ids)
    if set(after) != set(ids):
        raise EvidenciaNoValida("Postflight interno: no se recuperaron todos los partidos")
    changes = Counter()
    for item in cohort:
        plan = item["plan"]
        match_id = str(plan["canonical"]["id"])
        row = after[match_id]
        for field, expected in plan["updates"].items():
            if row[field] != expected:
                raise EvidenciaNoValida("Postflight interno: valor canónico no concilia")
        for field in COLUMNAS_BACKUP:
            old, new = before[match_id][field], row[field]
            if old != new:
                changes[field] += 1
                if field not in set(CAMPOS_OBJETIVO) | DERIVADOS_PERMITIDOS:
                    raise EvidenciaNoValida(f"Postflight interno: cambió columna no autorizada {field}")
        link = conn.execute(
            "SELECT partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=%s",
            (FUENTE, item["payload"]["event_id"]),
        ).fetchone()
        if link is None or str(link["partido_id"]) != match_id:
            raise EvidenciaNoValida("Postflight interno: vínculo de evento ausente o incorrecto")
        evidence = conn.execute(
            "SELECT campo,valor,sha256_payload FROM observaciones_multifuente_estadisticas_futbol WHERE fuente=%s AND id_evento_fuente=%s AND partido_id=%s",
            (FUENTE, item["payload"]["event_id"], match_id),
        ).fetchall()
        if len(evidence) != 6 or {entry["campo"]: int(entry["valor"]) for entry in evidence} != plan["updates"]:
            raise EvidenciaNoValida("Postflight interno: procedencia no reproduce los seis valores")
        if {entry["sha256_payload"] for entry in evidence} != {item["payload"]["source_row_sha256"]}:
            raise EvidenciaNoValida("Postflight interno: hash de fila de procedencia no concilia")
    return {"matches": len(after), "fields": sum(len(item["plan"]["updates"]) for item in cohort), "changed_columns_by_match_count": dict(changes)}


def ejecutar(evidence_dir: Path, *, apply: bool, backup_dir: Path | None) -> dict[str, Any]:
    cohort, source_hashes = _leer_cohorte(evidence_dir)
    match_ids = sorted(str(item["plan"]["canonical"]["id"]) for item in cohort)
    load_dotenv(RAIZ_REPO / "backend/.env", override=False)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no está disponible en el mecanismo protegido")
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as read_conn:
        read_conn.read_only = True
        with read_conn.transaction():
            read_conn.execute("SET TRANSACTION READ ONLY")
            read_conn.execute("SET LOCAL statement_timeout='45s'")
            before = _leer_estado(read_conn, match_ids)
            if len(before) != 2:
                raise EvidenciaNoValida("El preflight no recuperó las dos filas completas")
            context = _validar_contexto(read_conn, cohort)
            constraints = _leer_restricciones(read_conn)
            migration_needed = len(constraints) != 2 or any(FUENTE not in value for value in constraints.values())
            if not migration_needed and any(FUENTE not in value for value in constraints.values()):
                raise EvidenciaNoValida("Estado inesperado de restricciones de fuente")
            if not apply:
                return {
                    "status": "READ_ONLY_PREFLIGHT_OK",
                    "database_read_only": True,
                    "matches": 2,
                    "values": 12,
                    "migration_needed": migration_needed,
                    "source_hashes": source_hashes,
                    "source_constraints": constraints,
                    "targets": [
                        {"match_id": str(item["plan"]["canonical"]["id"]), "event_id": item["payload"]["event_id"], "updates": item["plan"]["updates"], "canonical_names": [context[str(item["plan"]["canonical"]["id"])]["home_name"], context[str(item["plan"]["canonical"]["id"])]["away_name"]]}
                        for item in cohort
                    ],
                }
    if backup_dir is None:
        raise ValueError("--apply requiere --backup-dir privado nuevo")
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as backup_conn:
        backup_conn.read_only = True
        with backup_conn.transaction():
            backup_conn.execute("SET TRANSACTION READ ONLY")
            backup_conn.execute("SET LOCAL statement_timeout='45s'")
            before = _leer_estado(backup_conn, match_ids)
            _validar_contexto(backup_conn, cohort)
            backup = _backup_preaplicacion(backup_conn, before, cohort, source_hashes, backup_dir)
    try:
        with connect(database_url, connect_timeout=12, row_factory=dict_row) as write_conn:
            with write_conn.transaction():
                write_conn.execute("SET LOCAL lock_timeout='5s'")
                write_conn.execute("SET LOCAL statement_timeout='60s'")
                locked = _leer_estado_for_update(write_conn, match_ids)
                if _serializar_estados(locked) != _serializar_estados(before):
                    raise EvidenciaNoValida("El estado canónico cambió después del backup")
                _validar_contexto(write_conn, cohort)
                current_constraints = _leer_restricciones(write_conn)
                if any(FUENTE not in value for value in current_constraints.values()):
                    _ejecutar_migracion(write_conn)
                applied = _insertar_aplicacion(write_conn, cohort, locked)
                postflight_transaction = _validar_resultado(write_conn, cohort, locked)
            with connect(database_url, connect_timeout=12, row_factory=dict_row) as post_conn:
                post_conn.read_only = True
                with post_conn.transaction():
                    post_conn.execute("SET TRANSACTION READ ONLY")
                    post_conn.execute("SET LOCAL statement_timeout='45s'")
                    postflight_independent = _validar_resultado(post_conn, cohort, before)
        result = {
            "status": "APPLIED_AND_VERIFIED",
            "database_read_only": False,
            "migration_applied": backup["source_constraints_before"] and any(FUENTE not in v for v in backup["source_constraints_before"].values()),
            "applied": applied,
            "transaction_postflight": postflight_transaction,
            "independent_read_only_postflight": postflight_independent,
            "backup": backup,
            "source_hashes": source_hashes,
        }
        return result
    except Exception:
        # The backup remains the authoritative recovery point; failed transaction rolls back atomically.
        raise


def _leer_estado_for_update(conn: Any, match_ids: list[str]) -> dict[str, dict[str, Any]]:
    columnas = list(COLUMNAS_BACKUP)
    query = sql.SQL("SELECT {} FROM partidos_futbol WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE").format(
        sql.SQL(",").join(sql.Identifier(campo) for campo in columnas)
    )
    return {str(row["id"]): dict(row) for row in conn.execute(query, (match_ids,)).fetchall()}


def _serializar_estados(rows: dict[str, dict[str, Any]]) -> str:
    normalized = {match_id: _json_serializable(row) for match_id, row in sorted(rows.items())}
    return json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, default=DIRECTORIO_EVIDENCIA)
    parser.add_argument("--apply", action="store_true", help="Aplica únicamente el lote verificado de dos filas")
    parser.add_argument("--backup-dir", type=Path, help="Directorio privado nuevo, fuera del repositorio")
    args = parser.parse_args()
    result = ejecutar(args.evidence_dir, apply=args.apply, backup_dir=args.backup_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
