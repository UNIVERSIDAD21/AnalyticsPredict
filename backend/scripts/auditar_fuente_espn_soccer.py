"""Probe read-only de calendario/outcomes ESPN Soccer; no ingesta ni DML.

La respuesta 200 sin eventos significa NO_DATA solo para ese mes/liga. HTTP 403,
JSON roto o lote potencialmente truncado significan SOURCE_UNAVAILABLE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LIGAS = {"premier": "eng.1", "laliga": "esp.1", "seriea": "ita.1",
          "bundesliga": "ger.1", "ligue1": "fra.1"}
LIMITE = 500


class FuenteNoDisponible(Exception):
    """La fuente no permitió un lote completo y verificable."""


def _entero_no_negativo(valor: Any) -> int | None:
    if valor is None or isinstance(valor, bool):
        return None
    try:
        n = int(valor)
        return n if n >= 0 and str(valor).strip() == str(n) else None
    except (TypeError, ValueError):
        return None


def _instante_utc(valor: Any) -> str:
    if not isinstance(valor, str):
        raise FuenteNoDisponible("Evento sin fecha ISO")
    try:
        instante = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FuenteNoDisponible("Fecha de evento inválida") from exc
    if instante.tzinfo is None:
        raise FuenteNoDisponible("Fecha de evento sin zona horaria")
    return instante.astimezone(timezone.utc).isoformat()


def interpretar_evento(evento: dict[str, Any], liga: str) -> dict[str, Any]:
    """Conserva 0 reales; nunca convierte un programado en outcome."""
    if not isinstance(evento, dict) or not evento.get("id"):
        raise FuenteNoDisponible("Evento sin ID")
    competiciones = evento.get("competitions")
    if not isinstance(competiciones, list) or len(competiciones) != 1:
        raise FuenteNoDisponible("Competición de evento ambigua")
    competidores = competiciones[0].get("competitors")
    if not isinstance(competidores, list) or len(competidores) != 2:
        raise FuenteNoDisponible("Local/visitante incompletos")
    por_lado = {item.get("homeAway"): item for item in competidores}
    if set(por_lado) != {"home", "away"}:
        raise FuenteNoDisponible("Local/visitante ambiguos")
    estado = evento.get("status", {}).get("type", {})
    final = estado.get("completed") is True and estado.get("name") in {"STATUS_FULL_TIME", "STATUS_FINAL"}
    salida = {"fuente": "ESPN_SOCCER", "liga": liga, "id_fuente": str(evento["id"]),
              "inicio_utc": _instante_utc(evento.get("date")), "estado_fuente": estado.get("name"),
              "final_acreditado": final}
    for lado, etiqueta in (("home", "local"), ("away", "visitante")):
        item = por_lado[lado]
        equipo = item.get("team") or {}
        if not equipo.get("id") or not equipo.get("displayName"):
            raise FuenteNoDisponible("Identidad de equipo incompleta")
        salida[f"{etiqueta}_id_fuente"] = str(equipo["id"])
        salida[f"{etiqueta}_nombre"] = str(equipo["displayName"])
        goles = _entero_no_negativo(item.get("score")) if final else None
        if final and goles is None:
            raise FuenteNoDisponible("Final sin marcador numérico completo")
        salida[f"{etiqueta}_goles"] = goles
    return salida


def interpretar_estadisticas(payload: dict[str, Any], evento: dict[str, Any]) -> dict[str, Any]:
    """Corners/tiros solo cuando ambos equipos aportan el campo; faltante es NULL."""
    equipos = (payload.get("boxscore") or {}).get("teams")
    if not isinstance(equipos, list) or len(equipos) != 2:
        raise FuenteNoDisponible("Boxscore incompleto")
    por_id = {}
    for item in equipos:
        equipo_id = str((item.get("team") or {}).get("id") or "")
        if not equipo_id or equipo_id in por_id:
            raise FuenteNoDisponible("Identidad de boxscore ambigua")
        por_id[equipo_id] = {s.get("name"): _entero_no_negativo(s.get("displayValue"))
                             for s in item.get("statistics", []) if isinstance(s, dict)}
    salida = {}
    for campo, clave in (("corners", "wonCorners"), ("disparos", "totalShots"),
                         ("disparos_arco", "shotsOnTarget")):
        valores = [por_id.get(evento[f"{lado}_id_fuente"], {}).get(clave)
                   for lado in ("local", "visitante")]
        salida[f"{campo}_completos"] = all(v is not None for v in valores)
        salida[f"local_{campo}"] = valores[0] if salida[f"{campo}_completos"] else None
        salida[f"visitante_{campo}"] = valores[1] if salida[f"{campo}_completos"] else None
    return salida


def _obtener_json(session: requests.Session, url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        respuesta = session.get(url, params=params, timeout=(5, 10))
    except requests.RequestException as exc:
        raise FuenteNoDisponible(type(exc).__name__) from exc
    if respuesta.status_code != 200:
        # Incluye 403: no renovar cookies, impersonar ni reintentar.
        raise FuenteNoDisponible(f"HTTP {respuesta.status_code}")
    try:
        payload = respuesta.json()
    except ValueError as exc:
        raise FuenteNoDisponible("JSON inválido") from exc
    if not isinstance(payload, dict):
        raise FuenteNoDisponible("Contrato JSON inválido")
    return payload


def auditar_mes(liga: str, mes: str, max_finales: int = 0,
                session: requests.Session | None = None) -> dict[str, Any]:
    if liga not in LIGAS or len(mes) != 6 or not mes.isdigit() or not 1 <= int(mes[4:]) <= 12:
        raise ValueError("Liga o mes YYYYMM inválido")
    s = session or requests.Session()
    s.headers.update({"User-Agent": "AnalyticsPredict-quality-probe/1.0", "Accept": "application/json"})
    codigo = LIGAS[liga]
    payload = _obtener_json(s, f"{BASE}/{codigo}/scoreboard", {"dates": mes, "limit": LIMITE})
    eventos = payload.get("events")
    if not isinstance(eventos, list) or len(eventos) >= LIMITE:
        raise FuenteNoDisponible("Lista ausente o potencialmente truncada")
    interpretados = [interpretar_evento(e, codigo) for e in eventos]
    if len({e["id_fuente"] for e in interpretados}) != len(interpretados):
        raise FuenteNoDisponible("IDs duplicados en lote")
    finales = [e for e in interpretados if e["final_acreditado"]]
    for evento in finales[:max_finales]:
        boxscore = _obtener_json(s, f"{BASE}/{codigo}/summary", {"event": evento["id_fuente"]})
        evento.update(interpretar_estadisticas(boxscore, evento))
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"estado": "NO_DATA" if not eventos else "OK", "fuente": "ESPN_SOCCER",
            "liga": codigo, "mes": mes, "n_eventos": len(eventos), "n_finales": len(finales),
            "n_resumenes_consultados": min(len(finales), max_finales),
            "sha256_scoreboard": digest, "eventos": interpretados}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--liga", required=True, choices=sorted(LIGAS))
    parser.add_argument("--mes", required=True, help="YYYYMM")
    parser.add_argument("--max-finales", type=int, default=0)
    parser.add_argument("--salida", type=Path, help="JSON local de evidencia, fuera del repo")
    args = parser.parse_args()
    if args.max_finales < 0:
        parser.error("--max-finales debe ser no negativo")
    try:
        informe = auditar_mes(args.liga, args.mes, args.max_finales)
    except (FuenteNoDisponible, ValueError) as exc:
        print(json.dumps({"estado": "SOURCE_UNAVAILABLE", "motivo": str(exc)}))
        return 1
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in informe.items() if k != "eventos"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
