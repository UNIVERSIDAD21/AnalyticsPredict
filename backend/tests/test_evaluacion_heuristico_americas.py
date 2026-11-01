from datetime import datetime, timedelta, timezone
import math

from scripts.evaluar_heuristico_americas import cohorte, metricas


def test_cohorte_no_divide_kickoffs_simultaneos_en_copas_retiradas():
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    rows = [{"fecha_partido": base + timedelta(days=i), "id": f"{i}-{j}"} for i in range(20) for j in range(2)]
    elegidos = cohorte(rows)
    assert len(elegidos) == 8
    assert all(r["fecha_partido"] >= base + timedelta(days=16) for r in elegidos)


def test_cohorte_reciente_se_fija_sin_mirar_errores():
    rows = [{"fecha_partido": datetime(y,1,1,tzinfo=timezone.utc)} for y in [2023,2024,2025,2026]]
    assert [r["fecha_partido"].year for r in cohorte(rows)] == [2025,2026]


def test_metricas_conocidas_y_sin_muestra_es_nd_no_cero():
    assert metricas([])["mae"] is None
    r = metricas([{"media": 2., "y": 1., "p": .7, "binario": 1}, {"media": 2., "y": 3., "p": .3, "binario": 0}])
    assert r["mae"] == r["rmse"] == 1 and r["sesgo"] == 0
    assert math.isclose(r["brier"], .09) and math.isclose(r["logloss"], -math.log(.7))
