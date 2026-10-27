from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from ingesta_futbol_americas import (
    cargar_lote, competicion_fila, digest, instante, preparar, temporada_fila, validar_fila,
)


def fila(**cambios):
    r = {"contrato": "espn_latam_v1", "fuente": "ESPN", "codigo_liga": "arg.1", "source_game_id": "1234",
         "temporada": 2020, "temporada_nombre_fuente": "2020 Argentine Liga Profesional",
         "fase_fuente": "regular-season", "fase": "REG", "season_type_fuente": "777", "estado": "FINALIZADO", "final_completo": True,
         "estadisticas_completas": True, "inicio_utc": "2020-03-10T23:00:00+00:00",
         "inicio_colombia": "2020-03-10T18:00:00-05:00", "local_id_fuente": "100", "visitante_id_fuente": "200",
         "local_nombre": "Equipo A", "visitante_nombre": "Equipo B", "hubo_prorroga": False, "hubo_penales": False,
         "url_fuente": "https://www.espn.com/soccer/match/_/gameId/1234", "evidencia": [
             {"observado_utc": "2026-10-26T16:00:00+00:00", "sha256": "a" * 64}]}
    for l in ("local", "visitante"):
        r.update({l + "_goles": 1, l + "_goles_90": 1, l + "_goles_1t": 0, l + "_goles_2t": 1,
                  l + "_goles_et": 0, l + "_penales": None, l + "_corners": 0,
                  l + "_tiros_totales": 10, l + "_tiros_al_arco": 3})
    return {**r, **cambios}


@pytest.mark.parametrize("campos,codigo", [
    ({}, "ARG_PRIMERA"),
    ({"fase_fuente": "copa-diego-armando-maradona---fase-campeon-final"}, "ARG_MARADONA"),
    ({"codigo_liga": "arg.copa_lpf"}, "ARG_COPA_LPF"),
    ({"codigo_liga": "arg.copa_de_la_superliga"}, "ARG_SUPERLIGA"),
    ({"codigo_liga": "usa.1", "fase_fuente": "all-star-game"}, None),
    ({"codigo_liga": "usa.1", "fase_fuente": "mls-is-back---final"}, "USA_MLS_BACK"),
    ({"codigo_liga": "bra.1"}, "BRA_SERIEA"),
    ({"codigo_liga": "col.1"}, "COL_PRIMERAA"),
])
def test_competicion_no_equivale_al_feed(campos, codigo):
    assert competicion_fila(fila(**campos)) == codigo


def test_temporada_fuente_no_se_deduce_de_la_fecha():
    assert temporada_fila(fila(temporada=2019, temporada_nombre_fuente="Superliga Argentina 2019-20"), "ARG_PRIMERA") == ("2019-2020", 2019, 2020)
    assert temporada_fila(fila(codigo_liga="bra.1", inicio_utc="2021-01-10T23:00:00Z"), "BRA_SERIEA") == ("2020", 2020, 2020)


@pytest.mark.parametrize("campos", [
    {"local_goles": -1}, {"local_goles": True}, {"local_goles": None},
    {"local_tiros_al_arco": 20}, {"local_goles_2t": 5},
    {"local_goles_et": 2}, {"local_id_fuente": "200"},
    {"inicio_utc": "2020-03-10T23:00:00"}, {"codigo_liga": "eng.1"},
    {"hubo_penales": True, "local_penales": 5, "visitante_penales": 5},
])
def test_adversariales_se_apartan(campos):
    with pytest.raises(ValueError):
        validar_fila(fila(**campos))


def test_cero_se_conserva_null_no_invalida_goles_y_tiempos_ausentes_no_se_inventan():
    r = fila(local_corners=None, local_goles_1t=None, local_goles_2t=None, estadisticas_completas=False)
    assert validar_fila(r) == "ARG_PRIMERA"
    assert r["visitante_corners"] == 0 and r["local_goles_1t"] is None


def test_preparacion_deduplica_agregado_y_torneos_sin_mutar_originales():
    r = fila(); antes = deepcopy(r)
    lotes = [{"filas": [r], "reporte": "/tmp/reporte", "sha256": "b" * 64}] * 2
    p = preparar(lotes, desde_fixtures=instante("2026-10-26T05:00:00Z"), hasta_fixtures=instante("2026-12-27T05:00:00Z"))
    assert len(p["filas"]) == 1 and p["conteos"][0]["duplicados_identicos"] == 1 and r == antes
    lotes[1] = {**lotes[0], "filas": [fila(local_goles=2)]}
    with pytest.raises(ValueError, match="contradictorias"):
        preparar(lotes, desde_fixtures=instante("2026-10-26T05:00:00Z"), hasta_fixtures=instante("2026-12-27T05:00:00Z"))


def test_no_importa_cancelados_antiguos_ni_all_star():
    rows = [fila(), fila(source_game_id="1235", codigo_liga="usa.1", fase_fuente="all-star-game")]
    p = preparar([{"filas": rows, "reporte": "/tmp/r", "sha256": "b" * 64}],
                 desde_fixtures=instante("2026-10-26T05:00:00Z"), hasta_fixtures=instante("2026-12-27T05:00:00Z"))
    assert len(p["filas"]) == 1 and p["apartados"][0]["motivo"] == "ALL_STAR_FUERA_DE_COMPETICION"


def test_lote_mutable_se_rechaza(tmp_path):
    path = tmp_path / "reporte.json"
    path.write_text(json.dumps({"estado": "EN_CURSO"}))
    with pytest.raises(ValueError, match="mutable"):
        cargar_lote(path)


def test_fixture_no_contiene_outcomes_y_limite_cot_inclusivo():
    r = fila(estado="PROGRAMADO", final_completo=False, local_goles=None, visitante_goles=None,
             estadisticas_completas=False, inicio_utc="2026-12-27T04:59:00Z", inicio_colombia="2026-12-26T23:59:00-05:00")
    from ingesta_futbol_americas import NUMERICOS
    for l in ("local", "visitante"):
        for f in NUMERICOS:
            r[l + "_" + f] = None
    lote = {"filas": [r], "reporte": "/tmp/r", "sha256": "b" * 64}
    p = preparar([lote], desde_fixtures=instante("2026-10-26T05:00:00Z"), hasta_fixtures=instante("2026-12-27T05:00:00Z"))
    assert len(p["filas"]) == 1
    r["local_goles"] = 0
    p = preparar([lote], desde_fixtures=instante("2026-10-26T05:00:00Z"), hasta_fixtures=instante("2026-12-27T05:00:00Z"))
    assert not p["filas"] and "No final" in p["apartados"][0]["motivo"]
