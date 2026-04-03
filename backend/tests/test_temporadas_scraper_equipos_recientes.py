from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import temporadas_pipeline as mod


def test_inferir_anio_fin_temporada_octubre_salta_al_anio_siguiente():
    assert mod.inferir_anio_fin_temporada(date(2025, 10, 5), "REG") == 2026


def test_inferir_anio_fin_temporada_enero_mantiene_anio_actual():
    assert mod.inferir_anio_fin_temporada(date(2026, 1, 10), "REG") == 2026


def test_resolver_temporada_id_evento_prioriza_season_api_y_registra_discrepancia():
    warnings = []
    mapa = {2026: "temp-2026"}

    temporada_id = mod.resolver_temporada_id_evento(
        conexion=None,
        fecha_evento=date(2025, 9, 20),
        season_api=2026,
        tipo_partido="PRE",
        temporada_por_anio_fin=mapa,
        warnings=warnings,
        event_id="evt-1",
        equipo="Lakers",
        asegurar_temporadas_fn=lambda *_args, **_kwargs: {},
        verbose=False,
    )

    assert temporada_id == "temp-2026"
    assert any(w["causa"] == "season_api_difiere_de_fecha" for w in warnings)


def test_resolver_temporada_id_evento_fallback_a_inferida_y_crea_temporada():
    warnings = []
    mapa = {}

    def _fake_asegurar(_conexion, seasons):
        assert seasons == [2026]
        return {2026: "temp-creada-2026"}

    temporada_id = mod.resolver_temporada_id_evento(
        conexion=None,
        fecha_evento=date(2025, 12, 1),
        season_api=None,
        tipo_partido="REG",
        temporada_por_anio_fin=mapa,
        warnings=warnings,
        event_id="evt-2",
        equipo="Celtics",
        asegurar_temporadas_fn=_fake_asegurar,
        verbose=False,
    )

    assert temporada_id == "temp-creada-2026"
    assert mapa[2026] == "temp-creada-2026"
    assert warnings == []


def test_resolver_temporada_id_evento_registra_warning_si_no_hay_temporada():
    warnings = []

    temporada_id = mod.resolver_temporada_id_evento(
        conexion=None,
        fecha_evento=date(2026, 2, 15),
        season_api=2026,
        tipo_partido="REG",
        temporada_por_anio_fin={},
        warnings=warnings,
        event_id="evt-3",
        equipo="Warriors",
        asegurar_temporadas_fn=lambda *_args, **_kwargs: {},
        verbose=False,
    )

    assert temporada_id is None
    assert len(warnings) == 1
    assert warnings[0]["causa"] == "temporada_no_resuelta"
