from copy import deepcopy

import numpy as np
import pytest

from motor.contraccion_wnba_experimental import medias_contraidas, delta_emparejado, validar_publicacion
from motor.wnba import medias


def modelo():
    return {"entidades": {"a": 0, "b": 1}, "efectivos": {"a": 8, "b": 24},
            "coeficientes": [[20] * 4, [2] * 4, [4] * 4, [8] * 4, [-2] * 4, [-6] * 4]}


def test_k0_reproduce_conocidos_y_no_muta_coeficientes():
    m = modelo()
    antes = deepcopy(m)
    filas = [{"local_id": "a", "visitante_id": "b"}, {"local_id": "b", "visitante_id": "a"}]
    np.testing.assert_array_equal(medias_contraidas(m, filas, 0), medias(m, filas))
    assert m == antes
    assert medias_contraidas(m, filas, 8)[0, 0] == 22 + 4 * .5 - 6 * .75


def test_equipo_nuevo_no_imputa_historial_ni_utiliza_outcomes_del_evento():
    m = modelo()
    r = {"local_id": "nuevo", "visitante_id": "otro", "y": [0] * 8}
    np.testing.assert_array_equal(medias_contraidas(m, [r], 8), [[22] * 4 + [20] * 4])
    p = medias_contraidas(m, [r], 8)
    r.update(y=[200] * 8, fecha="2099-01-01")
    np.testing.assert_array_equal(medias_contraidas(m, [r], 8), p)
    with pytest.raises(ValueError):
        medias_contraidas(m, [r], -1)


def test_bootstrap_empareja_partidos_y_agrupa_dias_no_filas_de_cuarto():
    filas = [{"fecha": f"2025-01-{i // 2 + 1:02d}", "y": [0] * 8} for i in range(10)]
    r = delta_emparejado(filas, np.ones((10, 8)), np.zeros((10, 8)))
    assert r["COMPLETO"]["n"] == 10
    assert r["COMPLETO"]["dias"] == 5
    assert r["COMPLETO"]["delta_mae"] == 8
    assert r["COMPLETO"]["ic95_dias"] == [8, 8]


def test_snapshot_alterado_se_rechaza_sin_sustituir_cohorte():
    with pytest.raises(ValueError, match="no íntegra"):
        validar_publicacion({"formato": "otro", "datos": [], "dataset_sha256": "falso"})
