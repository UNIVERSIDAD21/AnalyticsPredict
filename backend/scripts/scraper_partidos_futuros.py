#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper_partidos_futuros.py — Sincroniza partidos próximos (sin resultado) desde ESPN.

Uso:
    python scripts/scraper_partidos_futuros.py --days 14
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import psycopg
import requests
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

ESPN_API = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ZONA_HORARIA_NBA = ZoneInfo("America/New_York")


def obtener_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


def fetch_scoreboard(fecha: date) -> List[Dict[str, Any]]:
    url = f"{ESPN_API}/scoreboard"
    params = {"dates": fecha.strftime("%Y%m%d")}

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("events", [])


def parse_evento_espn(evento: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    comps = evento.get("competitions", [])
    if not comps:
        return None

    comp = comps[0]
    competidores = comp.get("competitors", [])
    if len(competidores) < 2:
        return None

    home = next((c for c in competidores if c.get("homeAway") == "home"), None)
    away = next((c for c in competidores if c.get("homeAway") == "away"), None)

    if not home or not away:
        return None

    status = comp.get("status", {}).get("type", {})
    completado = status.get("completed", False)

    fecha_str = comp.get("date", "")
    try:
        fecha_utc = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
        # Convertir a zona horaria NBA para obtener la fecha correcta del partido
        fecha_nba = fecha_utc.astimezone(ZONA_HORARIA_NBA)
        fecha_partido = fecha_nba.date()
    except (ValueError, TypeError) as exc:
        print(f"    ⚠️ Error parseando fecha: {fecha_str} - {exc}")
        return None

    return {
        "espn_game_id": str(evento.get("id", "")),
        "fecha_partido": fecha_partido,
        "home_team": home.get("team", {}).get("displayName", ""),
        "home_abbr": home.get("team", {}).get("abbreviation", ""),
        "away_team": away.get("team", {}).get("displayName", ""),
        "away_abbr": away.get("team", {}).get("abbreviation", ""),
        "completado": completado,
    }


def obtener_equipo_id(cursor: psycopg.Cursor, nombre: str, abbr: str) -> Optional[str]:
    cursor.execute(
        """
        SELECT id FROM equipos
        WHERE LOWER(nombre) = LOWER(%s)
           OR LOWER(abreviatura) = LOWER(%s)
        LIMIT 1
        """,
        [nombre, abbr],
    )
    row = cursor.fetchone()
    return str(row["id"]) if row else None


def obtener_temporada_activa(cursor: psycopg.Cursor) -> Optional[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT id, nombre FROM temporadas
        WHERE activa = true
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def upsert_partido_futuro(
    cursor: psycopg.Cursor,
    fecha_partido: date,
    temporada_id: str,
    espn_game_id: str,
    equipo_local_id: str,
    equipo_visitante_id: str,
) -> bool:
    """
    Inserta o actualiza un partido futuro (sin resultados).
    Usa INSERT ... ON CONFLICT para manejar duplicados de forma atómica.
    """
    try:
        cursor.execute(
            """
            INSERT INTO partidos (
                temporada_id, fecha_partido, tipo_partido, espn_game_id,
                equipo_local_id, equipo_visitante_id,
                local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
                visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
                diferencia_puntos, hubo_overtime
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0,
                0, false
            )
            ON CONFLICT (espn_game_id) 
            WHERE espn_game_id IS NOT NULL
            DO UPDATE SET
                fecha_partido = EXCLUDED.fecha_partido,
                temporada_id = EXCLUDED.temporada_id,
                actualizado_en = now()
            RETURNING (xmax = 0) AS es_nuevo
            """,
            [
                temporada_id,
                fecha_partido,
                "REG",
                espn_game_id,
                equipo_local_id,
                equipo_visitante_id,
            ],
        )
        row = cursor.fetchone()
        return bool(row and row["es_nuevo"])
    except Exception as e:
        print(f"    ⚠️ Error al insertar partido {espn_game_id}: {e}")
        return False


def sincronizar_partidos_futuros(dias: int = 14) -> Dict[str, int]:
    db_url = obtener_database_url()
    stats = {
        "dias_procesados": 0,
        "eventos_encontrados": 0,
        "insertados": 0,
        "ya_existian": 0,
        "errores": 0,
        "equipos_no_encontrados": 0,
    }

    # Obtener la fecha actual en zona horaria NBA
    hoy = datetime.now(ZONA_HORARIA_NBA).date()
    print(f"📅 Fecha actual NBA: {hoy}")

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        # Configurar la zona horaria de la sesión para consistencia
        with conn.cursor() as cursor:
            cursor.execute("SET TIMEZONE = 'America/New_York'")
        conn.commit()
        with conn.cursor() as cursor:
            temporada = obtener_temporada_activa(cursor)
            if not temporada:
                raise RuntimeError("No hay temporada activa en la BD")

            temporada_id = str(temporada["id"])
            print(f"📅 Temporada activa: {temporada['nombre']}")

            for i in range(dias + 1):
                fecha = hoy + timedelta(days=i)
                stats["dias_procesados"] += 1

                try:
                    eventos = fetch_scoreboard(fecha)
                    print(f"  📅 {fecha} ({i} días desde hoy): {len(eventos)} eventos")

                    for evento in eventos:
                        stats["eventos_encontrados"] += 1

                        parsed = parse_evento_espn(evento)
                        if not parsed:
                            continue

                        if parsed["completado"]:
                            continue

                        home_id = obtener_equipo_id(cursor, parsed["home_team"], parsed["home_abbr"])
                        away_id = obtener_equipo_id(cursor, parsed["away_team"], parsed["away_abbr"])

                        if not home_id or not away_id:
                            stats["equipos_no_encontrados"] += 1
                            print(f"    ⚠️ Equipo no encontrado: {parsed['home_abbr']} vs {parsed['away_abbr']}")
                            continue

                        insertado = upsert_partido_futuro(
                            cursor,
                            fecha_partido=parsed["fecha_partido"],
                            temporada_id=temporada_id,
                            espn_game_id=parsed["espn_game_id"],
                            equipo_local_id=home_id,
                            equipo_visitante_id=away_id,
                        )

                        if insertado:
                            stats["insertados"] += 1
                            print(f"    ✅ {parsed['away_abbr']} @ {parsed['home_abbr']} (ESPN ID: {parsed['espn_game_id']}, Fecha BD: {parsed['fecha_partido']})")
                        else:
                            stats["ya_existian"] += 1

                    conn.commit()

                except Exception as exc:
                    conn.rollback()
                    stats["errores"] += 1
                    print(f"    ❌ Error en {fecha}: {exc}")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza partidos futuros desde ESPN")
    parser.add_argument("--days", type=int, default=14, help="Días hacia adelante (default: 14)")
    args = parser.parse_args()

    print("=" * 60)
    print("🏀 SINCRONIZADOR DE PARTIDOS FUTUROS")
    print("=" * 60)
    print()

    try:
        stats = sincronizar_partidos_futuros(dias=args.days)

        print()
        print("=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        print(f"  Días procesados:        {stats['dias_procesados']}")
        print(f"  Eventos encontrados:    {stats['eventos_encontrados']}")
        print(f"  Partidos insertados:    {stats['insertados']}")
        print(f"  Ya existían:            {stats['ya_existian']}")
        print(f"  Equipos no encontrados: {stats['equipos_no_encontrados']}")
        print(f"  Errores:                {stats['errores']}")

        if stats["insertados"] > 0:
            print()
            print("✅ ¡Ahora el SelectorPartido debería mostrar partidos!")

    except Exception as exc:
        print(f"❌ Error fatal: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()