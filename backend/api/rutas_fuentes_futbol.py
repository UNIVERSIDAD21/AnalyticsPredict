"""Lectura de capturas ESPN Soccer; no mezcla snapshots con partidos validados."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from db import obtener_pool
from scripts.auditar_fuente_espn_soccer import LIGAS


router = APIRouter(prefix="/api/futbol/fuentes", tags=["Fútbol - Fuentes"])


def leer_captura_mes(conn, liga: str, mes: str) -> dict:
    """Último lote completo observado; nunca une eventos de distintas capturas."""
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("""
            SELECT id, estado, observado_en, ingestado_en, sha256_scoreboard
            FROM capturas_espn_soccer_lotes
            WHERE liga = %s AND mes = %s
            ORDER BY observado_en DESC, id DESC LIMIT 1
        """, (liga, mes))
        lote = cursor.fetchone()
        if lote is None:
            return {"estado": "SIN_CAPTURA", "fuente": "ESPN_SOCCER", "liga": liga,
                    "mes": mes, "observado_en": None, "ingestado_en": None,
                    "sha256_scoreboard": None, "vinculo_partidos_futbol": "NO_VERIFICADO",
                    "n_eventos": 0,
                    "n_finales": 0, "n_corners": 0, "n_disparos": 0,
                    "n_disparos_arco": 0, "n_1x2": 0, "eventos": []}
        cursor.execute("""
            SELECT evento FROM capturas_espn_soccer_eventos
            WHERE lote_id = %s
            ORDER BY inicio_utc, id_fuente
        """, (lote["id"],))
        eventos = [fila["evento"] for fila in cursor.fetchall()]
    finales = [e for e in eventos if e["final_acreditado"]]
    return {
        "estado": lote["estado"],
        "fuente": "ESPN_SOCCER", "liga": liga, "mes": mes,
        "observado_en": lote["observado_en"],
        "ingestado_en": lote["ingestado_en"],
        "sha256_scoreboard": lote["sha256_scoreboard"].strip(),
        "n_eventos": len(eventos), "n_finales": len(finales),
        "n_corners": sum(e.get("corners_completos") is True for e in finales),
        "n_disparos": sum(e.get("disparos_completos") is True for e in finales),
        "n_disparos_arco": sum(e.get("disparos_arco_completos") is True for e in finales),
        "n_1x2": sum(e.get("local_goles") is not None and e.get("visitante_goles") is not None
                     for e in finales),
        "vinculo_partidos_futbol": "NO_VERIFICADO",
        "eventos": eventos,
    }


@router.get("/espn-soccer", summary="Calendario y outcomes de capturas ESPN Soccer")
async def obtener_espn_soccer(
    liga: str = Query(..., description="premier|laliga|seriea|bundesliga|ligue1"),
    mes: str = Query(..., pattern=r"^[0-9]{6}$", description="Mes UTC YYYYMM"),
):
    if liga not in LIGAS or not 1 <= int(mes[4:]) <= 12 or int(mes[:4]) == 0:
        raise HTTPException(status_code=422, detail="Liga o mes inválido")
    try:
        with obtener_pool().connection() as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            datos = leer_captura_mes(conn, LIGAS[liga], mes)
        for campo in ("observado_en", "ingestado_en"):
            if isinstance(datos.get(campo), datetime):
                datos[campo] = datos[campo].astimezone(timezone.utc).isoformat()
        return datos
    except Exception as exc:
        raise HTTPException(status_code=503, detail={
            "estado": "CAPTURAS_NO_DISPONIBLES",
            "mensaje": "Almacén de capturas ESPN Soccer no disponible",
        }) from exc
