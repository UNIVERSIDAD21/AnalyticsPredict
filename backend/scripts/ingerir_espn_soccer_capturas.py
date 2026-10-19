"""Ingiere lotes ESPN Soccer ya auditados en capturas append-only separadas.

Sin ``--aplicar`` solo valida archivos. No enlaza clubes/temporadas Sofascore ni
modifica ``partidos_futbol``. Lotes erróneos detienen toda la transacción.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from scripts.auditar_fuente_espn_soccer import LIGAS, FuenteNoDisponible, _instante_utc


BACKEND = Path(__file__).resolve().parents[1]
MIGRACION = BACKEND / "migrations/2026-10-06_capturas_espn_soccer.sql"


def _digest(objeto: Any) -> str:
    return hashlib.sha256(json.dumps(objeto, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _sha256(valor: Any) -> bool:
    return isinstance(valor, str) and re.fullmatch(r"[0-9a-f]{64}", valor) is not None


def validar_lote(datos: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(datos, dict) or datos.get("fuente") != "ESPN_SOCCER":
        raise ValueError("Fuente distinta de ESPN_SOCCER")
    liga, mes = datos.get("liga"), datos.get("mes")
    if (liga not in LIGAS.values() or not isinstance(mes, str)
            or re.fullmatch(r"[0-9]{6}", mes) is None):
        raise ValueError("Liga o mes inválido")
    if not 1 <= int(mes[4:]) <= 12 or int(mes[:4]) == 0:
        raise ValueError("Mes inválido")
    observado = _instante_utc(datos.get("observado_en"))
    if datetime.fromisoformat(observado) > datetime.now(timezone.utc):
        raise ValueError("Observación futura")
    eventos = datos.get("eventos")
    if (not isinstance(eventos, list) or type(datos.get("n_eventos")) is not int
            or len(eventos) != datos["n_eventos"]):
        raise ValueError("Conteo de eventos incongruente")
    if len(eventos) >= 500:
        raise ValueError("Lote potencialmente truncado")
    finales = 0
    normalizados = []
    ids = set()
    for evento in eventos:
        if not isinstance(evento, dict) or evento.get("fuente") != "ESPN_SOCCER" or evento.get("liga") != liga:
            raise ValueError("Evento de otra fuente/liga")
        evento = evento.copy()
        for campo in ("id_fuente", "local_id_fuente", "visitante_id_fuente",
                      "local_nombre", "visitante_nombre", "estado_fuente"):
            valor = evento.get(campo)
            if not isinstance(valor, str) or not valor.strip() or valor != valor.strip():
                raise ValueError("Identidad de evento/equipos incompleta")
        if evento["id_fuente"] in ids:
            raise ValueError("ID repetido en lote")
        ids.add(evento["id_fuente"])
        if evento["local_id_fuente"] == evento["visitante_id_fuente"]:
            raise ValueError("Equipos idénticos")
        instante = _instante_utc(evento.get("inicio_utc"))
        evento["inicio_utc"] = instante
        if instante[:7] != mes[:4] + "-" + mes[4:]:
            raise ValueError("Evento fuera del mes UTC acreditado")
        final = evento.get("final_acreditado")
        if not isinstance(final, bool):
            raise ValueError("Finalidad ambigua")
        if final != (evento["estado_fuente"] in {
                "STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FINAL_AET", "STATUS_FINAL_PEN"}):
            raise ValueError("Finalidad incompatible con estado fuente")
        if final and datetime.fromisoformat(instante) > datetime.fromisoformat(observado):
            raise ValueError("Final posterior a su observación")
        goles = (evento.get("local_goles"), evento.get("visitante_goles"))
        if final:
            finales += 1
            if any(type(n) is not int or n < 0 for n in goles):
                raise ValueError("Final sin goles completos")
        elif any(n is not None for n in goles):
            raise ValueError("Programado con marcador imputado")
        for campo in ("corners", "disparos", "disparos_arco"):
            completo = evento.get(f"{campo}_completos")
            valores = (evento.get(f"local_{campo}"), evento.get(f"visitante_{campo}"))
            if completo is True and any(type(n) is not int or n < 0 for n in valores):
                raise ValueError(f"{campo} marcado completo sin ambos equipos")
            if completo is not True and any(n is not None for n in valores):
                raise ValueError(f"{campo} parcial no puede publicarse")
            if completo is not None and type(completo) is not bool:
                raise ValueError(f"{campo} tiene cobertura ambigua")
            if completo is True and (not final or not _sha256(evento.get("sha256_boxscore"))):
                raise ValueError(f"{campo} sin final o hash de boxscore")
            evento[f"{campo}_completos"] = completo is True
            for lado in ("local", "visitante"):
                evento.setdefault(f"{lado}_{campo}", None)
        normalizados.append(evento)
    if type(datos.get("n_finales")) is not int or finales != datos["n_finales"]:
        raise ValueError("Conteo de finales incongruente")
    estado = "NO_DATA" if not eventos else "OK"
    if datos.get("estado") != estado:
        raise ValueError("Estado NO_DATA/OK incongruente")
    digest = datos.get("sha256_scoreboard")
    if not _sha256(digest):
        raise ValueError("SHA-256 scoreboard ausente")
    normalizados.sort(key=lambda e: e["id_fuente"])
    lote = {"fuente": "ESPN_SOCCER", "liga": liga, "mes": mes, "estado": estado,
            "observado_en": observado, "n_eventos": len(eventos),
            "n_finales": finales, "sha256_scoreboard": digest, "eventos": normalizados}
    return {**lote, "sha256_lote": _digest(lote)}


def aplicar_lotes(conn, lotes: list[dict[str, Any]]) -> tuple[int, int]:
    """DML atómico e idempotente; snapshot distinto conserva nueva revisión."""
    lotes = [validar_lote(lote) for lote in lotes]
    nuevos_lotes = nuevos_eventos = 0
    with conn.transaction(), conn.cursor() as cursor:
        for lote in lotes:
            cursor.execute("""
                INSERT INTO capturas_espn_soccer_lotes
                    (liga, mes, estado, n_eventos, n_finales, sha256_scoreboard, sha256_lote, observado_en)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (liga, mes, sha256_lote) DO NOTHING
                RETURNING id
            """, tuple(lote[k] for k in ("liga", "mes", "estado", "n_eventos", "n_finales",
                                         "sha256_scoreboard", "sha256_lote", "observado_en")))
            fila = cursor.fetchone()
            if fila is None:
                continue
            nuevos_lotes += 1
            for evento in lote["eventos"]:
                cursor.execute("""
                    INSERT INTO capturas_espn_soccer_eventos
                        (lote_id, liga, id_fuente, inicio_utc, final_acreditado, sha256_evento, evento)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (fila[0], lote["liga"], evento["id_fuente"],
                      datetime.fromisoformat(evento["inicio_utc"]), evento["final_acreditado"],
                      _digest(evento), Jsonb(evento)))
                nuevos_eventos += cursor.fetchone() is not None
    return nuevos_lotes, nuevos_eventos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archivo", action="append", required=True, type=Path,
                        help="JSON auditado, fuera del repositorio; repetir para varios lotes")
    parser.add_argument("--aplicar", action="store_true", help="Ejecutar DML transaccional explícito")
    args = parser.parse_args()
    try:
        lotes = [validar_lote(json.loads(path.read_text(encoding="utf-8"))) for path in args.archivo]
    except (ValueError, OSError, FuenteNoDisponible, KeyError) as exc:
        parser.error(f"Lote inválido: {exc}")
    print(json.dumps({"lotes": len(lotes), "eventos": sum(x["n_eventos"] for x in lotes),
                      "finales": sum(x["n_finales"] for x in lotes), "modo": "aplicar" if args.aplicar else "validar"}))
    if not args.aplicar:
        return 0
    from dotenv import load_dotenv
    import os
    import psycopg
    load_dotenv(BACKEND / ".env", override=False)
    if not os.getenv("DATABASE_URL"):
        parser.error("DATABASE_URL de AnalyticsPredict ausente")
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=8) as conn:
        if conn.execute("SELECT to_regclass('public.capturas_espn_soccer_lotes')").fetchone()[0] is None:
            raise RuntimeError(f"Aplicar primero {MIGRACION.name}")
        nuevos_lotes, nuevos_eventos = aplicar_lotes(conn, lotes)
    print(json.dumps({"lotes_nuevos": nuevos_lotes, "eventos_nuevos": nuevos_eventos}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
