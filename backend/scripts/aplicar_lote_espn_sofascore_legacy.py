"""Carga explícita del lote ESPN validado para fechas SofaScore legacy.

El modo predeterminado es READ ONLY. ``--apply`` requiere un directorio de
backup nuevo fuera del repositorio; crea la migración aditiva y aplica los
47 partidos dentro de una única transacción, verificando el postflight antes
del COMMIT. No descarga fuentes ni corrige fechas canónicas.

Ejemplo desde ``backend/``:
  python -m scripts.aplicar_lote_espn_sofascore_legacy \
    --evidence-dir /ruta/privada/ESPN_SCOREBOARDS
  python -m scripts.aplicar_lote_espn_sofascore_legacy \
    --evidence-dir /ruta/privada/ESPN_SCOREBOARDS --apply \
    --backup-dir /ruta/privada/backup_lote_YYYYMMDD
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from psycopg import connect, sql
from psycopg.rows import dict_row

from servicios.resolucion_multifuente_futbol import (
    CAMPOS_RECUPERABLES,
    EvidenciaCampo,
    EvidenciaNoValida,
    METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA,
    PartidoCanonico,
    PartidoProveedor,
    aplicar_plan_resolucion,
    construir_plan_resolucion,
    extraer_evidencia_espn,
    sha256_json,
    validar_vinculo_partido,
)


RAIZ_REPO = Path(__file__).resolve().parents[2]
MIGRACION = RAIZ_REPO / "backend/migrations/2026-10-20_observaciones_multifuente_futbol.sql"
CAMPOS_OBJETIVO = (
    "local_corners_total",
    "visitante_corners_total",
    "local_disparos_total",
    "visitante_disparos_total",
    "local_disparos_arco",
    "visitante_disparos_arco",
)
TRIGGER_DERIVADOS = {
    "datos_completos",
    "datos_corners_completos",
    "datos_disparos_completos",
    "diferencia_goles",
    "resultado_final",
    "ganador_id",
    "local_goles_total",
    "visitante_goles_total",
    "actualizado_en",
}


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
    ).encode("utf-8")


def _hash_archivo(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for bloque in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _guardar_nuevo(path: Path, contenido: bytes, modo: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, modo)
    try:
        with os.fdopen(fd, "wb") as archivo:
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())
    except Exception:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        raise


def _leer_evidencia(evidence_dir: Path) -> tuple[list[dict[str, Any]], dict[str, list[EvidenciaCampo]], dict[str, dict[str, Any]]]:
    evidence_dir = evidence_dir.expanduser().resolve()
    if evidence_dir == RAIZ_REPO or RAIZ_REPO in evidence_dir.parents:
        raise ValueError("La evidencia debe permanecer fuera del repositorio")
    nombres = {
        "identity_candidates.json",
        "preflight_dry_run_readonly.json",
        "summary_field_evidence.json",
        "legacy_offset_identity_validation_final.json",
    }
    reportes = {nombre: json.loads((evidence_dir / nombre).read_text(encoding="utf-8")) for nombre in nombres}
    final = reportes["legacy_offset_identity_validation_final.json"]
    for nombre, digest in final["input_sha256"].items():
        if nombre not in reportes or _hash_archivo(evidence_dir / nombre) != digest:
            raise EvidenciaNoValida("El hash de un reporte de entrada no coincide")
    if (
        final.get("source") != "ESPN_SOCCER"
        or final.get("canonical_source") != "SOFASCORE"
        or final.get("identity_method") != METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA
        or final.get("scoreboards_validated") != 164
        or final.get("one_to_one_candidates") != 75
        or final.get("matched_summaries_with_stats") != 47
        or final.get("matched_summaries_without_stats") != 28
        or final.get("evidence_values") != 282
        or final.get("all_dry_run_conflicts") != 0
        or final.get("database_changes") != 0
    ):
        raise EvidenciaNoValida("El reporte final no corresponde al lote autorizado")

    candidates = reportes["identity_candidates.json"].get("candidate_games", [])
    preflight = reportes["preflight_dry_run_readonly.json"].get("games", [])
    source_evidence = reportes["summary_field_evidence.json"].get("evidence", [])
    candidate_by_id = {str(row["partido_id"]): row for row in candidates}
    if len(candidates) != 75 or len(candidate_by_id) != 75:
        raise EvidenciaNoValida("Cohorte de candidatos incompleta o duplicada")
    by_event = {str(row["event_id"]): row for row in candidates}
    if len(by_event) != 75:
        raise EvidenciaNoValida("IDs de evento duplicados en la cohorte")
    eligible = {str(row["partido_id"]): row for row in preflight}
    if len(eligible) != 47 or len(preflight) != 47:
        raise EvidenciaNoValida("Cohorte elegible distinta de 47 partidos")
    if len(source_evidence) != 282:
        raise EvidenciaNoValida("La cantidad de evidencia estadística no es 282")

    evidence_by_match: dict[str, list[EvidenciaCampo]] = {partido_id: [] for partido_id in eligible}
    recorded_by_match: dict[str, list[dict[str, Any]]] = {partido_id: [] for partido_id in eligible}
    for item in source_evidence:
        partido_id = str(item.get("partido_id") or "")
        if partido_id not in evidence_by_match:
            raise EvidenciaNoValida("La evidencia apunta a partido fuera del lote elegible")
        if item.get("fuente") != "ESPN_SOCCER":
            raise EvidenciaNoValida("Fuente estadística inesperada")
        evidencia = EvidenciaCampo(
            campo=str(item["campo"]),
            valor=int(item["valor"]),
            fuente="ESPN_SOCCER",
            evento_id=str(item["evento_id"]),
            clave_proveedor=str(item["clave_proveedor"]),
            periodo_proveedor=str(item["periodo_proveedor"]),
            sha256_payload=str(item["sha256_payload"]),
            observado_en=datetime.fromisoformat(str(item["observado_en"]).replace("Z", "+00:00")),
            contrato=str(item["contrato"]),
        )
        evidence_by_match[partido_id].append(evidencia)
        recorded_by_match[partido_id].append(item)

    identities: dict[str, dict[str, Any]] = {}
    for partido_id, planned in eligible.items():
        candidate = candidate_by_id.get(partido_id)
        if candidate is None:
            raise EvidenciaNoValida("Partido elegible ausente de la cohorte de identidad")
        event_id = str(candidate["event_id"])
        if event_id != str(planned["evento_espn"]):
            raise EvidenciaNoValida("El ID ESPN de la identidad y del plan no coincide")
        if not evidence_by_match[partido_id]:
            raise EvidenciaNoValida("Partido elegible sin valores estadísticos")
        if len(evidence_by_match[partido_id]) != 6:
            raise EvidenciaNoValida("Partido elegible no tiene seis valores")
        valores_evidencia = {item.campo: item.valor for item in evidence_by_match[partido_id]}
        valores_preflight = {str(campo): int(valor) for campo, valor in planned["actual_updates"].items()}
        if valores_evidencia != valores_preflight or set(valores_evidencia) != set(CAMPOS_OBJETIVO):
            raise EvidenciaNoValida("El dry-run ya archivado difiere de los payloads extraídos")
        identity = dict(planned["identity_metadata"])
        team_ids = candidate["ids_equipo_espn"]
        score = candidate["marcador_ft"]
        identity.update(
            {
                "metodo": METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA,
                "provider_competition_id": str(candidate["league"]),
                "provider_home_team_id": str(team_ids["local"]),
                "provider_away_team_id": str(team_ids["visitante"]),
                "provider_start_utc": str(candidate["inicio_utc_espn"]),
                "provider_ft": list(score),
                "canonical_source": "SOFASCORE",
            }
        )
        identity["canonical_start_utc"] = str(candidate["sofascore_inicio_utc"])
        if identity.get("canonical_ft") != list(score):
            raise EvidenciaNoValida("FT del crosswalk y del plan no coincide")
        if str(identity.get("canonical_competition_id")) != str(candidate["competicion_id"]):
            raise EvidenciaNoValida("La competición canónica cambió entre reportes")
        identity["canonical_start_utc"] = datetime.fromisoformat(
            identity["canonical_start_utc"].replace("Z", "+00:00")
        )
        identity["provider_start_utc"] = datetime.fromisoformat(
            identity["provider_start_utc"].replace("Z", "+00:00")
        )
        identities[partido_id] = identity

        liga_archivo = str(candidate["league"]).replace(".", "_")
        raw_path = evidence_dir / f"summary_{liga_archivo}_{event_id}.json.gz"
        if not raw_path.is_file():
            raise EvidenciaNoValida("Falta el summary comprimido del evento")
        with gzip.open(raw_path, "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
        expected = {
            "id_fuente": event_id,
            "liga": str(candidate["league"]),
            "inicio_utc": identity["provider_start_utc"],
            "local_id_fuente": str(team_ids["local"]),
            "visitante_id_fuente": str(team_ids["visitante"]),
            "local_goles": int(score[0]),
            "visitante_goles": int(score[1]),
        }
        observaciones_raw = extraer_evidencia_espn(
            payload, expected, observado_en=min(item.observado_en for item in evidence_by_match[partido_id])
        )
        serializadas = sorted(
            (item.campo, item.valor, item.clave_proveedor, item.periodo_proveedor,
             item.sha256_payload, item.contrato)
            for item in observaciones_raw
        )
        registradas = sorted(
            (str(item["campo"]), int(item["valor"]), str(item["clave_proveedor"]),
             str(item["periodo_proveedor"]), str(item["sha256_payload"]), str(item["contrato"]))
            for item in recorded_by_match[partido_id]
        )
        if serializadas != registradas or len(observaciones_raw) != 6:
            raise EvidenciaNoValida("La extracción del payload no reproduce la evidencia archivada")

        canonical = PartidoCanonico(
            partido_id=partido_id,
            competicion_id=str(candidate["competicion_id"]),
            equipo_local_id=str(identity["canonical_home_team_id"]),
            equipo_visitante_id=str(identity["canonical_away_team_id"]),
            inicio_utc=identity["canonical_start_utc"],
            estado="FINALIZADO",
            goles_local=int(score[0]),
            goles_visitante=int(score[1]),
        )
        provider = PartidoProveedor(
            fuente="ESPN_SOCCER",
            evento_id=event_id,
            competicion_id=str(candidate["league"]),
            equipo_local_id=str(team_ids["local"]),
            equipo_visitante_id=str(team_ids["visitante"]),
            inicio_utc=identity["provider_start_utc"],
            estado="finished",
            goles_local=int(score[0]),
            goles_visitante=int(score[1]),
        )
        validar_vinculo_partido(
            canonical,
            provider,
            mapeo_competiciones={("ESPN_SOCCER", provider.competicion_id): canonical.competicion_id},
            mapeo_equipos={
                ("ESPN_SOCCER", provider.equipo_local_id): canonical.equipo_local_id,
                ("ESPN_SOCCER", provider.equipo_visitante_id): canonical.equipo_visitante_id,
            },
            metodo_identidad=METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA,
            fuente_canonica="SOFASCORE",
        )

    return candidates, evidence_by_match, identities


def _leer_filas(conn: Any, partido_ids: list[str], *, for_update: bool = False) -> dict[str, dict[str, Any]]:
    from psycopg import sql

    columnas = sorted(CAMPOS_RECUPERABLES)
    seleccion = [
        "id", "fuente_datos", "estado", "competicion_id", "equipo_local_id",
        "equipo_visitante_id", "fecha_partido", "local_goles_total", "visitante_goles_total",
        "datos_completos", "datos_corners_completos", "datos_disparos_completos",
        "actualizado_en", *columnas,
    ]
    suffix = sql.SQL(" FOR UPDATE") if for_update else sql.SQL("")
    query = sql.SQL("SELECT {} FROM partidos_futbol WHERE id=ANY(%s::uuid[]){}").format(
        sql.SQL(",").join(sql.Identifier(c) for c in seleccion), suffix
    )
    rows = conn.execute(query, (partido_ids,)).fetchall()
    return {str(row["id"]): dict(row) for row in rows}


def _validar_cohorte_y_planes(
    filas: dict[str, dict[str, Any]],
    candidates: list[dict[str, Any]],
    evidence_by_match: dict[str, list[EvidenciaCampo]],
    identities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    candidate_by_id = {str(row["partido_id"]): row for row in candidates}
    if set(filas) != set(candidate_by_id):
        raise ConflictoConcurrente("El conjunto actual de partidos difiere de los 75 candidatos")
    planes: dict[str, Any] = {}
    for partido_id, evidencia in evidence_by_match.items():
        row = filas[partido_id]
        candidate = candidate_by_id[partido_id]
        identity = identities[partido_id]
        if (
            row["fuente_datos"] != "SOFASCORE"
            or row["estado"] != "FINALIZADO"
            or str(row["competicion_id"]) != str(identity["canonical_competition_id"])
            or str(row["equipo_local_id"]) != str(identity["canonical_home_team_id"])
            or str(row["equipo_visitante_id"]) != str(identity["canonical_away_team_id"])
            or row["fecha_partido"].astimezone(timezone.utc) != identity["canonical_start_utc"].astimezone(timezone.utc)
            or [row["local_goles_total"], row["visitante_goles_total"]] != identity["canonical_ft"]
        ):
            raise ConflictoConcurrente("Origen o identidad canónica cambió desde la auditoría")
        actual = {campo: row.get(campo) for campo in CAMPOS_RECUPERABLES}
        plan = construir_plan_resolucion(actual, evidencia)
        if plan.conflictos or plan.actualizaciones != {
            campo: item.valor for campo, items in _agrupar_por_campo(evidencia).items()
            for item in items[:1]
        }:
            raise ConflictoConcurrente("El plan ya no produce seis actualizaciones sin conflicto")
        if set(plan.actualizaciones) != set(CAMPOS_OBJETIVO):
            raise ConflictoConcurrente("El partido no conserva los seis objetivos NULL-only")
        # El trigger canónico recalcula corners totales si ambas mitades existen.
        for lado, total, primero, segundo in (
            ("local", "local_corners_total", "local_corners_1t", "local_corners_2t"),
            ("visitante", "visitante_corners_total", "visitante_corners_1t", "visitante_corners_2t"),
        ):
            if row[primero] is not None and row[segundo] is not None:
                if row[primero] + row[segundo] != plan.actualizaciones[total]:
                    raise ConflictoConcurrente(f"Corners por mitades contradicen el total {lado}")
        planes[partido_id] = plan
    return planes


def _agrupar_por_campo(evidencia: list[EvidenciaCampo]) -> dict[str, list[EvidenciaCampo]]:
    salida: dict[str, list[EvidenciaCampo]] = {}
    for item in evidencia:
        salida.setdefault(item.campo, []).append(item)
    return salida


def _backup_privado(
    conn: Any,
    filas: dict[str, dict[str, Any]],
    evidence_dir: Path,
    backup_dir: Path,
) -> dict[str, Any]:
    backup_dir = backup_dir.expanduser().resolve()
    if backup_dir == RAIZ_REPO or RAIZ_REPO in backup_dir.parents:
        raise ValueError("El backup debe quedar fuera del repositorio")
    if backup_dir.exists():
        raise FileExistsError("El directorio de backup ya existe; no se sobrescribe")
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    rows_payload = {partido_id: row for partido_id, row in sorted(filas.items())}
    comprimido = gzip.compress(_json_bytes(rows_payload), mtime=0)
    backup_path = backup_dir / "partidos_futbol_47_preaplicacion.json.gz"
    _guardar_nuevo(backup_path, comprimido)
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "rows": len(filas),
        "database_url_stored": False,
        "backup_file": backup_path.name,
        "backup_sha256": hashlib.sha256(comprimido).hexdigest(),
        "source_report_sha256": {
            name: _hash_archivo(evidence_dir / name)
            for name in (
                "identity_candidates.json",
                "preflight_dry_run_readonly.json",
                "summary_field_evidence.json",
                "legacy_offset_identity_validation_final.json",
            )
        },
        "migration_sha256": _hash_archivo(MIGRACION),
        "read_only_preflight": True,
        "ddl_or_dml_performed": False,
    }
    _guardar_nuevo(backup_dir / "manifest_preaplicacion.json", _json_bytes(manifest))
    return {"directory": str(backup_dir), "path": backup_path, "manifest": manifest}


def _statements_migracion() -> list[str]:
    contenido = MIGRACION.read_text(encoding="utf-8")
    salida = []
    for bloque in contenido.split(";"):
        limpio = re.sub(r"(?m)^\s*--.*$", "", bloque).strip()
        if not limpio or limpio.upper() in {"BEGIN", "COMMIT"}:
            continue
        salida.append(limpio)
    return salida


def _verificar_postflight(
    conn: Any,
    backup_rows: dict[str, dict[str, Any]],
    plans: dict[str, Any],
    identities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ids = sorted(backup_rows)
    after = _leer_filas(conn, ids)
    if set(after) != set(ids):
        raise ConflictoConcurrente("Postflight no recuperó todas las filas objetivo")
    diff_counts: dict[str, int] = {}
    for partido_id, before in backup_rows.items():
        row = after[partido_id]
        for campo, esperado in plans[partido_id].actualizaciones.items():
            if row[campo] is None or row[campo] != esperado:
                raise ConflictoConcurrente(f"Postflight difiere en el objetivo {campo}")
        if not row["datos_disparos_completos"]:
            raise ConflictoConcurrente("El trigger no derivó datos_disparos_completos=true")
        for campo, valor in row.items():
            previo = before.get(campo)
            if valor != previo:
                diff_counts[campo] = diff_counts.get(campo, 0) + 1
                if campo not in set(CAMPOS_OBJETIVO) | TRIGGER_DERIVADOS:
                    raise ConflictoConcurrente(f"Postflight detectó cambio no esperado en {campo}")
        for campo in ("fuente_datos", "estado", "competicion_id", "equipo_local_id",
                      "equipo_visitante_id", "fecha_partido", "local_goles_total", "visitante_goles_total"):
            if row.get(campo) != before.get(campo):
                raise ConflictoConcurrente(f"Postflight alteró dato protegido {campo}")
    links = conn.execute(
        "SELECT count(*) AS n FROM vinculos_multifuente_partidos_futbol WHERE fuente='ESPN_SOCCER' AND partido_id=ANY(%s::uuid[])",
        (ids,),
    ).fetchone()["n"]
    observations = conn.execute(
        "SELECT count(*) AS n FROM observaciones_multifuente_estadisticas_futbol WHERE fuente='ESPN_SOCCER' AND partido_id=ANY(%s::uuid[])",
        (ids,),
    ).fetchone()["n"]
    if links != 47 or observations != 282:
        raise ConflictoConcurrente("Postflight no concilia los vínculos/observaciones insertados")
    return {
        "partidos_actualizados": len(ids),
        "campos_objetivo_aplicados": sum(len(plan.actualizaciones) for plan in plans.values()),
        "vinculos_evento": links,
        "observaciones_con_procedencia": observations,
        "columnas_con_cambio_detectado": diff_counts,
        "fuente_y_fecha_canónicas_preservadas": True,
        "ft_preservado": True,
        "datos_disparos_completos_derivado": True,
    }


def ejecutar(*, evidence_dir: Path, apply: bool, backup_dir: Path | None) -> dict[str, Any]:
    evidence_dir = evidence_dir.expanduser().resolve()
    candidates, evidence_by_match, identities = _leer_evidencia(evidence_dir)
    load_dotenv(RAIZ_REPO / "backend/.env", override=False)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no está configurada en el entorno de ejecución")

    ids = sorted(str(row["partido_id"]) for row in candidates)
    read_rows: dict[str, dict[str, Any]]
    with connect(database_url, connect_timeout=10, row_factory=dict_row) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '30s'")
            read_rows = _leer_filas(conn, ids)
            if len(read_rows) != 75:
                raise ConflictoConcurrente("El censo READ ONLY no encontró 75 partidos candidatos")
            plans = _validar_cohorte_y_planes(read_rows, candidates, evidence_by_match, identities)
            tables = conn.execute(
                "SELECT to_regclass('public.vinculos_multifuente_partidos_futbol')::text AS links, "
                "to_regclass('public.observaciones_multifuente_estadisticas_futbol')::text AS evidence"
            ).fetchone()
            if apply and any(tables[key] is not None for key in ("links", "evidence")):
                raise EvidenciaNoValida("Las tablas de procedencia ya existen; se aborta sin sobreescribir")
            if any(tables[key] is None for key in ("links", "evidence")):
                migration_pending = True
            else:
                migration_pending = False
            target_rows = {partido_id: read_rows[partido_id] for partido_id in evidence_by_match}
            summary = {
                "mode": "APPLY_REQUESTED" if apply else "READ_ONLY_DRY_RUN",
                "candidate_games": len(candidates),
                "eligible_games": len(plans),
                "planned_field_updates": sum(len(plan.actualizaciones) for plan in plans.values()),
                "conflicts": sum(len(plan.conflictos) for plan in plans.values()),
                "migration_pending": migration_pending,
                "database_changes": False,
            }

        if not apply:
            return summary
        if backup_dir is None:
            raise ValueError("--apply requiere --backup-dir")
        backup_info = _backup_privado(conn, target_rows, Path(evidence_dir).resolve(), backup_dir)
        backup_rows = target_rows
        with conn.transaction():
            conn.execute("SET LOCAL lock_timeout = '5s'")
            conn.execute("SET LOCAL statement_timeout = '60s'")
            latest = _leer_filas(conn, ids)
            if latest != read_rows:
                raise ConflictoConcurrente("La cohorte cambió entre preflight y aplicación")
            for statement in _statements_migracion():
                conn.execute(statement, prepare=False)
            resultados = []
            candidate_by_id = {str(row["partido_id"]): row for row in candidates}
            for partido_id, plan in sorted(plans.items()):
                identity = identities[partido_id]
                candidate = candidate_by_id[partido_id]
                resultado = aplicar_plan_resolucion(
                    conn,
                    partido_id=partido_id,
                    goles_local_ft=int(identity["canonical_ft"][0]),
                    goles_visitante_ft=int(identity["canonical_ft"][1]),
                    plan=plan,
                    identidades={
                        ("ESPN_SOCCER", str(candidate["event_id"])): identity
                    },
                    dry_run=False,
                )
                resultados.append(resultado)
            postflight = _verificar_postflight(conn, backup_rows, plans, identities)
        resumen = {
            **summary,
            "mode": "APPLIED_ATOMICALLY",
            "database_changes": True,
            "migration_applied": True,
            "migration_pending_before_apply": summary["migration_pending"],
            "migration_pending": False,
            "backup_directory": backup_info["directory"],
            "backup_sha256": backup_info["manifest"]["backup_sha256"],
            "application_rows": len(resultados),
            "postflight": postflight,
        }
        return resumen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Aplica migración y valores dentro de una transacción")
    parser.add_argument("--backup-dir", type=Path, help="Destino externo, privado y aún inexistente del respaldo")
    args = parser.parse_args()
    try:
        resultado = ejecutar(evidence_dir=args.evidence_dir, apply=args.apply, backup_dir=args.backup_dir)
    except Exception as exc:
        sqlstate = getattr(getattr(exc, "diag", None), "sqlstate", None)
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "sqlstate": sqlstate}, sort_keys=True))
        return 2
    print(json.dumps(resultado, sort_keys=True, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
