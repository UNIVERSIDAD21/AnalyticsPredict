"""Resuelve un lote histórico mínimo de estadísticas HF con evidencia fija.

Modo predeterminado: lectura y preflight READ ONLY. ``--rehearse-rollback``
ejecuta el DDL/DML dentro de una transacción que siempre revierte. ``--apply``
requiere un directorio privado nuevo para backup y guarda link, observaciones y
valores solo si siguen nulos bajo bloqueo. No instala dependencias ni descarga
datos: consume el reporte/parquets archivados fuera del repositorio.

Fuente publicada: eatpizzanot/soccer-dataset, revisión fijada y licencia
declarada CC-BY-4.0. El card atribuye upstream a API-Football y
football-data.co.uk y advierte que puede no conceder derechos sobre todo el
contenido upstream; se conserva ese caveat en cada observación.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from psycopg import connect, sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from servicios.resolucion_multifuente_futbol import (
    EvidenciaCampo,
    EvidenciaNoValida,
    construir_plan_resolucion,
    extraer_evidencia_hf_eatpizzanot_dataset,
)


RAIZ_REPO = Path(__file__).resolve().parents[2]
FUENTE = "HF_EATPIZZANOT"
REVISION = "f0cbe86bee3f28cc4b803f735a5287968741c471"
URL_DATASET = "https://huggingface.co/datasets/eatpizzanot/soccer-dataset"
URL_REPOSITORIO = "https://github.com/v-eatpizzanot/soccer-dataset"
REPORTE = "hf_dataset_candidate_batch_v3_canonical_aliases.json"
REPORTE_SHA256 = "26997120bbcbd2b85ddf14f319cb4bb2c90a7c6985edb527e13562d6dfe02afd"
CONTRATO = "HF_EATPIZZANOT_STATS_V1"
ARCHIVOS_SHA256 = {
    "fixtures.parquet": "7ba90661dbed29eb940daf5ea385c7d76d5751d16be86bd9063293a982abc7b7",
    "league_catalogue.parquet": "ffe7a0733e997b2963e4bfde34e479fa1fff3ace2e2c8f04e57cc730fc70f4c8",
    "leagues.parquet": "55c8e198650f5e2864fac85823196f6b5b45caf8342c1308e87e351098242c58",
    "match_stats.parquet": "2fb85b14b4428e1a36efe6d651de4ca8f7a6169ecfa3edb9cda49cb5e58d97e9",
    "teams.parquet": "5529282b37ad51437142dd7c6d32fb60bbbdd56953dc432e3b9247dca17a2fa5",
}
CAMPOS = {
    "local_corners_total", "visitante_corners_total",
    "local_disparos_total", "visitante_disparos_total",
    "local_disparos_arco", "visitante_disparos_arco",
}
COLUMNAS_STATS = sorted(CAMPOS)
COLUMNAS_IDENTIDAD = [
    "competicion_id", "equipo_local_id", "equipo_visitante_id", "fecha_partido",
    "fecha_partido_local", "estado", "local_goles_total", "visitante_goles_total",
    "fuente_datos", "sofascore_match_id", "api_football_fixture_id",
]
COLUMNAS_FLAGS = [
    "datos_completos", "datos_corners_completos", "datos_disparos_completos",
    "resultado_final", "diferencia_goles", "ganador_id", "actualizado_en",
]
COLUMNAS = ["id", *COLUMNAS_IDENTIDAD, *COLUMNAS_STATS,
            "local_corners_1t", "visitante_corners_1t", "local_corners_2t",
            "visitante_corners_2t", "local_disparos_fuera", "visitante_disparos_fuera",
            "local_disparos_bloqueados", "visitante_disparos_bloqueados", *COLUMNAS_FLAGS]
ATRIBUCION = (
    "eatpizzanot; dataset Global Football (Soccer) Data Lake; CC-BY-4.0 declarada; "
    "upstream atribuido: API-Football y football-data.co.uk; revisión f0cbe86bee3f28cc4b803f735a5287968741c471; "
    "el card advierte que puede no conceder derechos sobre todo el contenido upstream."
)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(v) for v in value]
    return value


def _json_dump(path: Path, payload: Any, *, exclusive: bool = True) -> None:
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC)
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(_json_value(payload), stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
        os.chmod(path, 0o600)
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _leer_reporte(evidence_dir: Path) -> tuple[dict[str, Any], Path, dict[str, str]]:
    evidence_dir = evidence_dir.expanduser().resolve(strict=True)
    report_path = evidence_dir / REPORTE
    if report_path.is_symlink() or _sha(report_path) != REPORTE_SHA256:
        raise EvidenciaNoValida("El reporte HF no coincide con el hash fijado")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        report.get("status") != "READONLY_HF_DATASET_CANDIDATE_CROSSWALK_V1"
        or report.get("dataset_revision") != REVISION
        or report.get("declared_license") != "CC-BY-4.0"
        or report.get("dataset_url") != URL_DATASET
        or report.get("safe_candidate_matches") != 4
        or report.get("safe_null_only_updates") != 19
        or report.get("identity_crosswalk_evidence", {}).get("canonical_provider_ids_observed_null") is not True
        or report.get("identity_crosswalk_evidence", {}).get("league_api_football_id_to_canonical_code")
        != {"140":"ESP_LALIGA","2":"EUR_CHAMPIONS","78":"GER_BUNDESLIGA","135":"ITA_SERIEA"}
    ):
        raise EvidenciaNoValida("Contrato, identidad o conteos del lote HF cambiaron")
    if report.get("source_file_sha256") != ARCHIVOS_SHA256:
        raise EvidenciaNoValida("El manifiesto de archivos HF no coincide con la revisión fija")
    for name, expected in ARCHIVOS_SHA256.items():
        path = evidence_dir / name
        if path.is_symlink() or not path.is_file() or _sha(path) != expected:
            raise EvidenciaNoValida(f"Archivo HF ausente o con hash distinto: {name}")
    if len(report.get("matches", [])) != 4:
        raise EvidenciaNoValida("La cohorte HF no contiene exactamente cuatro partidos")
    total = 0
    event_ids: set[str] = set()
    match_ids: set[str] = set()
    for match in report["matches"]:
        if match.get("canonical_id") in match_ids or match.get("source_event_id") in event_ids:
            raise EvidenciaNoValida("El lote repite un partido o evento de proveedor")
        match_ids.add(match["canonical_id"])
        event_ids.add(match["source_event_id"])
        if len(match.get("updates", {})) == 0 or not set(match["updates"]).issubset(CAMPOS):
            raise EvidenciaNoValida("El lote incluye campos no autorizados o sin valores")
        total += len(match["updates"])
    if total != 19:
        raise EvidenciaNoValida("El conteo de actualizaciones no reproduce los 19 campos")
    return report, report_path, {"report_sha256": REPORTE_SHA256, **ARCHIVOS_SHA256}


def _evidencia_reporte(report: dict[str, Any]) -> dict[str, tuple[EvidenciaCampo, ...]]:
    observed_at = datetime.fromisoformat(report["observed_at_utc"])
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise EvidenciaNoValida("El instante observado del reporte no tiene zona")
    salida = {}
    for match in report["matches"]:
        registro = dict(match)
        registro.update({
            "dataset_revision": report["dataset_revision"],
            "dataset_url": report["dataset_url"],
            "declared_license": report["declared_license"],
            "source_quality_policy": report["source_quality_policy"],
        })
        evidencias = extraer_evidencia_hf_eatpizzanot_dataset(
            partido_auditado=registro,
            observado_en=observed_at,
            revision_esperada=REVISION,
        )
        if len(evidencias) != len(match["updates"]):
            raise EvidenciaNoValida("El parser HF no reproduce las observaciones del candidato")
        salida[match["canonical_id"]] = evidencias
    return salida


def _query_rows(conn: Any, ids: list[str], *, for_update: bool = False) -> dict[str, dict[str, Any]]:
    query = sql.SQL("SELECT {} FROM partidos_futbol p WHERE p.id=ANY(%s::uuid[]) ORDER BY p.id").format(
        sql.SQL(",").join(sql.SQL("p.{}").format(sql.Identifier(column)) for column in COLUMNAS)
    )
    if for_update:
        query += sql.SQL(" FOR UPDATE")
    rows = conn.execute(query, (ids,)).fetchall()
    return {str(row["id"]): dict(row) for row in rows}


def _query_identity_context(conn: Any, ids: list[str]) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """SELECT p.id::text AS id, p.competicion_id::text AS competition_id,
                  c.codigo AS competition_code, c.nombre AS competition_name,
                  c.nombre_corto AS competition_short,
                  c.api_football_id AS competition_api_id,
                  p.equipo_local_id::text AS home_team_id,
                  hl.api_football_id AS home_api_id,
                  p.equipo_visitante_id::text AS away_team_id,
                  ha.api_football_id AS away_api_id,
                  hl.nombre AS home_name, hl.nombre_corto AS home_short, hl.nombre_comun AS home_common,
                  ha.nombre AS away_name, ha.nombre_corto AS away_short, ha.nombre_comun AS away_common,
                  p.fecha_partido, p.fecha_partido_local, p.estado,
                  p.local_goles_total, p.visitante_goles_total, p.fuente_datos
                  , (SELECT count(*) FROM partidos_futbol q
                     WHERE q.competicion_id=p.competicion_id
                       AND q.equipo_local_id=p.equipo_local_id
                       AND q.equipo_visitante_id=p.equipo_visitante_id
                       AND q.fecha_partido_local=p.fecha_partido_local
                       AND q.local_goles_total=p.local_goles_total
                       AND q.visitante_goles_total=p.visitante_goles_total
                       AND q.estado='FINALIZADO') AS identity_match_count
           FROM partidos_futbol p
           JOIN competiciones_futbol c ON c.id=p.competicion_id
           JOIN equipos_futbol hl ON hl.id=p.equipo_local_id
           JOIN equipos_futbol ha ON ha.id=p.equipo_visitante_id
           WHERE p.id=ANY(%s::uuid[]) ORDER BY p.id""",
        (ids,),
    ).fetchall()
    return {row["id"]: dict(row) for row in rows}


def _identity_context_valid(report: dict[str, Any], rows: dict[str, dict[str, Any]], context: dict[str, dict[str, Any]]) -> None:
    if set(rows) != {m["canonical_id"] for m in report["matches"]} or set(context) != set(rows):
        raise EvidenciaNoValida("No se recuperaron todas las filas canónicas y sus catálogos")
    for match in report["matches"]:
        row = rows[match["canonical_id"]]
        ctx = context[match["canonical_id"]]
        league_to_competition = {140:"ESP_LALIGA",2:"EUR_CHAMPIONS",78:"GER_BUNDESLIGA",135:"ITA_SERIEA"}
        if (
            ctx["competition_code"] != match["competition_code"]
            or league_to_competition.get(match["source_league_api_football_id"]) != match["competition_code"]
            or (ctx["competition_api_id"] is not None and ctx["competition_api_id"] != match["source_league_api_football_id"])
            or (ctx["home_api_id"] is not None and ctx["home_api_id"] != match["source_home_team_api_football_id"])
            or (ctx["away_api_id"] is not None and ctx["away_api_id"] != match["source_away_team_api_football_id"])
            or row["estado"] != "FINALIZADO"
            or (row["local_goles_total"], row["visitante_goles_total"]) != tuple(match["source_ft"])
            or row["fuente_datos"] != "SOFASCORE"
            or ctx["fecha_partido_local"].isoformat() != match["canonical_local_date"]
            or ctx["identity_match_count"] != 1
        ):
            raise EvidenciaNoValida("La identidad externa ya no concilia con comp/equipos/FT/fecha canónicos")
        source_date = datetime.fromisoformat(match["source_date_utc_naive"])
        if match["source_timestamp_precision"] == "DATE_ONLY":
            if match["identity_method"] != "EXACT_COMPETITION_LOCAL_DATE_TEAMS_FT_UNIQUE_DATE_ONLY_V1":
                raise EvidenciaNoValida("Método date-only no reconocido")
            if source_date.date().isoformat() != ctx["fecha_partido_local"].isoformat():
                raise EvidenciaNoValida("La fecha de calendario date-only cambió")
            if match["source_api_football_id"] is not None:
                raise EvidenciaNoValida("Un registro date-only no debe inventar ID API-Football")
        elif match["source_timestamp_precision"] == "UTC_INSTANT_NAIVE_DOCUMENTED":
            if match["identity_method"] != "SOFASCORE_LEGACY_BOGOTA_NAIVE_TIME_PLUS_5H_EXACT_SAME_DAY_V1":
                raise EvidenciaNoValida("Método temporal +5h no reconocido")
            canonical = row["fecha_partido"].astimezone(timezone.utc)
            source_as_utc = source_date.replace(tzinfo=timezone.utc)
            if source_as_utc.date() != canonical.date() or (source_as_utc - canonical).total_seconds() != 18000:
                raise EvidenciaNoValida("El delta temporal ya no es exactamente +5h en el mismo día UTC")
            if match["source_api_football_id"] is None:
                raise EvidenciaNoValida("El registro con hora necesita ID de fixture API-Football")
        else:
            raise EvidenciaNoValida("Precisión temporal HF desconocida")
        def normalize(value: str) -> str:
            decomposed = unicodedata.normalize("NFKD", value)
            return " ".join("".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold().split())
        competition_aliases = {ctx["competition_name"], ctx["competition_short"]}
        if normalize(str(match["source_league_catalogue_name"])) not in {normalize(str(alias)) for alias in competition_aliases if alias}:
            raise EvidenciaNoValida("El nombre de competición fuente no coincide con el catálogo canónico")
        for name_key, catalogue_key, db_keys in (
            ("source_home_name", "source_home_team_catalogue_name", ("home_name", "home_short", "home_common")),
            ("source_away_name", "source_away_team_catalogue_name", ("away_name", "away_short", "away_common")),
        ):
            provider_name = normalize(str(match[name_key]))
            catalogue_name = normalize(str(match[catalogue_key]))
            aliases = {normalize(str(ctx[key])) for key in db_keys if ctx.get(key)}
            if provider_name != catalogue_name or provider_name not in aliases:
                raise EvidenciaNoValida("El nombre literal de equipo proveedor no coincide con alias canónico")


def _read_source_constraints(conn: Any) -> dict[str, str]:
    return {
        row["relname"]: row["definition"]
        for row in conn.execute(
            """SELECT c.relname, pg_get_constraintdef(k.oid) AS definition
               FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
               JOIN pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='public'
                 AND c.relname IN ('vinculos_multifuente_partidos_futbol', 'observaciones_multifuente_estadisticas_futbol')
                 AND k.contype='c'
                 AND k.conname IN ('vinculos_multifuente_partidos_futbol_fuente_check',
                                   'observaciones_multifuente_estadisticas_futbol_fuente_check')"""
        ).fetchall()
    }


def _migration_needed(constraints: dict[str, str]) -> bool:
    expected_tables = {"vinculos_multifuente_partidos_futbol", "observaciones_multifuente_estadisticas_futbol"}
    if set(constraints) != expected_tables:
        raise EvidenciaNoValida("No se encontraron ambas restricciones de fuente multifuente")
    for definition in constraints.values():
        known = {"PITCHAPI", "ESPN_SOCCER", "SOFASCORE", "THESTATSAPI", "DATAHUB_FOOTBALL_DATA", "KAGGLE_GOKHANERGUL"}
        observed = set(re.findall(r"'([A-Z0-9_]+)'", definition))
        if observed not in (known, known | {FUENTE}):
            raise EvidenciaNoValida("La allowlist SQL de fuentes contiene cambios no previstos")
    return any(FUENTE not in definition for definition in constraints.values())


def _apply_migration(conn: Any) -> None:
    allowlist = "'PITCHAPI', 'ESPN_SOCCER', 'SOFASCORE', 'THESTATSAPI', 'DATAHUB_FOOTBALL_DATA', 'KAGGLE_GOKHANERGUL', 'HF_EATPIZZANOT'"
    conn.execute(
        f"ALTER TABLE vinculos_multifuente_partidos_futbol DROP CONSTRAINT vinculos_multifuente_partidos_futbol_fuente_check, ADD CONSTRAINT vinculos_multifuente_partidos_futbol_fuente_check CHECK (fuente IN ({allowlist}))"
    )
    conn.execute(
        f"ALTER TABLE observaciones_multifuente_estadisticas_futbol DROP CONSTRAINT observaciones_multifuente_estadisticas_futbol_fuente_check, ADD CONSTRAINT observaciones_multifuente_estadisticas_futbol_fuente_check CHECK (fuente IN ({allowlist}))"
    )


def _merge_plans(report: dict[str, Any], rows: dict[str, dict[str, Any]], evidences: dict[str, tuple[EvidenciaCampo, ...]]) -> dict[str, Any]:
    plans = {}
    for match in report["matches"]:
        match_id = match["canonical_id"]
        values = {field: rows[match_id][field] for field in CAMPOS}
        plan = construir_plan_resolucion(values, evidences[match_id])
        if dict(plan.actualizaciones) != match["updates"] or plan.conflictos:
            raise EvidenciaNoValida("El merge NULL-only no reproduce el lote de valores declarados")
        if plan.preservados:
            raise EvidenciaNoValida("El preflight cambió: hay observaciones ya existentes")
        plans[match_id] = plan.actualizaciones
    return plans


def _links_existing(conn: Any, report: dict[str, Any]) -> list[dict[str, Any]]:
    ids = [m["source_event_id"] for m in report["matches"]]
    rows = conn.execute(
        "SELECT fuente,id_evento_fuente,partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=ANY(%s)",
        (FUENTE, ids),
    ).fetchall()
    return [dict(row) for row in rows]


def _observation_existing(conn: Any, report: dict[str, Any]) -> list[dict[str, Any]]:
    ids = [m["source_event_id"] for m in report["matches"]]
    rows = conn.execute(
        "SELECT fuente,id_evento_fuente,partido_id::text,campo,valor::text FROM observaciones_multifuente_estadisticas_futbol WHERE fuente=%s AND id_evento_fuente=ANY(%s)",
        (FUENTE, ids),
    ).fetchall()
    return [dict(row) for row in rows]


def _gap_count(conn: Any) -> int:
    return conn.execute(
        """SELECT count(*) AS gap_count FROM partidos_futbol WHERE estado='FINALIZADO'
           AND local_goles_total IS NOT NULL AND visitante_goles_total IS NOT NULL
           AND (local_corners_total IS NULL OR visitante_corners_total IS NULL
             OR local_disparos_total IS NULL OR visitante_disparos_total IS NULL
             OR local_disparos_arco IS NULL OR visitante_disparos_arco IS NULL)"""
    ).fetchone()["gap_count"]


def _snapshot_database(conn: Any, report: dict[str, Any], evidences: dict[str, tuple[EvidenciaCampo, ...]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    ids = [m["canonical_id"] for m in report["matches"]]
    rows = _query_rows(conn, ids)
    context = _query_identity_context(conn, ids)
    _identity_context_valid(report, rows, context)
    if any(any(rows[m["canonical_id"]][field] is not None for field in CAMPOS) for m in report["matches"]):
        raise EvidenciaNoValida("Un campo objetivo ya no es NULL; no se altera ni se replanifica este lote")
    if _links_existing(conn, report) or _observation_existing(conn, report):
        raise EvidenciaNoValida("Ya existe procedencia HF para este lote; no se duplica")
    plans = _merge_plans(report, rows, evidences)
    return rows, context, {
        "migration_needed": _migration_needed(_read_source_constraints(conn)),
        "gap_matches_before": _gap_count(conn),
        "updates_by_match": plans,
    }


def _write_backup(backup_dir: Path, report: dict[str, Any], row_snapshot: dict[str, dict[str, Any]], context: dict[str, dict[str, Any]], metadata: dict[str, Any], hashes: dict[str, str], report_path: Path) -> dict[str, Any]:
    backup_dir = backup_dir.expanduser().absolute()
    repo = RAIZ_REPO.resolve()
    if repo == backup_dir or repo in backup_dir.parents:
        raise ValueError("El backup debe quedar fuera del repositorio del producto")
    backup_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    os.chmod(backup_dir, 0o700)
    payload = {
        "status": "PRIVATE_PREAPPLY_BACKUP_HF_EATPIZZANOT",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_revision": REVISION,
        "candidate_report_sha256": _sha(report_path),
        "source_hashes": hashes,
        "canonical_rows": row_snapshot,
        "identity_context": context,
        "existing_links_for_source_events": [],
        "existing_observations_for_source_events": [],
        "metadata": metadata,
        "planned_mutations": [
            {"match_id": m["canonical_id"], "event_id": m["source_event_id"], "updates": m["updates"]}
            for m in report["matches"]
        ],
        "attribution": ATRIBUCION,
    }
    path = backup_dir / "backup_preaplicacion.json"
    _json_dump(path, payload)
    return {"directory": str(backup_dir), "file": str(path), "sha256": _sha(path), "mode": oct(path.stat().st_mode & 0o777)}


def _write_link_evidence(conn: Any, match: dict[str, Any], evidences: tuple[EvidenciaCampo, ...]) -> None:
    match_id = match["canonical_id"]
    event_id = match["source_event_id"]
    conn.execute(
        "INSERT INTO vinculos_multifuente_partidos_futbol(fuente,id_evento_fuente,partido_id) VALUES (%s,%s,%s)",
        (FUENTE, event_id, match_id),
    )
    common_identity = {
        "source_dataset": report_dataset_marker(),
        "source_url": URL_DATASET,
        "repository_url": URL_REPOSITORIO,
        "dataset_owner": "eatpizzanot",
        "declared_license": "CC-BY-4.0",
        "attribution": ATRIBUCION,
        "rights_caveat": "El card del dataset indica que la licencia declarada puede no extender derechos sobre todo el contenido upstream.",
        "declared_upstreams": ["API-Football", "football-data.co.uk"],
        "dataset_revision": REVISION,
        "source_files_sha256": match["source_files_sha256"],
        "source_row_sha256": match["source_row_sha256"],
        "source_fixture_id": match["source_fixture_id"],
        "source_api_football_id": match["source_api_football_id"],
        "source_competition_id": match["source_competition_id"],
        "source_league_api_football_id": match["source_league_api_football_id"],
        "source_team_ids": {
            "home_dataset_id": match["raw_source_payload"]["home_team_id"],
            "home_api_football_id": match["source_home_team_api_football_id"],
            "away_dataset_id": match["raw_source_payload"]["away_team_id"],
            "away_api_football_id": match["source_away_team_api_football_id"],
        },
        "identity_method": match["identity_method"],
        "competition_code": match["competition_code"],
        "source_names": {"home": match["source_home_name"], "away": match["source_away_name"]},
        "canonical_names": {"home": match["canonical_home_name"], "away": match["canonical_away_name"]},
        "source_timestamp_precision": match["source_timestamp_precision"],
        "source_date_utc_naive": match["source_date_utc_naive"],
        "source_status": match["source_status"],
        "source_ft": match["source_ft"],
        "raw_source_payload": match["raw_source_payload"],
        "quality_policy": "Source zeros excluded; non-null canonical values preserved; shot totals/target must be internally consistent.",
    }
    for evidence in evidences:
        conn.execute(
            """INSERT INTO observaciones_multifuente_estadisticas_futbol
               (fuente,id_evento_fuente,partido_id,campo,valor,clave_proveedor,periodo_proveedor,
                sha256_payload,contrato,evidencia_identidad,observado_en)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (FUENTE, event_id, match_id, evidence.campo, evidence.valor, evidence.clave_proveedor,
             "All", evidence.sha256_payload, CONTRATO, Jsonb({**common_identity, "source_field": evidence.clave_proveedor}),
             evidence.observado_en),
        )


def report_dataset_marker() -> str:
    return "Global Football (Soccer) Data Lake"


def _apply_batch(conn: Any, report: dict[str, Any], evidences: dict[str, tuple[EvidenciaCampo, ...]], before: dict[str, dict[str, Any]], migration_needed: bool) -> dict[str, Any]:
    if migration_needed:
        _apply_migration(conn)
    total_fields = 0
    for match in report["matches"]:
        match_id = match["canonical_id"]
        values = dict(match["updates"])
        if set(values) - CAMPOS:
            raise EvidenciaNoValida("Intento de modificar campos fuera de las seis estadísticas")
        assign = sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(k)) for k in values)
        null_guards = sql.SQL(" AND ").join(sql.SQL("{} IS NULL").format(sql.Identifier(k)) for k in values)
        updated = conn.execute(
            sql.SQL("UPDATE partidos_futbol SET {} WHERE id=%s AND estado='FINALIZADO' AND local_goles_total=%s AND visitante_goles_total=%s AND {} RETURNING id").format(assign, null_guards),
            (*values.values(), match_id, match["source_ft"][0], match["source_ft"][1]),
        ).fetchone()
        if updated is None:
            raise EvidenciaNoValida("UPDATE NULL-only perdió su guarda de estado/FT")
        _write_link_evidence(conn, match, evidences[match_id])
        total_fields += len(values)
    return {"matches": len(report["matches"]), "fields_written": total_fields, "links_written": len(report["matches"]), "observations_written": total_fields, "migration_applied": migration_needed}


def _postflight(conn: Any, report: dict[str, Any], before: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ids = [m["canonical_id"] for m in report["matches"]]
    after = _query_rows(conn, ids)
    if set(after) != set(before):
        raise EvidenciaNoValida("Postflight no recuperó las cuatro filas canónicas")
    expected_fields = 0
    for match in report["matches"]:
        match_id = match["canonical_id"]
        old, new = before[match_id], after[match_id]
        if (new["competicion_id"], new["equipo_local_id"], new["equipo_visitante_id"], new["fecha_partido"], new["estado"], new["local_goles_total"], new["visitante_goles_total"], new["fuente_datos"]) != (old["competicion_id"], old["equipo_local_id"], old["equipo_visitante_id"], old["fecha_partido"], old["estado"], old["local_goles_total"], old["visitante_goles_total"], old["fuente_datos"]):
            raise EvidenciaNoValida("Postflight encontró alteración de identidad o FT")
        for field, value in match["updates"].items():
            if new[field] != value:
                raise EvidenciaNoValida("Postflight no reproduce una estadística aplicada")
        if new["datos_completos"] != (new["local_goles_total"] is not None and new["visitante_goles_total"] is not None):
            raise EvidenciaNoValida("El trigger canónico dejó datos_completos inconsistente")
        if new["datos_corners_completos"] != all(new[k] is not None for k in ("local_corners_1t", "visitante_corners_1t", "local_corners_2t", "visitante_corners_2t")):
            raise EvidenciaNoValida("Flag canónico de corners no concilia con períodos")
        if new["datos_disparos_completos"] != all(new[k] is not None for k in ("local_disparos_total", "visitante_disparos_total", "local_disparos_arco", "visitante_disparos_arco")):
            raise EvidenciaNoValida("Flag canónico de disparos no concilia con columnas")
        for field in COLUMNAS:
            if field in match["updates"] or field in {"actualizado_en", "datos_completos", "datos_corners_completos", "datos_disparos_completos"}:
                continue
            if new[field] != old[field]:
                raise EvidenciaNoValida(f"Postflight detectó un cambio fuera de alcance: {field}")
        expected_fields += len(match["updates"])
    links = conn.execute("SELECT fuente,id_evento_fuente,partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=ANY(%s)", (FUENTE, [m["source_event_id"] for m in report["matches"]])).fetchall()
    expected_links = {(FUENTE, m["source_event_id"], m["canonical_id"]) for m in report["matches"]}
    if {(r["fuente"], r["id_evento_fuente"], r["partido_id"]) for r in links} != expected_links:
        raise EvidenciaNoValida("Postflight no recuperó los cuatro vínculos de fuente")
    observations = conn.execute("SELECT id_evento_fuente,partido_id::text,campo,valor::text,clave_proveedor,sha256_payload,contrato FROM observaciones_multifuente_estadisticas_futbol WHERE fuente=%s AND id_evento_fuente=ANY(%s)", (FUENTE, [m["source_event_id"] for m in report["matches"]])).fetchall()
    expected_obs = {(m["source_event_id"],m["canonical_id"],field,str(value), next(e.clave_proveedor for e in _evidencia_reporte(report)[m["canonical_id"]] if e.campo==field), m["source_row_sha256"], CONTRATO) for m in report["matches"] for field,value in m["updates"].items()}
    observed_obs = {(r["id_evento_fuente"],r["partido_id"],r["campo"],r["valor"],r["clave_proveedor"],r["sha256_payload"],r["contrato"]) for r in observations}
    if observed_obs != expected_obs:
        raise EvidenciaNoValida("Postflight de procedencia no reproduce valores/hashes/contrato")
    return {"matches":4,"fields":expected_fields,"links":len(links),"observations":len(observations),"gap_matches_remaining":_gap_count(conn)}


def ejecutar(evidence_dir: Path, *, apply: bool, rehearse_rollback: bool, backup_dir: Path | None, output: Path | None = None) -> dict[str, Any]:
    if apply and rehearse_rollback:
        raise ValueError("--apply y --rehearse-rollback son excluyentes")
    report, report_path, hashes = _leer_reporte(evidence_dir)
    evidences = _evidencia_reporte(report)
    load_dotenv(RAIZ_REPO / "backend/.env", override=False)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no está disponible en el mecanismo protegido")
    ids = [m["canonical_id"] for m in report["matches"]]
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as read_conn:
        read_conn.read_only = True
        with read_conn.transaction():
            read_conn.execute("SET TRANSACTION READ ONLY")
            read_conn.execute("SET LOCAL statement_timeout='45s'")
            before, context, metadata = _snapshot_database(read_conn, report, evidences)
            constraints = _read_source_constraints(read_conn)
            migration_needed = _migration_needed(constraints)
            preflight = {
                "status":"READ_ONLY_PREFLIGHT_OK","database_read_only":True,
                "matches":4,"positive_observations":19,"null_only_updates":19,
                "source_links_already_present":0,"source_observations_already_present":0,
                "migration_needed":migration_needed,"source_constraint_definitions":constraints,
                "gap_matches_before":metadata["gap_matches_before"],
                "source_hashes":hashes,"candidate_report_sha256":_sha(report_path),
                "targets":[{"match_id":m["canonical_id"],"competition":m["competition_code"],"home":m["canonical_home_name"],"away":m["canonical_away_name"],"date":m["canonical_local_date"],"ft":m["canonical_ft"],"updates":m["updates"]} for m in report["matches"]],
                "database_changes":False,
            }
    if not apply and not rehearse_rollback:
        result = preflight
        if output:
            _json_dump(output.expanduser().absolute(), result)
        return result
    if backup_dir is None:
        raise ValueError("--apply y --rehearse-rollback requieren --backup-dir privado nuevo")
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as backup_conn:
        backup_conn.read_only = True
        with backup_conn.transaction():
            backup_conn.execute("SET TRANSACTION READ ONLY")
            backup_conn.execute("SET LOCAL statement_timeout='45s'")
            backup_rows, backup_context, backup_meta = _snapshot_database(backup_conn, report, evidences)
            if json.dumps(_json_value(backup_rows), sort_keys=True) != json.dumps(_json_value(before), sort_keys=True):
                raise EvidenciaNoValida("El estado cambió entre preflight y backup")
            backup_info = _write_backup(backup_dir, report, backup_rows, backup_context, {**backup_meta, "source_constraints": constraints}, hashes, report_path)
    if rehearse_rollback:
        rehearsal_result = None
        with connect(database_url, connect_timeout=12, row_factory=dict_row) as write_conn:
            try:
                with write_conn.transaction():
                    write_conn.execute("SET LOCAL lock_timeout='5s'")
                    write_conn.execute("SET LOCAL statement_timeout='60s'")
                    locked = _query_rows(write_conn, ids, for_update=True)
                    if json.dumps(_json_value(locked), sort_keys=True) != json.dumps(_json_value(before), sort_keys=True):
                        raise EvidenciaNoValida("El estado cambió antes del ensayo de rollback")
                    _identity_context_valid(report, locked, _query_identity_context(write_conn, ids))
                    current_constraints = _read_source_constraints(write_conn)
                    needed = _migration_needed(current_constraints)
                    applied = _apply_batch(write_conn, report, evidences, locked, needed)
                    rehearsal_result = _postflight(write_conn, report, locked)
                    raise _RollbackRequested({"transactional_apply":applied,"transactional_postflight":rehearsal_result})
            except _RollbackRequested:
                pass
        with connect(database_url, connect_timeout=12, row_factory=dict_row) as verify_conn:
            verify_conn.read_only = True
            with verify_conn.transaction():
                verify_conn.execute("SET TRANSACTION READ ONLY")
                verify_conn.execute("SET LOCAL statement_timeout='45s'")
                after = _query_rows(verify_conn, ids)
                if json.dumps(_json_value(after), sort_keys=True) != json.dumps(_json_value(before), sort_keys=True):
                    raise EvidenciaNoValida("El ensayo de rollback dejó cambios canónicos")
                if _links_existing(verify_conn, report) or _observation_existing(verify_conn, report):
                    raise EvidenciaNoValida("El ensayo de rollback dejó procedencia persistida")
                post_censo = _gap_count(verify_conn)
                final_constraints = _read_source_constraints(verify_conn)
        result = {**preflight,"status":"ROLLBACK_REHEARSAL_VERIFIED","database_changes":False,"backup":backup_info,"rehearsal":rehearsal_result,"rollback_verified":True,"gap_matches_after_rollback":post_censo,"constraints_after_rollback":final_constraints}
        _json_dump(Path(backup_info["directory"]) / "ensayo_rollback.json", result)
        return result

    with connect(database_url, connect_timeout=12, row_factory=dict_row) as write_conn:
        with write_conn.transaction():
            write_conn.execute("SET LOCAL lock_timeout='5s'")
            write_conn.execute("SET LOCAL statement_timeout='60s'")
            locked = _query_rows(write_conn, ids, for_update=True)
            if json.dumps(_json_value(locked), sort_keys=True) != json.dumps(_json_value(before), sort_keys=True):
                raise EvidenciaNoValida("El lote cambió después del backup; aplicación abortada")
            _identity_context_valid(report, locked, _query_identity_context(write_conn, ids))
            current_constraints = _read_source_constraints(write_conn)
            needed = _migration_needed(current_constraints)
            if needed != migration_needed:
                raise EvidenciaNoValida("Cambió el estado de la migración desde el preflight")
            applied = _apply_batch(write_conn, report, evidences, locked, needed)
            postflight_tx = _postflight(write_conn, report, locked)
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as post_conn:
        post_conn.read_only = True
        with post_conn.transaction():
            post_conn.execute("SET TRANSACTION READ ONLY")
            post_conn.execute("SET LOCAL statement_timeout='45s'")
            postflight_independent = _postflight(post_conn, report, before)
            constraints_after = _read_source_constraints(post_conn)
    result = {**preflight,"status":"APPLIED_AND_INDEPENDENTLY_VERIFIED","database_read_only":False,"database_changes":True,"applied":applied,"transaction_postflight":postflight_tx,"independent_read_only_postflight":postflight_independent,"source_constraints_after":constraints_after,"backup":backup_info,"attribution":ATRIBUCION}
    _json_dump(Path(backup_info["directory"]) / "resultado_aplicacion.json", result)
    return result


class _RollbackRequested(Exception):
    def __init__(self, result: dict[str, Any]):
        super().__init__("Rollback rehearsal requested")
        self.result = result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Aplica el lote validado con backup/DDL/procedencia/postflight")
    parser.add_argument("--rehearse-rollback", action="store_true", help="Ejecuta DDL/DML y postflight dentro de una transacción que revierte")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--output", type=Path, help="Guarda resumen privado nuevo; no sobrescribe")
    args = parser.parse_args()
    try:
        result = ejecutar(args.evidence_dir, apply=args.apply, rehearse_rollback=args.rehearse_rollback, backup_dir=args.backup_dir, output=args.output)
    except Exception as exc:
        print(json.dumps({"ok":False,"error_type":type(exc).__name__,"sqlstate":getattr(getattr(exc,"diag",None),"sqlstate",None)},sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
