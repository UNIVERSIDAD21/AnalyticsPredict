#!/usr/bin/env python3
"""Probe HTTP read-only de ESPN/Sofascore; salida JSON local, sin ingesta."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import requests


def probar(url: str, clave: str, params: dict[str, str] | None = None) -> dict[str, object]:
    try:
        respuesta = requests.get(url, params=params, timeout=12,
                                 headers={"User-Agent": "AnalyticsPredict-quality-probe/1.0",
                                          "Accept": "application/json"})
        if respuesta.status_code != 200:
            return {"http_status": respuesta.status_code, "json_valido": False}
        payload = respuesta.json()
        return {"http_status": 200, "json_valido": isinstance(payload, dict) and clave in payload}
    except (requests.RequestException, ValueError):
        return {"http_status": None, "json_valido": False}


def main() -> None:
    ayer = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y%m%d")
    salida = {
        "corte_utc": datetime.now(timezone.utc).isoformat(),
        "ESPN": probar("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
                       "events", {"dates": ayer, "limit": "500"}),
        "SOFASCORE": probar("https://www.sofascore.com/api/v1/unique-tournament/8", "uniqueTournament"),
    }
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
