"""Recupera el único corner local explícito que quedó NULL en Serie A.

Modo predeterminado: auditoría READ ONLY. ``--apply`` guarda respaldo privado,
ensaya la transacción con rollback, vuelve a validar bajo lock y solo escribe
``local_corners_total=0`` si tres capturas licenciadas/corroborantes concilian
el mismo evento. No altera el marcador canónico 3-0 ni las métricas ya cargadas.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

RAIZ_REPO = Path(__file__).resolve().parents[2]
EVIDENCIA = Path(
    "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/"
    "RECUPERACION_MULTIFUENTE_SEGUIMIENTO_2026-10-20"
)
SALIDA = EVIDENCIA / "VERONA_ROMA_CORNERS_ZERO"
ID_CANONICO = "b7b40a06-5e43-4672-bf02-e1d8a4a85a1c"
FECHA = "2020-09-19"
ESPN_ID = "583156"
HF_ID = "API_FOOTBALL/608489"
DATAHUB_ID = "football-data.co.uk/ITA_SERIEA_2021.csv#row=3"
FUENTE_CAMPO = "local_corners_total"
HUELLAS = {
    "espn_scoreboard": "57b6b3f0cc3169bcc56e35c3822c1db71394d54b57c0c5c0cf692141a0978811",
    "datahub_seriea_csv": "2b39faf9d4a8df5bac17047aa6a41927322a3f618aea0b3c2bf75349cf52342a",
    "kaggle_cc0_zip": "1b7556539edc1011172e8838a986d2dd277d9a6f47ddc5b5f4301e7be632b492",
}
COLUMNAS_OBJETIVO = (
    "local_corners_total", "visitante_corners_total", "local_disparos_total",
    "visitante_disparos_total", "local_disparos_arco", "visitante_disparos_arco",
)
CAMBIOS_DERIVADOS_PERMITIDOS = {
    "actualizado_en", "datos_completos", "datos_corners_completos",
    "datos_disparos_completos",
}
FUENTES_REGISTRADAS = (
    {"name": "ESPN_SOCCER", "event_id": ESPN_ID, "field": FUENTE_CAMPO,
     "value": 0, "provider_key": "wonCorners", "period": "All",
     "contract": "ESPN_SOCCER_SCOREBOARD_V1"},
    {"name": "DATAHUB_FOOTBALL_DATA", "event_id": DATAHUB_ID,
     "field": FUENTE_CAMPO, "value": 0, "provider_key": "HC", "period": "All",
     "contract": "DATAHUB_FOOTBALL_DATA_CSV_V1"},
    {"name": "HF_EATPIZZANOT", "event_id": HF_ID, "field": FUENTE_CAMPO,
     "value": 0, "provider_key": "home_corners", "period": "All",
     "contract": "HF_EATPIZZANOT_STATS_V1"},
)


class EvidenciaNoValida(RuntimeError):
    pass


class RollbackEsperado(RuntimeError):
    pass


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return _sha_bytes(payload.encode("utf-8"))


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _guardar_nuevo(path: Path, content: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def _guardar_json(path: Path, data: Any) -> str:
    payload = (json.dumps(data, ensure_ascii=False, sort_keys=True,
                          indent=2, default=str, allow_nan=False) + "\n").encode()
    _guardar_nuevo(path, payload)
    return _sha_bytes(payload)


def _leer_fuentes() -> dict[str, Any]:
    espn_path = EVIDENCIA / "ESPN_SCOREBOARDS/scoreboard_ita_1_202009.json.gz"
    datahub_path = EVIDENCIA / "DATAHUB_FOOTBALL_CSV/ITA_SERIEA_2021.csv"
    kaggle_path = EVIDENCIA / "KAGGLE_CC0_TOP5_PROBE/top5leagues.zip"
    hf_path = EVIDENCIA / "HF_GLOBAL_FOOTBALL/hf_dataset_candidate_batch_v3_canonical_aliases.json"
    for name, path in (("espn_scoreboard", espn_path), ("datahub_seriea_csv", datahub_path),
                       ("kaggle_cc0_zip", kaggle_path)):
        if not path.is_file() or _sha_file(path) != HUELLAS[name]:
            raise EvidenciaNoValida(f"La evidencia local cambió o falta: {name}")

    espn_raw = gzip.decompress(espn_path.read_bytes())
    scoreboard = json.loads(espn_raw)
    events = [event for event in scoreboard.get("events", []) if str(event.get("id")) == ESPN_ID]
    if len(events) != 1:
        raise EvidenciaNoValida("El scoreboard no contiene un único evento ESPN esperado")
    event = events[0]
    competitions = event.get("competitions") or []
    league_ids = {str(league.get("id")) for league in scoreboard.get("leagues", [])}
    if (len(competitions) != 1 or "730" not in league_ids
            or "~l:730~" not in str(competitions[0].get("uid", ""))
            or competitions[0].get("altGameNote") != "Serie A"):
        raise EvidenciaNoValida("El evento ESPN no concilia con Serie A")
    sides: dict[str, dict[str, Any]] = {}
    for team in competitions[0].get("competitors", []):
        side = team.get("homeAway")
        if side not in {"home", "away"} or side in sides:
            raise EvidenciaNoValida("Lados ESPN ausentes o duplicados")
        stats = {str(item.get("name")): item.get("displayValue")
                 for item in team.get("statistics", [])}
        sides[side] = {"name": (team.get("team") or {}).get("displayName"),
                       "score": team.get("score"), "stats": stats}
    if set(sides) != {"home", "away"}:
        raise EvidenciaNoValida("Faltan lados ESPN")
    if (event.get("date") != "2020-09-19T18:45Z"
            or sides["home"]["name"] != "Hellas Verona"
            or sides["away"]["name"] != "AS Roma"
            or sides["home"]["score"] != "0" or sides["away"]["score"] != "0"):
        raise EvidenciaNoValida("La identidad ESPN no concilia en fecha/equipos/marcador jugado")
    for side in ("home", "away"):
        for key in ("wonCorners", "totalShots", "shotsOnTarget"):
            if key not in sides[side]["stats"]:
                raise EvidenciaNoValida(f"ESPN no contiene {key} para {side}")
    espn_stats = {
        "home_corners": int(sides["home"]["stats"]["wonCorners"]),
        "away_corners": int(sides["away"]["stats"]["wonCorners"]),
        "home_shots": int(sides["home"]["stats"]["totalShots"]),
        "away_shots": int(sides["away"]["stats"]["totalShots"]),
        "home_sot": int(sides["home"]["stats"]["shotsOnTarget"]),
        "away_sot": int(sides["away"]["stats"]["shotsOnTarget"]),
    }

    datahub_rows = []
    with datahub_path.open(newline="", encoding="utf-8-sig") as stream:
        for row_number, row in enumerate(csv.DictReader(stream), start=2):
            if (row.get("Date") == FECHA and row.get("HomeTeam") == "Verona"
                    and row.get("AwayTeam") == "Roma"):
                datahub_rows.append((row_number, row))
    if len(datahub_rows) != 1 or datahub_rows[0][0] != 3:
        raise EvidenciaNoValida("La fila DataHub del evento no es única o cambió")
    datahub_row = datahub_rows[0][1]
    datahub_stats = {"home_corners": int(datahub_row["HC"]),
                     "away_corners": int(datahub_row["AC"]),
                     "home_shots": int(datahub_row["HS"]),
                     "away_shots": int(datahub_row["AS"]),
                     "home_sot": int(datahub_row["HST"]),
                     "away_sot": int(datahub_row["AST"])}
    datahub_row_sha = _sha_json(datahub_row)
    if (datahub_row["FTHG"], datahub_row["FTAG"]) != ("0", "0"):
        raise EvidenciaNoValida("El marcador jugado DataHub esperado cambió")

    kaggle_bytes = kaggle_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(kaggle_bytes)) as archive:
        member = "top5/serie_a/2020-2021.csv"
        raw_csv = archive.read(member)
    kaggle_rows = []
    for row in csv.DictReader(io.StringIO(raw_csv.decode("utf-8-sig"))):
        if (row.get("Date") == FECHA and row.get("HomeTeam") == "Verona"
                and row.get("AwayTeam") == "Roma"):
            kaggle_rows.append(row)
    if len(kaggle_rows) != 1:
        raise EvidenciaNoValida("La fila Kaggle del evento no es única")
    kaggle_row = kaggle_rows[0]
    kaggle_stats = {"home_corners": int(kaggle_row["HC"]),
                    "away_corners": int(kaggle_row["AC"]),
                    "home_shots": int(kaggle_row["HS"]),
                    "away_shots": int(kaggle_row["AS"]),
                    "home_sot": int(kaggle_row["HST"]),
                    "away_sot": int(kaggle_row["AST"])}
    if (kaggle_row["FTHG"], kaggle_row["FTAG"]) != ("0", "0"):
        raise EvidenciaNoValida("El marcador jugado Kaggle esperado cambió")
    kaggle_row_sha = _sha_json(kaggle_row)

    hf_doc = json.loads(hf_path.read_text(encoding="utf-8"))
    hf_matches = [m for m in hf_doc.get("matches", []) if m.get("canonical_id") == ID_CANONICO]
    if len(hf_matches) != 1:
        raise EvidenciaNoValida("El crosswalk HF no tiene una única fila Verona–Roma")
    hf = hf_matches[0]
    hf_stats = hf.get("raw_source_payload", {}).get("match_stats", {})
    hf_normalized_stats = {
        "home_corners": hf_stats.get("home_corners"),
        "away_corners": hf_stats.get("away_corners"),
        "home_shots": hf_stats.get("home_shots_total"),
        "away_shots": hf_stats.get("away_shots_total"),
        "home_sot": hf_stats.get("home_shots_on_goal"),
        "away_sot": hf_stats.get("away_shots_on_goal"),
    }
    hf_file_hashes = hf.get("source_files_sha256") or hf_doc.get("source_file_sha256") or {}
    if (hf.get("source_event_id") != HF_ID or hf.get("source_fixture_id") != 209611
            or hf.get("canonical_ft") != [3, 0]
            or hf_stats.get("home_corners") != 0 or hf_stats.get("away_corners") != 6
            or hf.get("source_row_sha256") != "f552dd8cde80448c086002c66ad50ca116bb5f36ffbbb7d53f95910669e02d0f"):
        raise EvidenciaNoValida("La fila HF no concilia con la fuente ya vinculada")
    if hf_file_hashes.get("match_stats.parquet") != "2fb85b14b4428e1a36efe6d651de4ca8f7a6169ecfa3edb9cda49cb5e58d97e9":
        raise EvidenciaNoValida("El hash del parquet HF no concilia")
    if not (espn_stats["home_corners"] == datahub_stats["home_corners"] ==
            kaggle_stats["home_corners"] == hf_normalized_stats["home_corners"] == 0):
        raise EvidenciaNoValida("No hay consenso explícito para los corners locales")
    if not (espn_stats["away_corners"] == datahub_stats["away_corners"] ==
            kaggle_stats["away_corners"] == hf_normalized_stats["away_corners"] == 6):
        raise EvidenciaNoValida("Los corners visitantes no concilian como control")
    if (espn_stats["home_shots"] != hf_normalized_stats["home_shots"]
            or espn_stats["away_shots"] != hf_normalized_stats["away_shots"]):
        raise EvidenciaNoValida("Los valores ESPN/HF de tiros no concilian")
    if (datahub_stats["home_shots"], datahub_stats["away_shots"],
            datahub_stats["home_sot"], datahub_stats["away_sot"]) != (9, 15, 7, 7):
        raise EvidenciaNoValida("La fila DataHub esperada cambió")
    if (kaggle_stats["home_shots"], kaggle_stats["away_shots"],
            kaggle_stats["home_sot"], kaggle_stats["away_sot"]) != (9, 15, 7, 7):
        raise EvidenciaNoValida("La fila Kaggle esperada cambió")

    return {
        "status": "READ_ONLY_CONSENSUS_SOURCE_AUDIT",
        "target": {"canonical_id": ID_CANONICO, "competition": "ITA_SERIEA",
                   "date_local": FECHA, "home": "Hellas Verona", "away": "Roma",
                   "canonical_ft_preserved": [3, 0], "only_null_target": FUENTE_CAMPO,
                   "proposed_value": 0},
        "source_results": {
            "ESPN_SOCCER": {"event_id": ESPN_ID, "file_sha256": HUELLAS["espn_scoreboard"],
                            "event_sha256": _sha_json(event), "match_date_utc": event["date"],
                            "played_ft": [0, 0], "stats": espn_stats},
            "DATAHUB_FOOTBALL_DATA": {"source_row_id": DATAHUB_ID,
                                      "csv_sha256": HUELLAS["datahub_seriea_csv"],
                                      "row_sha256": datahub_row_sha, "license": "ODC-PDDL-1.0",
                                      "played_ft": [0, 0], "stats": datahub_stats},
            "KAGGLE_FERRARIBOY4K": {"archive_sha256": HUELLAS["kaggle_cc0_zip"],
                                    "member": member, "row_sha256": kaggle_row_sha,
                                    "license": "CC0 Public Domain per Kaggle metadata",
                                    "upstream": ["football-data.co.uk", "understat.com", "sofifa.com", "transfermarkt.co.uk"],
                                    "played_ft": [0, 0], "stats": kaggle_stats,
                                    "not_persisted_as_independent_source": True},
            "HF_EATPIZZANOT": {"event_id": HF_ID, "fixture_id": 209611,
                               "dataset_revision": hf_doc.get("dataset_revision"),
                               "row_sha256": hf.get("source_row_sha256"),
                               "file_sha256": hf_file_hashes.get("match_stats.parquet"),
                               "license": "CC-BY-4.0; upstream rights caveat retained",
                               "source_ft": [3, 0], "stats": hf_normalized_stats},
        },
        "identity_policy": "Exact competition/date/ordered teams plus ESPN and HF provider event IDs; score difference between played 0-0 reports and canonical 3-0 is documented, not used to mutate canonical goals. Only a consensus corners field is eligible.",
        "score_explanation": "Not independently adjudicated by this script; canonical FT is preserved without asserting a cause.",
        "unresolved_source_conflicts": {
            "shots": {"ESPN_and_HF": [8, 21], "DataHub_and_Kaggle": [9, 15]},
            "shots_on_target": {"ESPN_and_HF": [3, 4], "DataHub_and_Kaggle": [7, 7]},
            "decision": "Preserve existing canonical values; no shot fields changed."},
    }


def _target_query(for_update: bool = False) -> str:
    lock = " FOR UPDATE OF p" if for_update else ""
    return """SELECT p.*, to_jsonb(p) AS row_snapshot,
                     p.id::text AS canonical_id, c.codigo AS competition_code,
                     p.fecha_partido_local::date::text AS local_date,
                     el.nombre AS home_name, ev.nombre AS away_name
              FROM partidos_futbol p
              JOIN competiciones_futbol c ON c.id=p.competicion_id
              JOIN equipos_futbol el ON el.id=p.equipo_local_id
              JOIN equipos_futbol ev ON ev.id=p.equipo_visitante_id
              WHERE c.codigo='ITA_SERIEA' AND p.fecha_partido_local::date=%s
                AND lower(el.nombre)='hellas verona' AND lower(ev.nombre)='roma'""" + lock


def _leer_target(conn: Any, *, for_update: bool = False) -> dict[str, Any]:
    rows = conn.execute(_target_query(for_update), (FECHA,)).fetchall()
    if len(rows) != 1:
        raise EvidenciaNoValida(f"La consulta exacta encontró {len(rows)} filas, se requiere una")
    row = dict(rows[0])
    if row["canonical_id"] != ID_CANONICO:
        raise EvidenciaNoValida("El ID canónico no concilia")
    if (str(row["estado"]) != "FINALIZADO" or row["local_goles_total"] != 3
            or row["visitante_goles_total"] != 0):
        raise EvidenciaNoValida("Estado o marcador canónico inesperado; no se escribe")
    expected = {
        "visitante_corners_total": 6, "local_disparos_total": 8,
        "visitante_disparos_total": 21, "local_disparos_arco": 3,
        "visitante_disparos_arco": 4,
    }
    for field, value in expected.items():
        if row[field] != value:
            raise EvidenciaNoValida(f"El campo no nulo {field} cambió; se preserva y aborta")
    if row[FUENTE_CAMPO] not in (None, 0):
        raise EvidenciaNoValida("El corner local ya contiene un valor distinto de la evidencia")
    if (row["competicion_id"] is None or row["equipo_local_id"] is None
            or row["equipo_visitante_id"] is None):
        raise EvidenciaNoValida("Faltan llaves canónicas")
    return row


def _leer_procedencia(conn: Any) -> dict[str, Any]:
    links = conn.execute(
        "SELECT fuente,id_evento_fuente,partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE partido_id=%s ORDER BY fuente,id_evento_fuente",
        (ID_CANONICO,),
    ).fetchall()
    observations = conn.execute(
        """SELECT fuente,id_evento_fuente,campo,valor::text AS valor,clave_proveedor,
                  periodo_proveedor,sha256_payload,contrato
           FROM observaciones_multifuente_estadisticas_futbol
           WHERE partido_id=%s ORDER BY fuente,id_evento_fuente,campo,clave_proveedor""",
        (ID_CANONICO,),
    ).fetchall()
    return {"links": [dict(row) for row in links],
            "observations": [dict(row) for row in observations]}


def _validar_procedencia_previa(conn: Any) -> None:
    rows = conn.execute(
        "SELECT fuente,id_evento_fuente,partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE fuente='HF_EATPIZZANOT' AND id_evento_fuente=%s",
        (HF_ID,),
    ).fetchall()
    if len(rows) != 1 or rows[0]["partido_id"] != ID_CANONICO:
        raise EvidenciaNoValida("El vínculo HF que acredita la identidad no existe o no concilia")
    definitions = conn.execute(
        """SELECT conname,pg_get_constraintdef(oid) AS definition
           FROM pg_constraint WHERE conrelid IN (
             'public.vinculos_multifuente_partidos_futbol'::regclass,
             'public.observaciones_multifuente_estadisticas_futbol'::regclass)
             AND contype='c' AND conname IN (
               'vinculos_multifuente_partidos_futbol_fuente_check',
               'observaciones_multifuente_estadisticas_futbol_fuente_check')"""
    ).fetchall()
    if len(definitions) != 2 or any(
        any(source not in row["definition"] for source in
            ("ESPN_SOCCER", "DATAHUB_FOOTBALL_DATA", "HF_EATPIZZANOT"))
        for row in definitions
    ):
        raise EvidenciaNoValida("Los CHECK de fuentes actuales no permiten las observaciones requeridas")


def _insertar_procedencia(
    conn: Any, audit: dict[str, Any], observed_at: datetime, canonical_row: dict[str, Any]
) -> None:
    source_hashes = {
        "ESPN_SOCCER": audit["source_results"]["ESPN_SOCCER"]["event_sha256"],
        "DATAHUB_FOOTBALL_DATA": audit["source_results"]["DATAHUB_FOOTBALL_DATA"]["row_sha256"],
        "HF_EATPIZZANOT": audit["source_results"]["HF_EATPIZZANOT"]["row_sha256"],
    }
    source_details = {
        "ESPN_SOCCER": audit["source_results"]["ESPN_SOCCER"],
        "DATAHUB_FOOTBALL_DATA": audit["source_results"]["DATAHUB_FOOTBALL_DATA"],
        "HF_EATPIZZANOT": audit["source_results"]["HF_EATPIZZANOT"],
    }
    common = {
        "canonical_match_id": ID_CANONICO,
        "canonical_competition": "ITA_SERIEA",
        "canonical_date_local": FECHA,
        "canonical_home_team_id": str(canonical_row["equipo_local_id"]),
        "canonical_away_team_id": str(canonical_row["equipo_visitante_id"]),
        "canonical_ft_preserved": [3, 0],
        "played_score_reports": {"ESPN_SOCCER": [0, 0], "DATAHUB_FOOTBALL_DATA": [0, 0],
                                 "KAGGLE_FERRARIBOY4K": [0, 0], "HF_EATPIZZANOT": [3, 0]},
        "score_explanation": audit["score_explanation"],
        "identity_policy": audit["identity_policy"],
        "field_conflicts_not_applied": audit["unresolved_source_conflicts"],
        "zero_policy": "Explicit 0 retained only because ESPN, DataHub, Kaggle and HF all report 0 for this exact home-corner field.",
    }
    for item in FUENTES_REGISTRADAS:
        source = item["name"]
        conn.execute(
            """INSERT INTO vinculos_multifuente_partidos_futbol(fuente,id_evento_fuente,partido_id)
               VALUES (%s,%s,%s) ON CONFLICT (fuente,id_evento_fuente) DO NOTHING""",
            (source, item["event_id"], ID_CANONICO),
        )
        link = conn.execute(
            "SELECT partido_id::text FROM vinculos_multifuente_partidos_futbol WHERE fuente=%s AND id_evento_fuente=%s",
            (source, item["event_id"]),
        ).fetchone()
        if link is None or link["partido_id"] != ID_CANONICO:
            raise EvidenciaNoValida(f"El vínculo concurrente de {source} apunta a otro partido")
        identity = {**common, "source": source, "source_event_id": item["event_id"],
                    "source_field": item["provider_key"], "source_value": 0,
                    "source_details": source_details[source]}
        conn.execute(
            """INSERT INTO observaciones_multifuente_estadisticas_futbol
               (fuente,id_evento_fuente,partido_id,campo,valor,clave_proveedor,
                periodo_proveedor,sha256_payload,contrato,evidencia_identidad,observado_en)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT DO NOTHING""",
            (source, item["event_id"], ID_CANONICO, item["field"], item["value"],
             item["provider_key"], item["period"], source_hashes[source], item["contract"],
             Jsonb(identity), observed_at),
        )
        observation = conn.execute(
            """SELECT valor::text,sha256_payload FROM observaciones_multifuente_estadisticas_futbol
               WHERE fuente=%s AND id_evento_fuente=%s AND partido_id=%s AND campo=%s
                 AND clave_proveedor=%s AND periodo_proveedor=%s AND contrato=%s""",
            (source, item["event_id"], ID_CANONICO, item["field"], item["provider_key"],
             item["period"], item["contract"]),
        ).fetchone()
        if observation is None or observation["valor"] != "0" or observation["sha256_payload"].strip() != source_hashes[source]:
            raise EvidenciaNoValida(f"La observación de procedencia {source} no concilia")


def _hacer_cambios(conn: Any, audit: dict[str, Any], *, rehearsal: bool = False) -> dict[str, Any]:
    conn.execute("SET LOCAL lock_timeout='5s'")
    conn.execute("SET LOCAL statement_timeout='30s'")
    row = _leer_target(conn, for_update=True)
    _validar_procedencia_previa(conn)
    observed = datetime.now(timezone.utc)
    _insertar_procedencia(conn, audit, observed, row)
    cursor = conn.execute(
        """UPDATE partidos_futbol SET local_corners_total=0
           WHERE id=%s AND estado='FINALIZADO' AND local_goles_total=3
             AND visitante_goles_total=0 AND local_corners_total IS NULL""",
        (ID_CANONICO,),
    )
    if cursor.rowcount != 1:
        raise EvidenciaNoValida("La guarda NULL-only no actualizó exactamente un campo")
    after = conn.execute("SELECT to_jsonb(p) AS row FROM partidos_futbol p WHERE id=%s", (ID_CANONICO,)).fetchone()["row"]
    if after.get(FUENTE_CAMPO) != 0 or after.get("local_goles_total") != 3 or after.get("visitante_goles_total") != 0:
        raise EvidenciaNoValida("La escritura de corner no preservó la fila canónica")
    prior = row.get("row_snapshot")
    if not isinstance(prior, dict):
        raise EvidenciaNoValida("No se pudo obtener snapshot JSONB de la fila previa")
    changed = [key for key in set(prior) | set(after) if prior.get(key) != after.get(key)]
    allowed = set(COLUMNAS_OBJETIVO) | CAMBIOS_DERIVADOS_PERMITIDOS
    if set(changed) - allowed != set():
        raise EvidenciaNoValida(f"Cambió una columna no autorizada: {sorted(set(changed)-allowed)}")
    return {"target": ID_CANONICO, "field": FUENTE_CAMPO, "value": 0,
            "rowcount": cursor.rowcount, "changed_columns": sorted(changed),
            "provenance_observations": 3, "rollback_rehearsal": rehearsal}


def _preflight(conn: Any, audit: dict[str, Any]) -> dict[str, Any]:
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        conn.execute("SET LOCAL statement_timeout='20s'")
        row = _leer_target(conn)
        _validar_procedencia_previa(conn)
        provenance = _leer_procedencia(conn)
        result = {
            "status": "READ_ONLY_PREFLIGHT_OK",
            "database_changes": False,
            "canonical": {"id": ID_CANONICO, "date": row["local_date"],
                          "home": row["home_name"], "away": row["away_name"],
                          "ft": [row["local_goles_total"], row["visitante_goles_total"]],
                          "target_before": row[FUENTE_CAMPO],
                          "other_target_values": {field: row[field] for field in COLUMNAS_OBJETIVO if field != FUENTE_CAMPO}},
            "target_count": 1,
            "current_provenance": provenance,
            "source_audit_sha256": _sha_json(audit),
            "migration_needed": False,
        }
    return result


def _snapshot(conn: Any) -> dict[str, Any]:
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        conn.execute("SET LOCAL statement_timeout='20s'")
        _validar_procedencia_previa(conn)
        full = conn.execute("SELECT to_jsonb(p) AS row FROM partidos_futbol p WHERE id=%s", (ID_CANONICO,)).fetchone()
        if full is None:
            raise EvidenciaNoValida("El registro canónico desapareció antes del backup")
        return {"canonical_row": full["row"], "provenance": _leer_procedencia(conn)}


def _verify_rollback(conn: Any) -> dict[str, Any]:
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        row = _leer_target(conn)
        provenance = _leer_procedencia(conn)
    if row[FUENTE_CAMPO] is not None:
        raise EvidenciaNoValida("El ensayo no revirtió el NULL original")
    if any(link["fuente"] in {"ESPN_SOCCER", "DATAHUB_FOOTBALL_DATA"} and
           link["id_evento_fuente"] in {ESPN_ID, DATAHUB_ID} for link in provenance["links"]):
        raise EvidenciaNoValida("El ensayo dejó vínculos fuente persistidos")
    if any(obs["campo"] == FUENTE_CAMPO and obs["id_evento_fuente"] in {ESPN_ID, DATAHUB_ID, HF_ID}
           for obs in provenance["observations"]):
        raise EvidenciaNoValida("El ensayo dejó observaciones persistidas")
    return {"status": "ROLLBACK_VERIFIED", "canonical_field_is_null": True,
            "new_links": 0, "new_observations": 0}


def ejecutar(*, apply: bool) -> dict[str, Any]:
    audit = _leer_fuentes()
    run_id = datetime.now(timezone.utc).strftime("RUN_%Y%m%dT%H%M%S%fZ")
    SALIDA.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(SALIDA, 0o700)
    run_dir = SALIDA / run_id
    run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(run_dir, 0o700)
    _guardar_json(run_dir / "source_consensus_audit.json", audit)
    audit_hash = _sha_file(run_dir / "source_consensus_audit.json")
    load_dotenv(RAIZ_REPO / "backend/.env", override=False)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise EvidenciaNoValida("DATABASE_URL no está disponible en el mecanismo protegido")
    with connect(database_url, connect_timeout=10, row_factory=dict_row) as conn:
        preflight = _preflight(conn, audit)
        preflight["source_audit_file_sha256"] = audit_hash
        _guardar_json(run_dir / "readonly_preflight.json", preflight)
        if not apply:
            return {"run_directory": str(run_dir), **preflight}
        if preflight["canonical"]["target_before"] is not None:
            raise EvidenciaNoValida("El target ya no es NULL; no hay nada que aplicar")
        backup = _snapshot(conn)
        backup_bytes = gzip.compress((json.dumps(backup, ensure_ascii=False, sort_keys=True,
                                               indent=2, default=str, allow_nan=False) + "\n").encode(), mtime=0)
        backup_dir = run_dir / "backup_preaplicacion"
        backup_dir.mkdir(mode=0o700)
        os.chmod(backup_dir, 0o700)
        backup_file = backup_dir / "estado_preaplicacion.json.gz"
        _guardar_nuevo(backup_file, backup_bytes)
        backup_sha = _sha_file(backup_file)
        if backup_sha != _sha_bytes(backup_bytes):
            raise EvidenciaNoValida("La huella del backup no concilia")
        _guardar_json(backup_dir / "manifest.json", {
            "canonical_match_id": ID_CANONICO,
            "backup_file_sha256": backup_sha,
            "source_audit_file_sha256": audit_hash,
            "directory_mode": "0700", "file_mode": "0600",
            "database_url_stored": False,
        })

        try:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ WRITE")
                rehearsal = _hacer_cambios(conn, audit, rehearsal=True)
                raise RollbackEsperado("rollback rehearsal")
        except RollbackEsperado:
            pass
        rollback = _verify_rollback(conn)
        _guardar_json(run_dir / "rollback_rehearsal.json", {**rollback, "transactional_preview": rehearsal})

        with conn.transaction():
            conn.execute("SET TRANSACTION READ WRITE")
            application = _hacer_cambios(conn, audit)
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout='20s'")
            row = _leer_target(conn)
            provenance = _leer_procedencia(conn)
        if row[FUENTE_CAMPO] != 0:
            raise EvidenciaNoValida("Postflight independiente: corner local no concilia")
        target_observations = [obs for obs in provenance["observations"]
                               if obs["campo"] == FUENTE_CAMPO and obs["valor"] == "0"
                               and obs["id_evento_fuente"] in {ESPN_ID, DATAHUB_ID, HF_ID}]
        if len(target_observations) != 3:
            raise EvidenciaNoValida("Postflight independiente: faltan observaciones de las tres fuentes")
        result = {
            "status": "APPLIED_AND_POSTFLIGHT_OK",
            "database_changes": True,
            "canonical_match_id": ID_CANONICO,
            "canonical_ft_preserved": [row["local_goles_total"], row["visitante_goles_total"]],
            "field_applied": FUENTE_CAMPO,
            "value": 0,
            "new_canonical_values": 1,
            "source_match_links_for_this_match": len(provenance["links"]),
            "observations_for_this_field": [dict(obs) for obs in target_observations],
            "application": application,
            "rollback_rehearsal": rollback,
            "backup_sha256": backup_sha,
            "backup_file": str(backup_file),
            "source_audit_sha256": audit_hash,
        }
        _guardar_json(run_dir / "application_result.json", result)
        return {"run_directory": str(run_dir), **result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Ejecuta backup, ensayo con rollback, aplicación y postflight")
    args = parser.parse_args()
    try:
        result = ejecutar(apply=args.apply)
    except Exception as exc:
        # Excepciones de red/driver pueden incluir detalles del DSN; solo se
        # muestran mensajes propios de validación de evidencia.
        message = str(exc)[:500] if isinstance(exc, EvidenciaNoValida) else "Fallo operativo; detalle omitido."
        print(json.dumps({"status": "ERROR", "error_type": type(exc).__name__,
                          "message": message}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
