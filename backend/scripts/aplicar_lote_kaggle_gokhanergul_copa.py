"""Aplica únicamente stats NULL de Coupe de France con evidencia Kaggle MIT.

Modo predeterminado: preflight READ ONLY. El lote requiere un reporte de
identidad explícita, el ZIP fuente intacto y un backup privado nuevo para
``--apply``. La fecha de Kaggle se interpreta como fecha local de calendario;
no se fabrica zona horaria ni se altera la fecha canónica.

Ejemplo:
  python -m scripts.aplicar_lote_kaggle_gokhanergul_copa \
    --evidence-dir /ruta/privada/KAGGLE_GOKHANERGUL
  python -m scripts.aplicar_lote_kaggle_gokhanergul_copa \
    --evidence-dir /ruta/privada/KAGGLE_GOKHANERGUL --apply \
    --backup-dir /ruta/privada/backup_kaggle_copa_YYYYMMDD
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata
from collections import Counter
from datetime import date, datetime, timezone
from typing import Any
from zipfile import ZipFile

from dotenv import load_dotenv
from psycopg import connect, sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from servicios.resolucion_multifuente_futbol import (
    CAMPOS_RECUPERABLES,
    EvidenciaCampo,
    EvidenciaNoValida,
    construir_plan_resolucion,
    extraer_evidencia_kaggle_gokhanergul_csv,
    sha256_json,
)


RAIZ_REPO = Path(__file__).resolve().parents[2]
MIGRACION = RAIZ_REPO / "backend/migrations/2026-10-20_fuente_kaggle_gokhanergul.sql"
REPORTE = "readonly_kaggle_stats_explicit_crosswalk_audit.json"
ARCHIVO_ZIP = "football-match-statistics.zip"
FUENTE = "KAGGLE_GOKHANERGUL"
URL_DATASET = "https://www.kaggle.com/datasets/gokhanergul/football-match-statistics"
LICENCIA = "MIT"
COMPETICIONES = {
    ("England", "Fa-cup"): "ENG_FACUP",
    ("France", "Coupe-de-france"): "FRA_COUPE",
    ("Italy", "Coppa-italia"): "ITA_COPPA",
}
ESTADISTICAS = {
    "local_corners_total": "Corner_Kicks_Home",
    "visitante_corners_total": "Corner_Kicks_Host",
    "local_disparos_total": "Goal_Attempts_Home",
    "visitante_disparos_total": "Goal_Attempts_Host",
    "local_disparos_arco": "Shots_on_Goal_Home",
    "visitante_disparos_arco": "Shots_on_Goal_Host",
}
TRIGGER_DERIVADOS = {
    "actualizado_en", "datos_completos", "datos_corners_completos",
    "datos_disparos_completos", "diferencia_goles", "resultado_final",
    "ganador_id", "local_goles_total", "visitante_goles_total",
}
COLUMNAS = (
    "id", "competicion_id", "temporada_id", "equipo_local_id", "equipo_visitante_id",
    "fecha_partido", "fecha_partido_local", "estado", "valido", "fuente_datos",
    "local_goles_1t", "local_goles_2t", "local_goles_et", "local_goles_total",
    "visitante_goles_1t", "visitante_goles_2t", "visitante_goles_et", "visitante_goles_total",
    "local_penales", "visitante_penales", "hubo_penales", "hubo_tiempo_extra",
    *sorted(CAMPOS_RECUPERABLES), "datos_completos", "datos_corners_completos",
    "datos_disparos_completos", "ganador_id", "resultado_final", "diferencia_goles",
    "actualizado_en",
)
# Pares concretos revisados como alias equivalentes. No hay edit-distance ni
# resolución difusa; cada alias debe llevar al alias canónico de ese equipo.
ALIAS_EQUIPO = {
    "acajaccio": "ajaccio",
    "zouasia": "jumeauxmzouazia",
    "andrezieux": "andrezieuxboutheonfc",
    "athleticom": "athleticomarseille",
    "angoulemecfc": "angoulemecharentefc",
    "stetienne": "saintetienne",
    "asmbelfort": "belfort",
    "gonfreville": "ententesportivemunicipalegonfreville",
    "saintpierroise": "jssaintpierroise",
    "iccroix": "croixiriscf",
    "noisylegrand": "noisylegrandfc",
    "saintpryve": "stpryvesthilairefc",
    "pontivy": "pontivygsi",
    "bourges": "bourgesfoot18",
}


def _normalizar(texto: Any) -> str:
    descompuesto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(ch.lower() for ch in descompuesto if ch.isalnum())


def _fecha_local_dataset(date_day: str, season: str) -> str:
    """Reconstruye la fecha calendario del CSV sin asignarle zona horaria."""
    match = re.fullmatch(r"([0-9]{4})/([0-9]{4})", season)
    day_month = re.fullmatch(r"([0-9]{1,2})\.([0-9]{1,2})", date_day)
    if not match or not day_month:
        raise EvidenciaNoValida("Temporada o fecha local Kaggle con formato inesperado")
    start_year, end_year = map(int, match.groups())
    if end_year != start_year + 1:
        raise EvidenciaNoValida("Temporada Kaggle no es un intervalo consecutivo")
    day, month = map(int, day_month.groups())
    year = start_year if month >= 7 else end_year
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        raise EvidenciaNoValida("Fecha local Kaggle inválida") from None


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode()


def _sha_archivo(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for bloque in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _guardar_nuevo(path: Path, contenido: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
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


def _leer_reporte(
    evidence_dir: Path,
    report_name: str = REPORTE,
) -> tuple[list[dict[str, Any]], dict[str, Any], Path, Path]:
    evidence_dir = evidence_dir.expanduser().resolve()
    if evidence_dir == RAIZ_REPO or RAIZ_REPO in evidence_dir.parents:
        raise ValueError("La evidencia debe permanecer fuera del repositorio")
    if Path(report_name).name != report_name or not report_name.endswith(".json"):
        raise ValueError("El reporte debe ser un archivo JSON dentro del directorio de evidencia")
    report_path = evidence_dir / report_name
    archive_path = evidence_dir / ARCHIVO_ZIP
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        report.get("status") != "READ_ONLY_KAGGLE_STATS_EXPLICIT_CROSSWALK_AUDIT"
        or report.get("database_read_only") is not True
        or report.get("ddl_or_dml_performed") is not False
        or report.get("license") != "MIT (Kaggle dataset metadata)"
        or report.get("source_archive_sha256") != _sha_archivo(archive_path)
        or report.get("invalid_stats") != 0
    ):
        raise EvidenciaNoValida("Reporte/hash Kaggle no corresponde al lote revisado")
    try:
        observed_at = datetime.fromisoformat(str(report.get("audited_at_utc")))
    except ValueError:
        raise EvidenciaNoValida("Timestamp de observación del reporte no es ISO") from None
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise EvidenciaNoValida("Timestamp de observación del reporte debe tener zona horaria")
    games = report.get("matched")
    if (not isinstance(games, list) or not games
            or report.get("matches_with_stats_strict_or_manual_alias") != len(games)
            or report.get("stat_observations") != len(games) * 6
            or sum(int(report.get(key, -1)) for key in (
                "values_null_available", "values_equal_nonnull", "values_conflicting_nonnull"
            )) != report.get("stat_observations")
            or any(not isinstance(report.get(key), int) or report[key] < 0 for key in (
                "values_null_available", "values_equal_nonnull", "values_conflicting_nonnull"
            ))):
        raise EvidenciaNoValida("Conteos del lote Kaggle no concilian con sus partidos/campos")
    match_ids = [str(game.get("match_id") or "") for game in games]
    event_ids = [str(game.get("source", {}).get("event_id") or "") for game in games]
    if len(set(match_ids)) != len(games) or len(set(event_ids)) != len(games):
        raise EvidenciaNoValida("Partidos o eventos Kaggle duplicados en el lote")

    source_rows: dict[int, dict[str, str]] = {}
    with ZipFile(archive_path) as archive:
        if archive.namelist() != ["Football.csv"]:
            raise EvidenciaNoValida("Estructura ZIP Kaggle distinta a la auditoría")
        target_lines = {int(game["source"]["line"]) for game in games}
        with archive.open("Football.csv") as raw, __import__("io").TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
            for line_number, row in enumerate(csv.DictReader(stream), start=2):
                if line_number in target_lines:
                    source_rows[line_number] = dict(row)
    if len(source_rows) != len(games):
        raise EvidenciaNoValida("No se recuperaron todas las filas fuente exactas del ZIP")

    for game in games:
        source = game["source"]
        line_number = int(source["line"])
        raw_row = source_rows[line_number]
        if sha256_json(raw_row) != source.get("row_sha256"):
            raise EvidenciaNoValida("Hash de fila Kaggle distinto al crosswalk auditado")
        if (game.get("competition") != "FRA_COUPE"
                or COMPETICIONES.get((raw_row.get("Country"), raw_row.get("League"))) != game.get("competition")):
            raise EvidenciaNoValida("La competición de la fila Kaggle cambió")
        if (
            raw_row.get("home_team") != source.get("home")
            or raw_row.get("away_team") != source.get("away")
            or raw_row.get("season_year") != source.get("season")
            or raw_row.get("Date_day") != source.get("date_day")
            or int(raw_row.get("home_score", -1)) != int(source["ft"][0])
            or int(raw_row.get("away_score", -1)) != int(source["ft"][1])
        ):
            raise EvidenciaNoValida("Campos identidad Kaggle no reproducen el crosswalk")
        expected_local_date = _fecha_local_dataset(str(source["date_day"]), str(source["season"]))
        if expected_local_date != source.get("local_date_inferred") or expected_local_date != game.get("date_local"):
            raise EvidenciaNoValida("Fecha local del dataset no se deriva de fecha y temporada")
        expected_event_id = (
            f"KAGGLE_GOKHANERGUL/{game['competition']}/{source['season']}/"
            f"{source['row_sha256'][:24]}"
        )
        if source.get("event_id") != expected_event_id:
            raise EvidenciaNoValida("ID sintético no reproduce competición, temporada y hash de fila")
        for side in ("home", "away"):
            alias = game.get("manual_aliases", {}).get(side)
            if alias is None:
                continue
            source_name = _normalizar(alias.get("provider_name"))
            if (alias.get("method") != "EXPLICIT_ALIAS_MAP"
                    or ALIAS_EQUIPO.get(source_name) != _normalizar(alias.get("canonical_team_name"))):
                raise EvidenciaNoValida("Alias Kaggle no está en la lista explícita aprobada")
        if any(_normalizar(alias.get("provider_name")) == "zouasia"
               for alias in game.get("manual_aliases", {}).values()):
            urls = set(game.get("identity_corroboration_urls", []))
            if urls != {
                "https://epreuves.fff.fr/competition/club/538259-jumeaux-de-m-zoisia/equipe/202118898SEM1/resultats-et-calendrier.html",
                "https://www.girondins.com/fr/match/33212/composition",
            }:
                raise EvidenciaNoValida("Alias Zouasia requiere las dos referencias oficiales revisadas")
        game["_raw_row"] = raw_row
    return games, report, archive_path, report_path


def _leer_estado(conn: Any, ids: list[str], *, for_update: bool = False) -> dict[str, dict[str, Any]]:
    suffix = sql.SQL(" FOR UPDATE") if for_update else sql.SQL("")
    query = sql.SQL("SELECT {} FROM partidos_futbol WHERE id=ANY(%s::uuid[]) ORDER BY id{}").format(
        sql.SQL(",").join(sql.Identifier(field) for field in COLUMNAS), suffix
    )
    return {str(row["id"]): dict(row) for row in conn.execute(query, (ids,)).fetchall()}


def _leer_contexto(conn: Any, ids: list[str]) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """SELECT p.id::text AS id,c.codigo AS competition_code,p.competicion_id::text AS competition_id,
                  p.fecha_partido_local::date::text AS local_date,p.estado::text AS state,p.fuente_datos,
                  p.local_goles_total,p.visitante_goles_total,p.equipo_local_id::text AS home_id,
                  p.equipo_visitante_id::text AS away_id,
                  el.nombre AS home_name,el.nombre_corto AS home_short,el.nombre_comun AS home_common,el.abreviatura AS home_abbr,
                  ev.nombre AS away_name,ev.nombre_corto AS away_short,ev.nombre_comun AS away_common,ev.abreviatura AS away_abbr
           FROM partidos_futbol p JOIN competiciones_futbol c ON c.id=p.competicion_id
           JOIN equipos_futbol el ON el.id=p.equipo_local_id JOIN equipos_futbol ev ON ev.id=p.equipo_visitante_id
           WHERE p.id=ANY(%s::uuid[])""",
        (ids,),
    ).fetchall()
    return {str(row["id"]): dict(row) for row in rows}


def _serializar(rows: dict[str, dict[str, Any]]) -> str:
    return json.dumps(
        {key: {name: value.isoformat() if hasattr(value, "isoformat") else str(value) if value is not None else None
               for name, value in row.items()} for key, row in sorted(rows.items())},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )


def _crear_planes(
    conn: Any,
    games: list[dict[str, Any]],
    current: dict[str, dict[str, Any]],
    archive_hash: str,
    observed_at: datetime,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ids = [str(game["match_id"]) for game in games]
    context = _leer_contexto(conn, ids)
    if len(context) != len(games) or set(context) != set(ids):
        raise EvidenciaNoValida("El conjunto de partidos no concilia con el catálogo actual")
    evidence_by_match: dict[str, list[EvidenciaCampo]] = {}
    identity_by_match: dict[str, dict[str, Any]] = {}
    plans: dict[str, Any] = {}
    seen_source_ids: set[str] = set()
    for game in games:
        match_id = str(game["match_id"])
        row = current[match_id]
        ctx = context[match_id]
        source = game["source"]
        if (
            row["estado"] != "FINALIZADO"
            or row["valido"] is not True
            or ctx["state"] != "FINALIZADO"
            or ctx["competition_code"] != game["competition"]
            or ctx["local_date"] != game["date_local"]
            or [ctx["local_goles_total"], ctx["visitante_goles_total"]] != [int(x) for x in game["ft"]]
            or game["canonical_source"] != row["fuente_datos"]
            or any(row.get(field) != game.get("current_nonnull", {}).get(field) for field in game.get("current_nonnull", {}))
        ):
            raise EvidenciaNoValida("Identidad, fecha local, FT u origen canónico cambió desde el preflight")
        current_nonnull = {
            field: int(row[field]) for field in ESTADISTICAS if row[field] is not None
        }
        expected_nonnull = {
            field: int(value) for field, value in game.get("current_nonnull", {}).items()
        }
        if current_nonnull != expected_nonnull:
            raise EvidenciaNoValida("Los campos no nulos actuales no reproducen el crosswalk auditado")

        home_aliases = {ctx[key] for key in ("home_name", "home_short", "home_common", "home_abbr") if ctx[key]}
        away_aliases = {ctx[key] for key in ("away_name", "away_short", "away_common", "away_abbr") if ctx[key]}
        home_source, away_source = str(source["home"]), str(source["away"])
        def _alias_ok(
            source_name: str,
            aliases: set[str],
            detail: dict[str, Any] | None,
            expected_team_id: str,
        ) -> bool:
            if _normalizar(source_name) in {_normalizar(alias) for alias in aliases}:
                return detail is None
            if detail is None or _normalizar(detail.get("provider_name")) != _normalizar(source_name):
                return False
            return (
                detail.get("method") == "EXPLICIT_ALIAS_MAP"
                and str(detail.get("canonical_team_id")) == str(expected_team_id)
                and _normalizar(detail.get("canonical_team_name")) in {_normalizar(alias) for alias in aliases}
                and ALIAS_EQUIPO.get(_normalizar(source_name)) == _normalizar(detail.get("canonical_team_name"))
            )
        alias_meta = game.get("manual_aliases", {})
        if not _alias_ok(home_source, home_aliases, alias_meta.get("home"), str(ctx["home_id"])):
            raise EvidenciaNoValida("Nombre local sin identidad exacta o alias explícito aceptado")
        if not _alias_ok(away_source, away_aliases, alias_meta.get("away"), str(ctx["away_id"])):
            raise EvidenciaNoValida("Nombre visitante sin identidad exacta o alias explícito aceptado")
        if row["fuente_datos"] != game["canonical_source"]:
            raise EvidenciaNoValida("Origen canónico cambió")
        unique = conn.execute(
            """SELECT count(*) AS n FROM partidos_futbol p WHERE p.valido IS TRUE AND p.estado='FINALIZADO'
                 AND p.competicion_id=%s AND p.fecha_partido_local::date=%s
                 AND p.equipo_local_id=%s AND p.equipo_visitante_id=%s
                 AND p.local_goles_total=%s AND p.visitante_goles_total=%s""",
            (ctx["competition_id"], game["date_local"], ctx["home_id"], ctx["away_id"], int(game["ft"][0]), int(game["ft"][1])),
        ).fetchone()
        if unique["n"] != 1:
            raise EvidenciaNoValida("Identidad por competición/fecha/equipos/FT no es única")

        event_id = str(source["event_id"])
        if event_id in seen_source_ids or len(event_id) > 128:
            raise EvidenciaNoValida("ID sintético Kaggle duplicado o fuera del contrato")
        seen_source_ids.add(event_id)
        expected = {
            "event_id": event_id,
            "country": source["country"],
            "league": source["league"],
            "season": source["season"],
            "date_day": source["date_day"],
            "date_local": source["local_date_inferred"],
            "home": home_source,
            "away": away_source,
            "ft_home": int(source["ft"][0]),
            "ft_away": int(source["ft"][1]),
        }
        payload = {
            "event_id": event_id,
            "dataset": "gokhanergul/football-match-statistics",
            "dataset_version": 2,
            "license": "MIT",
            "dataset_url": URL_DATASET,
            "source_archive_sha256": archive_hash,
            "source_row_sha256": source["row_sha256"],
            "source_row_number": int(source["line"]),
            "country": source["country"], "league": source["league"],
            "season": source["season"], "date_day": source["date_day"],
            "date_local_inferred": source["local_date_inferred"],
            "home": home_source, "away": away_source,
            "ft_home": int(source["ft"][0]), "ft_away": int(source["ft"][1]),
            "raw_row": game["_raw_row"],
        }
        evidence = extraer_evidencia_kaggle_gokhanergul_csv(
            evento_id=event_id, payload=payload, esperado=expected,
            observado_en=observed_at,
        )
        if len(evidence) != 6:
            raise EvidenciaNoValida("El partido no conserva las seis métricas de equipo")
        recorded = {str(field): int(value) for field, value in game["observations"].items()}
        extracted = {item.campo: int(item.valor) for item in evidence}
        if recorded != extracted:
            raise EvidenciaNoValida("Las seis observaciones no reproducen el reporte auditado")
        identity = {
            "metodo": "KAGGLE_COMPETITION_LOCAL_DATE_TEAM_CROSSWALK_FT_UNIQUE_V1",
            "canonical_competition_id": str(ctx["competition_id"]),
            "provider_competition_id": f"{source['country']}/{source['league']}",
            "canonical_home_team_id": str(ctx["home_id"]),
            "provider_home_team_id": "KAGGLE_NAME/" + _normalizar(home_source),
            "canonical_away_team_id": str(ctx["away_id"]),
            "provider_away_team_id": "KAGGLE_NAME/" + _normalizar(away_source),
            "canonical_local_date": game["date_local"],
            "provider_local_date": game["date_local"],
            "provider_timezone": None,
            "canonical_ft": [int(game["ft"][0]), int(game["ft"][1])],
            "provider_ft": [int(game["ft"][0]), int(game["ft"][1])],
            "identity_rule": "Competition + local calendar date + ordered team names/approved aliases + FT + exactly one valid canonical match",
            "manual_alias_crosswalk": alias_meta,
            "identity_corroboration_urls": list(game.get("identity_corroboration_urls", [])),
            "source_archive_sha256": archive_hash,
            "source_row_sha256": source["row_sha256"],
            "source_row_number": int(source["line"]),
            "dataset_license_declared": "MIT",
            "dataset_version": 2,
        }
        plan = construir_plan_resolucion({field: row.get(field) for field in CAMPOS_RECUPERABLES}, evidence)
        expected_updates = {field: value for field, value in recorded.items() if row.get(field) is None}
        expected_conflicts = {field for field, value in recorded.items() if row.get(field) is not None and row.get(field) != value}
        if plan.actualizaciones != expected_updates or set(plan.conflictos) != expected_conflicts:
            raise EvidenciaNoValida("El merge campo-a-campo no concilia con nulos/evidencia")
        evidence_by_match[match_id] = list(evidence)
        identity_by_match[match_id] = identity
        plans[match_id] = plan
    return plans, {"context": context, "evidence": evidence_by_match, "identity": identity_by_match}


def _leer_restricciones(conn: Any) -> dict[str, str]:
    rows = conn.execute(
        """SELECT conname,pg_get_constraintdef(oid) AS definition FROM pg_constraint
           WHERE conrelid IN ('public.vinculos_multifuente_partidos_futbol'::regclass,
                              'public.observaciones_multifuente_estadisticas_futbol'::regclass)
             AND conname IN ('vinculos_multifuente_partidos_futbol_fuente_check',
                             'observaciones_multifuente_estadisticas_futbol_fuente_check')"""
    ).fetchall()
    return {row["conname"]: row["definition"] for row in rows}


def _migracion_necesaria(conn: Any) -> bool:
    constraints = _leer_restricciones(conn)
    if len(constraints) != 2:
        raise EvidenciaNoValida("No están presentes las dos restricciones de procedencia esperadas")
    return any(FUENTE not in definition for definition in constraints.values())


def _statements_migracion() -> list[str]:
    output = []
    for block in MIGRACION.read_text(encoding="utf-8").split(";"):
        clean = re.sub(r"(?m)^\s*--.*$", "", block).strip()
        if not clean or clean.upper() in {"BEGIN", "COMMIT"}:
            continue
        output.append(clean)
    return output


def _backup(conn: Any, before: dict[str, dict[str, Any]], games: list[dict[str, Any]], report_sha: str,
            evidence_dir: Path, backup_dir: Path) -> dict[str, Any]:
    backup_dir = backup_dir.expanduser().resolve()
    if backup_dir == RAIZ_REPO or RAIZ_REPO in backup_dir.parents:
        raise ValueError("El respaldo debe quedar fuera del repositorio")
    if backup_dir.exists():
        raise FileExistsError("El directorio de respaldo debe ser nuevo")
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    ids = sorted(before)
    source_links_before = [dict(row) for row in conn.execute(
        """SELECT fuente,id_evento_fuente,partido_id::text AS partido_id,registrado_en
           FROM vinculos_multifuente_partidos_futbol WHERE partido_id=ANY(%s::uuid[])
           ORDER BY fuente,id_evento_fuente""",
        (ids,),
    ).fetchall()]
    source_observations_before = [dict(row) for row in conn.execute(
        """SELECT fuente,id_evento_fuente,partido_id::text AS partido_id,campo,valor,clave_proveedor,
                  periodo_proveedor,sha256_payload,contrato,evidencia_identidad,observado_en,registrado_en
           FROM observaciones_multifuente_estadisticas_futbol WHERE partido_id=ANY(%s::uuid[])
           ORDER BY fuente,id_evento_fuente,campo,contrato,sha256_payload""",
        (ids,),
    ).fetchall()]
    blob = gzip.compress(_json_bytes(before), mtime=0)
    _guardar_nuevo(backup_dir / "partidos_futbol_preaplicacion.json.gz", blob)
    provenance = {
        "source_links_before": source_links_before,
        "source_observations_before": source_observations_before,
        "source_constraints_before": _leer_restricciones(conn),
    }
    provenance_blob = gzip.compress(_json_bytes(provenance), mtime=0)
    _guardar_nuevo(backup_dir / "procedencia_preaplicacion.json.gz", provenance_blob)
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "rows": len(before), "database_url_stored": False,
        "backup_sha256": hashlib.sha256(blob).hexdigest(),
        "provenance_backup_sha256": hashlib.sha256(provenance_blob).hexdigest(),
        "links_before": len(source_links_before),
        "observations_before": len(source_observations_before),
        "constraints_before": provenance["source_constraints_before"],
        "report_sha256": report_sha,
        "archive_sha256": _sha_archivo(evidence_dir / ARCHIVO_ZIP),
        "migration_sha256": _sha_archivo(MIGRACION),
        "ddl_or_dml_performed": False,
    }
    _guardar_nuevo(backup_dir / "manifest_preaplicacion.json", _json_bytes(manifest))
    return {"directory": str(backup_dir), "manifest": manifest}


def _insertar_link_y_evidencia(conn: Any, game: dict[str, Any], identity: dict[str, Any], evidence: list[EvidenciaCampo]) -> None:
    match_id = str(game["match_id"])
    event_id = str(game["source"]["event_id"])
    conn.execute(
        "INSERT INTO vinculos_multifuente_partidos_futbol (fuente,id_evento_fuente,partido_id) VALUES (%s,%s,%s)",
        (FUENTE, event_id, match_id),
    )
    for item in evidence:
        conn.execute(
            """INSERT INTO observaciones_multifuente_estadisticas_futbol
               (fuente,id_evento_fuente,partido_id,campo,valor,clave_proveedor,periodo_proveedor,
                sha256_payload,contrato,evidencia_identidad,observado_en)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (FUENTE, event_id, match_id, item.campo, item.valor, item.clave_proveedor,
             item.periodo_proveedor, item.sha256_payload, item.contrato, Jsonb(identity), item.observado_en),
        )


def _aplicar_plan(conn: Any, match_id: str, row: dict[str, Any], plan: Any) -> dict[str, int]:
    updates = dict(plan.actualizaciones)
    if not updates:
        return {}
    if any(row.get(field) is not None for field in updates):
        raise EvidenciaNoValida("Un destino dejó de ser NULL antes de actualizar")
    setters = sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(field)) for field in updates)
    guards = sql.SQL(" AND ").join(sql.SQL("{} IS NULL").format(sql.Identifier(field)) for field in updates)
    cursor = conn.execute(
        sql.SQL("UPDATE partidos_futbol SET {} WHERE id=%s AND estado='FINALIZADO' AND local_goles_total=%s AND visitante_goles_total=%s AND {}").format(setters, guards),
        (*updates.values(), match_id, row["local_goles_total"], row["visitante_goles_total"]),
    )
    if cursor.rowcount != 1:
        raise EvidenciaNoValida("El UPDATE NULL-only no afectó exactamente una fila")
    return updates


def _postflight(conn: Any, before: dict[str, dict[str, Any]], games: list[dict[str, Any]], plans: dict[str, Any]) -> dict[str, Any]:
    ids = sorted(before)
    after = _leer_estado(conn, ids)
    if set(after) != set(before):
        raise EvidenciaNoValida("Postflight perdió una fila objetivo")
    changes = Counter()
    for game in games:
        match_id = str(game["match_id"])
        row, old = after[match_id], before[match_id]
        for field, value in game["observations"].items():
            canonical = row[field]
            if canonical is None:
                raise EvidenciaNoValida("Postflight dejó un campo objetivo en NULL")
            if old[field] is None and canonical != int(value):
                raise EvidenciaNoValida("Postflight difiere del valor observado")
            if old[field] is not None and canonical != old[field]:
                raise EvidenciaNoValida("Postflight sobrescribió un valor canónico no nulo")
        for field, value in row.items():
            if value != old.get(field):
                changes[field] += 1
                if field not in set(ESTADISTICAS) | TRIGGER_DERIVADOS:
                    raise EvidenciaNoValida(f"Postflight detectó cambio no autorizado en {field}")
        for field in ("competicion_id", "equipo_local_id", "equipo_visitante_id", "fecha_partido", "fecha_partido_local", "estado", "fuente_datos"):
            if row[field] != old[field]:
                raise EvidenciaNoValida("Postflight alteró identidad o estado canónico")
    event_ids = [str(game["source"]["event_id"]) for game in games]
    links = conn.execute(
        "SELECT count(*) AS n FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=ANY(%s)",
        (FUENTE, event_ids),
    ).fetchone()["n"]
    observations = conn.execute(
        "SELECT count(*) AS n FROM observaciones_multifuente_estadisticas_futbol WHERE fuente=%s AND id_evento_fuente=ANY(%s)",
        (FUENTE, event_ids),
    ).fetchone()["n"]
    if links != len(games) or observations != len(games) * 6:
        raise EvidenciaNoValida("Postflight no concilia el número esperado de vínculos/observaciones")
    for game in games:
        match_id = str(game["match_id"])
        event_id = str(game["source"]["event_id"])
        link = conn.execute(
            "SELECT partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=%s",
            (FUENTE, event_id),
        ).fetchone()
        if link is None or str(link["partido_id"]) != match_id:
            raise EvidenciaNoValida("Postflight encontró un vínculo de origen incorrecto")
        rows = conn.execute(
            """SELECT campo,valor,sha256_payload,contrato FROM observaciones_multifuente_estadisticas_futbol
               WHERE fuente=%s AND id_evento_fuente=%s AND partido_id=%s""",
            (FUENTE, event_id, match_id),
        ).fetchall()
        expected_observations = {str(field): int(value) for field, value in game["observations"].items()}
        if (len(rows) != 6
                or {str(item["campo"]): int(item["valor"]) for item in rows} != expected_observations
                or {item["sha256_payload"] for item in rows} != {game["source"]["row_sha256"]}
                or {item["contrato"] for item in rows} != {"KAGGLE_GOKHANERGUL_CUP_STATS_V2"}):
            raise EvidenciaNoValida("Postflight no reproduce valores/hash/contrato de la fila fuente")
    return {"matches": len(ids), "fields_written": sum(len(plan.actualizaciones) for plan in plans.values()),
            "links": links, "observations": observations, "changed_columns": dict(changes),
            "identity_and_nonnull_preserved": True}


def ejecutar(
    evidence_dir: Path,
    *,
    apply: bool,
    backup_dir: Path | None,
    report_name: str = REPORTE,
) -> dict[str, Any]:
    games, report, archive_path, report_path = _leer_reporte(evidence_dir, report_name)
    observed_at = datetime.fromisoformat(str(report["audited_at_utc"]))
    load_dotenv(RAIZ_REPO / "backend/.env", override=False)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no está disponible en el mecanismo protegido")
    ids = sorted(str(game["match_id"]) for game in games)
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as read_conn:
        read_conn.read_only = True
        with read_conn.transaction():
            read_conn.execute("SET TRANSACTION READ ONLY")
            read_conn.execute("SET LOCAL statement_timeout='45s'")
            before = _leer_estado(read_conn, ids)
            if len(before) != len(games):
                raise EvidenciaNoValida("El preflight no recuperó todos los objetivos canónicos")
            plans, sidecars = _crear_planes(
                read_conn, games, before, _sha_archivo(archive_path), observed_at
            )
            expected_updates = sum(len(plan.actualizaciones) for plan in plans.values())
            conflict_fields = sum(len(plan.conflictos) for plan in plans.values())
            if (expected_updates != report["values_null_available"]
                    or conflict_fields != report["values_conflicting_nonnull"]):
                raise EvidenciaNoValida("El merge NULL-only no reproduce los contadores del reporte")
            tables = read_conn.execute(
                "SELECT to_regclass('public.vinculos_multifuente_partidos_futbol')::text AS links, "
                "to_regclass('public.observaciones_multifuente_estadisticas_futbol')::text AS observations"
            ).fetchone()
            if tables["links"] is None or tables["observations"] is None:
                raise EvidenciaNoValida("Faltan las tablas de procedencia previamente migradas")
            migration_needed = _migracion_necesaria(read_conn)
            for game in games:
                exists = read_conn.execute(
                    "SELECT partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=%s",
                    (FUENTE, game["source"]["event_id"]),
                ).fetchone()
                if exists:
                    raise EvidenciaNoValida("Ya existe un vínculo Kaggle para este ID; no se reingesta")
            summary = {
                "status": "READ_ONLY_PREFLIGHT_OK",
                "database_read_only": True,
                "matches": len(games),
                "source_observations": len(games) * 6,
                "null_only_updates": expected_updates,
                "equal_existing_values_preserved": report["values_equal_nonnull"],
                "conflicting_existing_values_preserved": conflict_fields,
                "migration_needed": migration_needed,
                "source_archive_sha256": _sha_archivo(archive_path),
                "report_sha256": _sha_archivo(report_path),
                "database_changes": False,
            }
    if not apply:
        return summary
    if backup_dir is None:
        raise ValueError("--apply requiere --backup-dir nuevo y privado")
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as backup_conn:
        backup_conn.read_only = True
        with backup_conn.transaction():
            backup_conn.execute("SET TRANSACTION READ ONLY")
            backup_conn.execute("SET LOCAL statement_timeout='45s'")
            backup_before = _leer_estado(backup_conn, ids)
            _crear_planes(
                backup_conn, games, backup_before, _sha_archivo(archive_path), observed_at
            )
            backup_info = _backup(backup_conn, backup_before, games, summary["report_sha256"],
                                  evidence_dir.expanduser().resolve(), backup_dir)
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as write_conn:
        with write_conn.transaction():
            write_conn.execute("SET LOCAL lock_timeout='5s'")
            write_conn.execute("SET LOCAL statement_timeout='60s'")
            locked = _leer_estado(write_conn, ids, for_update=True)
            if _serializar(locked) != _serializar(backup_before):
                raise EvidenciaNoValida("El lote cambió después del respaldo; rollback sin aplicar")
            locked_plans, sidecars = _crear_planes(
                write_conn, games, locked, _sha_archivo(archive_path), observed_at
            )
            if _migracion_necesaria(write_conn):
                for statement in _statements_migracion():
                    write_conn.execute(statement, prepare=False)
            for game in games:
                match_id = str(game["match_id"])
                _insertar_link_y_evidencia(
                    write_conn, game, sidecars["identity"][match_id], sidecars["evidence"][match_id]
                )
                _aplicar_plan(write_conn, match_id, locked[match_id], locked_plans[match_id])
            transactional_postflight = _postflight(write_conn, locked, games, locked_plans)
    with connect(database_url, connect_timeout=12, row_factory=dict_row) as post_conn:
        post_conn.read_only = True
        with post_conn.transaction():
            post_conn.execute("SET TRANSACTION READ ONLY")
            post_conn.execute("SET LOCAL statement_timeout='45s'")
            independent_postflight = _postflight(post_conn, backup_before, games, plans)
    return {
        **summary,
        "status": "APPLIED_AND_VERIFIED",
        "database_read_only": False,
        "database_changes": True,
        "migration_applied": migration_needed,
        "backup": backup_info,
        "transaction_postflight": transactional_postflight,
        "independent_read_only_postflight": independent_postflight,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--report-name", default=REPORTE,
                        help="Nombre del reporte de auditoría JSON dentro del directorio privado")
    parser.add_argument("--apply", action="store_true", help="Aplica con backup y postflight; por defecto solo READ ONLY")
    parser.add_argument("--backup-dir", type=Path)
    args = parser.parse_args()
    try:
        result = ejecutar(args.evidence_dir, apply=args.apply, backup_dir=args.backup_dir,
                          report_name=args.report_name)
    except Exception as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__,
                          "sqlstate": getattr(getattr(exc, "diag", None), "sqlstate", None)}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
