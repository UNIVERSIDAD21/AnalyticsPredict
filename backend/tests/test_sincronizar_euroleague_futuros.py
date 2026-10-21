from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sincronizar_euroleague_futuros.py"
SPEC = importlib.util.spec_from_file_location("sincronizar_euroleague_futuros", SCRIPT)
assert SPEC is not None
ingesta = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ingesta)


def capture_with_cards(*, reverse_mismatch: bool = False, first_live: bool = False):
    links = []
    lines = ["Games", "Schedule", "2026-27", "Regular season", "30 October 2026", "(10 games)"]
    for number in range(10):
        home = "Anadolu Efes Istanbul" if number % 2 == 0 else "FC Bayern Munich"
        away = "Besiktas Istanbul" if number % 2 == 0 else "Dubai Basketball"
        source_id = 200 + number
        label = f"{away} vs {home}"
        if reverse_mismatch and number == 1:
            label = f"{home} vs {away}"
        lines.append(f"game {label}")
        if number == 0 and first_live:
            lines.extend(["Live Q1", "ARENA SOFIA", home, "(5)", "11", "17", away, "(8)"])
        else:
            lines.extend(["14:30", "MAIN ARENA", home, "(5)", "VS", away, "(8)"])
        links.append({
            "label": label,
            "url": f"https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/a-b/E2026/{source_id}/",
        })
    return {
        "round": 20,
        "source_url": ingesta.SOURCE_PAGE,
        "observed_at_utc": "2026-10-21 16:00:00 UTC",
        "game_links": links,
        "schedule_text": "\n".join(lines),
    }


def test_parse_official_round_assigns_home_away_from_rendered_card(tmp_path):
    path = tmp_path / "round.json"
    path.write_text(json.dumps(capture_with_cards()), encoding="utf-8")
    games, excluded = ingesta.parse_round_capture(path)

    assert len(games) == 10
    assert excluded == []
    assert games[0]["equipo_local_fuente"] == "Anadolu Efes Istanbul"
    assert games[0]["equipo_visitante_fuente"] == "Besiktas Istanbul"
    assert games[0]["source_game_id"] == "E2026/200"
    assert games[0]["fecha_partido"] == "2026-10-30"


def test_live_game_is_recorded_as_excluded_not_fixture(tmp_path):
    path = tmp_path / "round.json"
    path.write_text(json.dumps(capture_with_cards(first_live=True)), encoding="utf-8")
    games, excluded = ingesta.parse_round_capture(path)

    assert len(games) == 9
    assert excluded == [{
        "source_game_id": "E2026/200",
        "label": "Besiktas Istanbul vs Anadolu Efes Istanbul",
        "date": "2026-10-30",
        "status_observed": "Live Q1",
        "reason": "no es una hora de partido programado; excluido del lote PRE",
    }]


def test_link_and_rendered_card_localia_must_match(tmp_path):
    path = tmp_path / "round.json"
    path.write_text(json.dumps(capture_with_cards(reverse_mismatch=True)), encoding="utf-8")
    with pytest.raises(ValueError, match="tarjeta y el enlace discrepan"):
        ingesta.parse_round_capture(path)


def test_team_crosswalk_is_exact_and_attaches_catalogue_ids():
    context = {
        "competition_id": "euro-comp",
        "season_id": "2026-season",
        "teams_by_name": {
            "anadolu efes": "efes-id",
            "besiktas istanbul": "besiktas-id",
        },
    }
    event = {
        "source_game_id": "E2026/64",
        "fecha_partido": "2026-10-22",
        "tipo_partido": "REG",
        "equipo_local_fuente": "Anadolu Efes Istanbul",
        "equipo_visitante_fuente": "Besiktas Istanbul",
    }
    attached = ingesta.attach_db_ids([event], context)[0]
    assert attached["equipo_local_id"] == "efes-id"
    assert attached["equipo_visitante_id"] == "besiktas-id"
    assert attached["source"] == "EUROLEAGUE"

    event["equipo_local_fuente"] = "Anadolu Efes-ish"
    with pytest.raises(ValueError, match="equipo oficial no registrado"):
        ingesta.attach_db_ids([event], context)
