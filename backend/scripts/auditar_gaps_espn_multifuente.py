"""Audita resúmenes ESPN para partidos enlazados con estadísticas canónicas nulas.

El catálogo se consulta con PostgreSQL READ ONLY. Las peticiones HTTP son GET,
secuenciales, con una pausa mínima de un segundo y sin redirecciones/reintentos.
Los payloads se guardan fuera del repositorio y no se escribe en la BD.

Ejemplo (desde `backend/`):
  python -m scripts.auditar_gaps_espn_multifuente \
    --out /ruta/externa/auditoria.json --raw-dir /ruta/externa/raw
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any

import requests
from psycopg import connect
from psycopg.rows import dict_row

from servicios.resolucion_multifuente_futbol import (
    EvidenciaNoValida,
    extraer_evidencia_espn,
)


LIGAS_PERMITIDAS = frozenset(
    {"eng.fa", "esp.copa_del_rey", "fra.coupe_de_france", "ita.coppa_italia"}
)
URL_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
MAX_BYTES = 8_000_000
_ID_EVENTO = re.compile(r"^[0-9]{1,20}$")


def _guardar_exclusivo(path: Path, contenido: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporal = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as archivo:
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.link(temporal, path)
    finally:
        try:
            os.unlink(temporal)
        except FileNotFoundError:
            pass


def _fuera_del_repo(path: Path, repo_root: Path) -> bool:
    resolved = path.expanduser().resolve()
    return resolved != repo_root and repo_root not in resolved.parents


def _cargar_gaps(conn: Any) -> list[dict[str, Any]]:
    """Lee exactamente la cohorte de copas con gaps examinada previamente."""
    consulta = """
        SELECT e.liga, e.id_fuente, p.id::text AS partido_id,
               p.competicion_id::text AS competicion_id,
               p.equipo_local_id::text AS equipo_local_id,
               p.equipo_visitante_id::text AS equipo_visitante_id,
               p.temporada_id::text AS temporada_id,
               p.fecha_partido, p.estado,
               p.local_goles_total, p.visitante_goles_total,
               p.local_corners_total, p.visitante_corners_total,
               p.local_disparos_total, p.visitante_disparos_total,
               p.local_disparos_arco, p.visitante_disparos_arco,
               e.evidencia,
               home.equipo_id::text AS mapped_home_id,
               away.equipo_id::text AS mapped_away_id,
               season.temporada_id::text AS mapped_season_id,
               canonical_season.competicion_id::text AS mapped_competition_id
          FROM partidos_fuente_espn_futbol e
          JOIN partidos_futbol p ON p.id = e.partido_id
          LEFT JOIN equipos_fuente_espn_futbol home
            ON home.id_fuente = e.evidencia->>'local_id_fuente'
          LEFT JOIN equipos_fuente_espn_futbol away
            ON away.id_fuente = e.evidencia->>'visitante_id_fuente'
          LEFT JOIN temporadas_fuente_espn_futbol season
            ON season.liga = e.liga
           AND season.anio = NULLIF(e.evidencia->>'anio_temporada', '')::integer
          LEFT JOIN temporadas_futbol canonical_season
            ON canonical_season.id = season.temporada_id
         WHERE e.liga = ANY(%s)
           AND p.estado = 'FINALIZADO'
           AND p.local_goles_total IS NOT NULL
           AND p.visitante_goles_total IS NOT NULL
           AND (p.local_corners_total IS NULL OR p.visitante_corners_total IS NULL
                OR p.local_disparos_total IS NULL OR p.visitante_disparos_total IS NULL
                OR p.local_disparos_arco IS NULL OR p.visitante_disparos_arco IS NULL)
         ORDER BY e.liga, p.fecha_partido, e.id_fuente
    """
    return list(conn.execute(consulta, (sorted(LIGAS_PERMITIDAS),)).fetchall())


def _identidad_previa_valida(row: dict[str, Any]) -> tuple[bool, str]:
    evidence = row["evidencia"]
    if not isinstance(evidence, dict):
        return False, "LINK_EVIDENCE_INVALID"
    if row["mapped_home_id"] != row["equipo_local_id"]:
        return False, "HOME_TEAM_CROSSWALK_MISMATCH"
    if row["mapped_away_id"] != row["equipo_visitante_id"]:
        return False, "AWAY_TEAM_CROSSWALK_MISMATCH"
    if row["mapped_season_id"] != row["temporada_id"]:
        return False, "SEASON_CROSSWALK_MISMATCH"
    if row["mapped_competition_id"] != row["competicion_id"]:
        return False, "COMPETITION_CROSSWALK_MISMATCH"
    if not evidence.get("local_id_fuente") or not evidence.get("visitante_id_fuente"):
        return False, "LINK_EVIDENCE_MISSING_TEAM_IDS"
    return True, ""


def _esperado(row: dict[str, Any]) -> dict[str, Any]:
    evidence = row["evidencia"]
    return {
        "id_fuente": str(row["id_fuente"]),
        "liga": str(row["liga"]),
        "inicio_utc": row["fecha_partido"],
        "local_id_fuente": str(evidence["local_id_fuente"]),
        "visitante_id_fuente": str(evidence["visitante_id_fuente"]),
        "local_goles": row["local_goles_total"],
        "visitante_goles": row["visitante_goles_total"],
    }


def _valores_canonicos(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "local_corners_total": row["local_corners_total"],
        "visitante_corners_total": row["visitante_corners_total"],
        "local_disparos_total": row["local_disparos_total"],
        "visitante_disparos_total": row["visitante_disparos_total"],
        "local_disparos_arco": row["local_disparos_arco"],
        "visitante_disparos_arco": row["visitante_disparos_arco"],
    }


def _serializar(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    raise TypeError(f"Tipo no serializable: {type(value).__name__}")


def auditar(
    *,
    database_url: str,
    output: Path,
    raw_dir: Path,
    intervalo: float = 1.2,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Consulta los 97 gaps sin escribir en PostgreSQL ni en el producto."""
    repo_root = Path(__file__).resolve().parents[2]
    output = output.expanduser().resolve()
    raw_dir = raw_dir.expanduser().resolve()
    if not _fuera_del_repo(output, repo_root) or not _fuera_del_repo(raw_dir, repo_root):
        raise ValueError("La evidencia debe quedar fuera del repositorio")
    if output.exists() or raw_dir.exists():
        raise FileExistsError("El destino de evidencia ya existe; no se sobrescribe")
    if intervalo < 1.0:
        raise ValueError("El intervalo mínimo aceptado para ESPN es un segundo")

    conn = connect(database_url, connect_timeout=10, row_factory=dict_row)
    try:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '30s'")
            conn.execute("SET LOCAL lock_timeout = '2s'")
            filas = _cargar_gaps(conn)
    finally:
        conn.close()

    raw_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    cliente = session or requests.Session()
    cliente.headers.update({"Accept": "application/json", "User-Agent": "AnalyticsPredict/1.0"})
    resultados: list[dict[str, Any]] = []
    estadisticas_por_campo: Counter[str] = Counter()
    stop_reason = None
    ultimo_request: float | None = None
    observado_en = datetime.now(timezone.utc)

    try:
        for row in filas:
            liga, event_id = row["liga"], str(row["id_fuente"])
            resultado: dict[str, Any] = {
                "liga": liga,
                "event_id": event_id,
                "partido_id": row["partido_id"],
                "identity_verified": False,
                "identity_reason": None,
                "http_status": None,
                "stats_evidence_count": 0,
                "stats_by_field": {},
                "canonical_null_fields": [
                    field for field, value in _valores_canonicos(row).items() if value is None
                ],
                "raw_sha256": None,
            }
            if liga not in LIGAS_PERMITIDAS or not _ID_EVENTO.fullmatch(event_id):
                resultado["identity_reason"] = "UNSAFE_SOURCE_ID"
                resultados.append(resultado)
                continue
            identity_ok, reason = _identidad_previa_valida(row)
            if not identity_ok:
                resultado["identity_reason"] = reason
                resultados.append(resultado)
                continue
            if ultimo_request is not None:
                restante = intervalo - (time.monotonic() - ultimo_request)
                if restante > 0:
                    time.sleep(restante)
            endpoint = f"{URL_BASE}/{liga}/summary"
            ultimo_request = time.monotonic()
            try:
                response = cliente.get(
                    endpoint,
                    params={"event": event_id},
                    timeout=(5, 20),
                    allow_redirects=False,
                )
            except requests.RequestException as exc:
                resultado["identity_reason"] = f"NETWORK_{type(exc).__name__}"
                resultados.append(resultado)
                stop_reason = "NETWORK_FAILURE_NO_RETRY"
                break
            resultado["http_status"] = int(response.status_code)
            if response.status_code in (401, 403):
                resultado["identity_reason"] = "SOURCE_ACCESS_DENIED_NO_BYPASS"
                resultados.append(resultado)
                stop_reason = f"HTTP_{response.status_code}_STOPPED"
                break
            if response.status_code == 429:
                resultado["identity_reason"] = "SOURCE_RATE_LIMITED_NO_RETRY"
                resultados.append(resultado)
                stop_reason = "HTTP_429_STOPPED"
                break
            if 300 <= response.status_code < 400:
                resultado["identity_reason"] = "REDIRECT_REFUSED"
                resultados.append(resultado)
                stop_reason = "REDIRECT_STOPPED"
                break
            if response.status_code != 200:
                resultado["identity_reason"] = f"HTTP_{response.status_code}"
                resultados.append(resultado)
                if response.status_code >= 500:
                    stop_reason = "SERVER_ERROR_STOPPED"
                    break
                continue
            if len(response.content) > MAX_BYTES:
                resultado["identity_reason"] = "RESPONSE_TOO_LARGE"
                resultados.append(resultado)
                stop_reason = "RESPONSE_SIZE_STOPPED"
                break
            raw_hash = sha256(response.content).hexdigest()
            resultado["raw_sha256"] = raw_hash
            _guardar_exclusivo(raw_dir / f"espn_{liga}_{event_id}.json", response.content)
            try:
                payload = response.json()
            except (ValueError, requests.JSONDecodeError):
                resultado["identity_reason"] = "INVALID_JSON"
                resultados.append(resultado)
                continue
            try:
                evidencia = extraer_evidencia_espn(
                    payload,
                    _esperado(row),
                    observado_en=datetime.now(timezone.utc),
                )
            except EvidenciaNoValida as exc:
                resultado["identity_reason"] = str(exc)
                resultados.append(resultado)
                continue
            resultado["identity_verified"] = True
            resultado["identity_reason"] = None
            by_field: dict[str, Any] = {}
            for item in evidencia:
                by_field[item.campo] = str(item.valor)
                estadisticas_por_campo[item.campo] += 1
            resultado["stats_by_field"] = by_field
            resultado["stats_evidence_count"] = len(evidencia)
            resultados.append(resultado)
    finally:
        if session is None:
            cliente.close()

    conteos_fuente = Counter(row["liga"] for row in filas)
    summary = {
        "schema": "ESPN_SOCCER_NULL_GAPS_AUDIT_V1",
        "observed_at_utc": observado_en.isoformat(),
        "source": "ESPN Soccer public summary endpoint",
        "database_mode": "READ ONLY",
        "request_policy": {"sequential": True, "min_interval_seconds": intervalo, "redirects": False, "retries": 0},
        "candidate_count": len(filas),
        "candidate_count_by_league": dict(conteos_fuente),
        "fetched_count": sum(item["http_status"] is not None for item in resultados),
        "identity_verified_count": sum(item["identity_verified"] for item in resultados),
        "identity_rejected_count": sum(not item["identity_verified"] for item in resultados),
        "stats_evidence_count": sum(item["stats_evidence_count"] for item in resultados),
        "stats_values_by_field": dict(sorted(estadisticas_por_campo.items())),
        "stop_reason": stop_reason,
        "results": resultados,
    }
    encoded = (json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2, default=_serializar) + "\n").encode()
    _guardar_exclusivo(output, encoded)
    return {key: summary[key] for key in (
        "candidate_count", "fetched_count", "identity_verified_count",
        "identity_rejected_count", "stats_evidence_count", "stats_values_by_field", "stop_reason",
    )}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="JSON manifiesto nuevo, fuera del repositorio")
    parser.add_argument("--raw-dir", required=True, type=Path, help="Directorio nuevo para respuestas HTTP")
    parser.add_argument("--interval", type=float, default=1.2, help="Pausa mínima secuencial (>=1 segundo)")
    args = parser.parse_args(argv)
    from db import obtener_database_url

    try:
        result = auditar(
            database_url=obtener_database_url(),
            output=args.out,
            raw_dir=args.raw_dir,
            intervalo=args.interval,
        )
    except Exception as exc:
        parser.error(f"Auditoría detenida ({type(exc).__name__}); no se muestra detalle sensible")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["stop_reason"] is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
