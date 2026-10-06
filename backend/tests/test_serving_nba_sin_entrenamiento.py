"""El arranque/GET nunca entrenan; el entrenamiento NBA es explícito y trazable."""

import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient

import app as app_modulo
from scripts import entrenar_modelo_nba_explicito as cli_entrenamiento
from motor_autoentrenamiento.artefacto_nba import cargar_artefacto, guardar_artefacto
from motor_autoentrenamiento.entrenador_bd import EntrenadorBD
from motor_autoentrenamiento.gestor_modelo import GestorModelo


def _datos_modelo():
    return {
        "alpha": 5.0,
        "entidad_a_indice": {"local": 0, "visitante": 1},
        "pesos_equipo": np.zeros((6, 4)),
        "pesos_rival": np.ones((6, 4)),
        "desviacion_equipo": np.ones(4),
        "desviacion_rival": np.ones(4),
        "modelo_version_id": 17,
        "metricas": {
            "modelo_version_id": 17,
            "modelo_version": 5,
            "hash_datos": "snapshot-prueba",
            "partidos_entrenamiento": 23,
            "fecha_min_entrenamiento": "2026-01-01",
            "fecha_max_entrenamiento": "2026-02-01",
            "fecha_entrenamiento": "2026-02-02T10:00:00+00:00",
            "fit_started_at": "2026-02-02T09:59:00+00:00",
            "fit_completed_at": "2026-02-02T09:59:30+00:00",
            "training_data_latest_game_date": "2026-02-01",
        },
    }


def test_artefacto_versionado_se_guarda_fuera_de_la_bd_y_carga_sin_pickle(tmp_path):
    ruta = tmp_path / "modelo.npz"
    guardar_artefacto(_datos_modelo(), ruta)
    assert os.stat(ruta).st_mode & 0o777 == 0o600
    recuperado = cargar_artefacto(ruta)
    assert recuperado["modelo_version_id"] == 17
    assert recuperado["metricas"]["modelo_version"] == 5
    assert recuperado["metricas"]["hash_datos"] == "snapshot-prueba"
    assert recuperado["fecha_entrenamiento"] == "2026-02-02T10:00:00+00:00"
    assert recuperado["metricas"]["fit_completed_at"] == "2026-02-02T09:59:30+00:00"
    assert np.array_equal(recuperado["pesos_rival"], np.ones((6, 4)))


def test_startup_y_get_sin_artefacto_no_entrenan_ni_abren_bd(monkeypatch, tmp_path):
    monkeypatch.setenv("ANALYTICSPREDICT_MODELO_NBA_ACTIVO", str(tmp_path / "ausente.npz"))
    GestorModelo.reiniciar()
    monkeypatch.setattr(EntrenadorBD, "entrenar", lambda _self: (_ for _ in ()).throw(AssertionError("entrenó")))
    monkeypatch.setattr("db.obtener_pool", lambda: (_ for _ in ()).throw(AssertionError("abrió BD")))
    monkeypatch.setattr(app_modulo, "cerrar_pool", lambda: None)
    try:
        for _ in range(2):  # dos ciclos equivalentes a startup/reload
            GestorModelo.reiniciar()
            with TestClient(app_modulo.app) as client:
                salud = client.get("/salud")
                estado = client.get("/api/modelo/estado")
                equipos = client.get("/api/modelo/equipos")
                assert salud.status_code == estado.status_code == 200
                assert salud.json()["estado"] == "degradado"
                assert estado.json()["exito"] is False
                assert equipos.status_code == 200 and equipos.json()["exito"] is False
    finally:
        GestorModelo.reiniciar()


def test_reload_carga_version_existente_sin_crear_otra(monkeypatch, tmp_path):
    ruta = tmp_path / "activo.npz"
    guardar_artefacto(_datos_modelo(), ruta)
    monkeypatch.setenv("ANALYTICSPREDICT_MODELO_NBA_ACTIVO", str(ruta))
    monkeypatch.setattr(EntrenadorBD, "entrenar", lambda _self: (_ for _ in ()).throw(AssertionError("entrenó")))
    monkeypatch.setattr("db.obtener_pool", lambda: (_ for _ in ()).throw(AssertionError("abrió BD")))
    monkeypatch.setattr(app_modulo, "cerrar_pool", lambda: None)
    try:
        for _ in range(2):
            GestorModelo.reiniciar()
            with TestClient(app_modulo.app) as client:
                estado = client.get("/api/modelo/estado")
                assert estado.status_code == 200
                assert estado.json()["modelo"]["version"] == 17
                assert estado.json()["modelo"]["fecha_entrenamiento"] == "2026-02-02T10:00:00+00:00"
                recarga = client.post("/api/modelo/cargar")
                assert recarga.status_code == 200
                assert recarga.json()["modelo_version_id"] == 17
    finally:
        GestorModelo.reiniciar()


def test_entrenamiento_explicito_publica_version_real(monkeypatch, tmp_path):
    GestorModelo.reiniciar()
    monkeypatch.setattr(EntrenadorBD, "entrenar", lambda _self: _datos_modelo())
    publicado = []
    monkeypatch.setattr(
        "motor_autoentrenamiento.gestor_modelo.guardar_artefacto",
        lambda datos: publicado.append(datos["modelo_version_id"]) or (tmp_path / "modelo.npz"),
    )
    try:
        gestor = GestorModelo.obtener_instancia(pool=object())
        assert gestor.esta_inicializado is False
        gestor.reentrenar()
        assert gestor.esta_inicializado is True
        assert gestor.modelo.version == 17
        assert publicado == [17]
    finally:
        GestorModelo.reiniciar()


def test_cli_exige_flag_y_solo_entonces_invoca_entrenamiento(monkeypatch):
    llamadas = []
    modelo = SimpleNamespace(
        version=17, cantidad_equipos=2,
        metricas={"hash_datos": "snapshot-prueba"},
        fecha_entrenamiento=SimpleNamespace(isoformat=lambda: "2026-02-02T10:00:00+00:00"),
    )
    gestor = SimpleNamespace(
        reentrenar=lambda: llamadas.append("entrenar"), modelo=modelo,
    )
    monkeypatch.setattr(cli_entrenamiento, "obtener_pool", lambda: object())
    monkeypatch.setattr(cli_entrenamiento.GestorModelo, "obtener_instancia", lambda _pool: gestor)
    monkeypatch.setattr(cli_entrenamiento, "cerrar_pool", lambda: llamadas.append("cerrar"))
    monkeypatch.setattr(cli_entrenamiento, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sys, "argv", ["entrenar_modelo_nba_explicito.py"])
    with pytest.raises(SystemExit) as salida:
        cli_entrenamiento.main()
    assert salida.value.code == 2
    assert llamadas == []
    monkeypatch.setattr(sys, "argv", ["entrenar_modelo_nba_explicito.py", "--entrenar"])
    assert cli_entrenamiento.main() == 0
    assert llamadas == ["entrenar", "cerrar"]
