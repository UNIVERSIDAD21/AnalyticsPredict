from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scraper_partidos_futuros.py"
SPEC = importlib.util.spec_from_file_location("scraper_partidos_futuros", SCRIPT)
ingesta = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ingesta)


def fixture_event(**changes):
    event = {
        "id": "401909834",
        "date_utc": "2026-10-21T23:00:00Z",
        "home": {"abbr": "ORL", "name": "Orlando Magic"},
        "away": {"abbr": "ATL", "name": "Atlanta Hawks"},
        "season_type": 2,
        "state": "pre",
        "status": "STATUS_SCHEDULED",
        "completed": False,
    }
    event.update(changes)
    return event


def test_parse_fixture_uses_new_york_calendar_date_and_regular_phase():
    parsed = ingesta.parse_event(fixture_event())
    assert parsed is not None
    assert parsed["fecha_partido"] == "2026-10-21"
    assert parsed["tipo_partido"] == "REG"
    assert parsed["home_abbr"] == "ORL"


def test_parse_utc_event_that_crosses_midnight_uses_previous_new_york_date():
    parsed = ingesta.parse_event(fixture_event(date_utc="2026-10-21T01:50:00Z"))
    assert parsed is not None
    assert parsed["fecha_partido"] == "2026-10-20"


def test_parse_raw_espn_response_shape():
    event = {
        "id": "raw-1",
        "date": "2026-10-21T23:00:00Z",
        "season": {"type": 2},
        "competitions": [{
            "status": {"type": {"state": "pre", "completed": False}},
            "competitors": [
                {"homeAway": "home", "team": {"abbreviation": "ORL", "displayName": "Orlando Magic"}},
                {"homeAway": "away", "team": {"abbreviation": "ATL", "displayName": "Atlanta Hawks"}},
            ],
        }],
    }
    parsed = ingesta.parse_event(event)
    assert parsed is not None
    assert parsed["espn_game_id"] == "raw-1"
    assert parsed["tipo_partido"] == "REG"


@pytest.mark.parametrize("event", [
    fixture_event(state="in"),
    fixture_event(state="post", completed=True),
])
def test_live_or_completed_event_is_not_imported(event):
    assert ingesta.parse_event(event) is None


def test_unknown_state_fails_closed():
    with pytest.raises(ValueError, match="estado ESPN no reconocido"):
        ingesta.parse_event(fixture_event(state="delayed"))


def test_unknown_season_type_fails_closed():
    with pytest.raises(ValueError, match="fase ESPN no permitida"):
        ingesta.parse_event(fixture_event(season_type=99))


def test_normalize_deduplicates_identical_event_ids():
    result = ingesta.normalize_events([fixture_event(), fixture_event()])
    assert len(result) == 1


def test_normalize_rejects_id_payload_mismatch_and_natural_key_collision():
    with pytest.raises(ValueError, match="payload distinto"):
        ingesta.normalize_events([fixture_event(), fixture_event(home={"abbr": "MIA", "name": "Miami Heat"})])

    other_id = fixture_event(id="another-id")
    with pytest.raises(ValueError, match="llave natural duplicada"):
        ingesta.normalize_events([fixture_event(), other_id])


def test_attach_db_ids_requires_exact_active_team_abbreviations():
    context = {"competicion_id": "comp", "temporada_id": "season", "temporada_nombre": "2026-27",
               "equipos_por_abrev": {"ORL": "home-id", "ATL": "away-id"},
               "equipos_por_nombre": {"orlando magic": "home-id", "atlanta hawks": "away-id"}}
    parsed = ingesta.normalize_events([fixture_event()])
    attached = ingesta.attach_db_ids(parsed, context)
    assert attached[0]["equipo_local_id"] == "home-id"
    assert attached[0]["source_game_id"] == attached[0]["espn_game_id"]

    context["equipos_por_abrev"].pop("ATL")
    context["equipos_por_nombre"].pop("atlanta hawks")
    with pytest.raises(ValueError, match="nombre completo ESPN no coincide"):
        ingesta.attach_db_ids(parsed, context)


def test_exact_full_name_allows_known_espn_abbreviation_variant():
    event = fixture_event(home={"abbr": "GS", "name": "Golden State Warriors"})
    context = {"competicion_id": "comp", "temporada_id": "season", "temporada_nombre": "2026-27",
               "equipos_por_abrev": {"GSW": "warriors-id", "ATL": "hawks-id"},
               "equipos_por_nombre": {"golden state warriors": "warriors-id", "atlanta hawks": "hawks-id"}}
    attached = ingesta.attach_db_ids(ingesta.normalize_events([event]), context)
    assert attached[0]["equipo_local_id"] == "warriors-id"


def test_full_name_and_known_abbreviation_must_not_disagree():
    event = fixture_event(home={"abbr": "BOS", "name": "Golden State Warriors"})
    context = {"competicion_id": "comp", "temporada_id": "season", "temporada_nombre": "2026-27",
               "equipos_por_abrev": {"BOS": "celtics-id", "ATL": "hawks-id"},
               "equipos_por_nombre": {"golden state warriors": "warriors-id", "atlanta hawks": "hawks-id"}}
    with pytest.raises(ValueError, match="abreviatura/nombre local ESPN discrepan"):
        ingesta.attach_db_ids(ingesta.normalize_events([event]), context)


def test_fetch_events_preserves_raw_responses_and_hashes(monkeypatch):
    event = fixture_event()
    body = json.dumps({"events": [event]}).encode("utf-8")

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, _url, params, timeout):
            assert params["limit"] == 500
            assert timeout == (10, 30)
            return SimpleNamespace(
                status_code=200,
                headers={"Date": "Tue, 21 Oct 2026 12:00:00 GMT", "Content-Type": "application/json"},
                content=body,
                url=f"https://example.test/?dates={params['dates']}",
                raise_for_status=lambda: None,
            )

    monkeypatch.setattr(ingesta.requests, "Session", FakeSession)
    monkeypatch.setattr(ingesta.time, "sleep", lambda _seconds: None)
    events, capture = ingesta.fetch_events(ingesta.date(2026, 10, 21), ingesta.date(2026, 10, 21))
    assert events == [event]
    assert capture["request_count"] == 1
    response = capture["responses"][0]
    assert response["body_text_utf8"] == body.decode("utf-8")
    assert response["body_sha256"] == hashlib.sha256(body).hexdigest()
    assert response["http_status"] == 200


def test_fetch_events_aborts_potentially_truncated_response(monkeypatch):
    body = json.dumps({"events": [{}] * 500}).encode("utf-8")

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, *_args, **_kwargs):
            return SimpleNamespace(
                status_code=200,
                headers={},
                content=body,
                url="https://example.test/",
                raise_for_status=lambda: None,
            )

    monkeypatch.setattr(ingesta.requests, "Session", FakeSession)
    with pytest.raises(ValueError, match="posible truncamiento"):
        ingesta.fetch_events(ingesta.date(2026, 10, 21), ingesta.date(2026, 10, 21))
