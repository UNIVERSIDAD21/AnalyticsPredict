"""Regresiones nativas con datos sintéticos: no consultan datos deportivos."""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from servicios.locks_archivo import adquirir
from servicios.consulta_local import consultar
from motor_autoentrenamiento.gestor_modelo import ModeloEnMemoria
from motor_autoentrenamiento.artefacto_nba import guardar_artefacto, cargar_artefacto
from api import rutas_local, rutas_analisis
from api.modelos_peticion import PeticionAnalisis
from api.excepciones import ErrorValidacion
from explicabilidad.contrato import construir_contrato


def modelo_sintetico():
    we, wr = np.zeros((6, 4)), np.zeros((6, 4))
    we[0], wr[0] = 25, 20
    return ModeloEnMemoria({
        "alpha": 5, "entidad_a_indice": {"local á": 0, "visita ñ": 1},
        "pesos_equipo": we, "pesos_rival": wr,
        "desviacion_equipo": np.full(4, 2.), "desviacion_rival": np.full(4, 3.),
        "modelo_version_id": 17, "fecha_entrenamiento": "2026-01-02T00:00:00+00:00",
        "metricas": {"hash_datos": "sintetico", "fecha_max_entrenamiento": "2026-01-01"},
    })


def test_lock_excluye_otro_proceso_y_se_libera_al_cerrar(tmp_path):
    path = tmp_path / "exclusión.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    script = '''
import os, sys
from servicios.locks_archivo import adquirir
fd = os.open(sys.argv[1], os.O_RDWR)
try:
    adquirir(fd)
except BlockingIOError:
    sys.exit(23)
finally:
    os.close(fd)
'''
    try:
        adquirir(fd)
        ocupado = subprocess.run([sys.executable, "-c", script, str(path)], cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=15)
        assert ocupado.returncode == 23, ocupado.stderr
    finally:
        os.close(fd)
    libre = subprocess.run([sys.executable, "-c", script, str(path)], cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=15)
    assert libre.returncode == 0, libre.stderr


def test_consulta_total_conserva_parametros_del_motor_y_ausencia_push():
    modelo = modelo_sintetico()
    r = consultar(modelo, "Local Á", "Visita Ñ", "TOTAL", 180.5)
    assert r["distribucion"]["media"] == 180
    assert r["distribucion"]["desviacion"] == pytest.approx(np.sqrt(52))
    assert r["probabilidad_over"] + r["probabilidad_under"] == pytest.approx(1)
    assert r["metadata"]["corte_modelo"] == "2026-01-01"
    entero = consultar(modelo, "Local Á", "Visita Ñ", "TOTAL", 180.)
    assert entero["probabilidad_over"] is None and entero["probabilidad_push"] is None
    assert entero["distribucion"] == r["distribucion"]
    assert consultar(modelo, "Local Á", "Visita Ñ", "Q2", 45.5)["distribucion"]["media"] == 45


def test_api_local_no_entrena_ni_abre_bd_y_no_admite_contexto(monkeypatch):
    def prohibido(*args, **kw):
        raise AssertionError("Operación ajena a la consulta local")
    monkeypatch.setattr("db.obtener_pool", prohibido)
    monkeypatch.setattr("motor_autoentrenamiento.entrenador_bd.EntrenadorBD.entrenar", prohibido)
    monkeypatch.setattr(rutas_local, "obtener_modelo", modelo_sintetico)
    app = FastAPI(); app.include_router(rutas_local.router)
    client = TestClient(app)
    assert client.get("/api/local/nba/catalogo").json()["equipos"] == ["local á", "visita ñ"]
    peticion = {"equipo_local": "Local Á", "equipo_visitante": "Visita Ñ", "linea": 180.5}
    for _ in range(2):
        r = client.post("/api/local/nba/consultar", json=peticion)
        assert r.status_code == 200
        assert r.json()["modo"] == "BASE_LOCAL"
    assert client.post("/api/local/nba/consultar", json={**peticion, "temporadas": ["x"]}).status_code == 422
    assert client.post("/api/local/nba/consultar", json={**peticion, "equipo_visitante": "Local Á"}).status_code == 422


def test_consulta_estandar_con_temporadas_rechaza_ajuste_implicito(monkeypatch):
    monkeypatch.setattr(rutas_analisis, "_validar_peticion_analisis", lambda p: [])
    monkeypatch.setattr(rutas_analisis, "obtener_pool", lambda: pytest.fail("Abrió BD"))
    peticion = PeticionAnalisis(equipo_local="Local", equipo_visitante="Visita", mercado="COMPLETO", linea=180.5,
                               temporadas=["11111111-1111-1111-1111-111111111111"])
    with pytest.raises(ErrorValidacion, match="modelo publicado"):
        rutas_analisis.ejecutar_analisis(peticion)


def test_explicacion_ausente_no_fabrica_media_intervalo_ni_historico():
    p = {"prediction_id": "test", "sport": "NBA", "home_team": "Local", "away_team": "Visita",
         "game_date": datetime(2026, 1, 1, tzinfo=timezone.utc), "league": "NBA", "value": None,
         "unit": "points", "line": 180.5, "recommendation": "skip", "confidence_numeric": None}
    c = construir_contrato(p, None, [], [], None)
    assert c.prediction.value is None and c.prediction.confidence.numeric is None
    assert c.prediction.confidence.interval is None
    assert c.explanation.top_factors == [] and c.explanation.historical_context is None


def test_sincronizacion_windows_es_puntual_explicita_y_sin_shell(monkeypatch):
    from api import rutas_agendas
    llamadas = []
    monkeypatch.setattr(rutas_agendas, 'os', SimpleNamespace(name='nt', environ={}))
    monkeypatch.setattr(rutas_agendas.subprocess, 'Popen', lambda args, **kw: llamadas.append((args, kw)))
    assert llamadas == []
    assert rutas_agendas.solicitar_sincronizacion()['estado'] == 'SOLICITADA'
    args, kw = llamadas[0]
    assert args[-1] == '--aplicar' and args[0] == sys.executable
    assert not kw.get('shell', False) and 'systemctl' not in args
    assert kw['stdout'] == subprocess.DEVNULL


def test_journal_wnba_utf8_no_modifica_tildes_ni_hash(tmp_path):
    from servicios.predictor_wnba import escribir
    from motor.wnba import huella
    datos = {'equipo': 'Peña Ñ', 'probabilidad': None}
    path = tmp_path / 'ñ.json'
    escribir(path, datos)
    import json
    assert huella(json.loads(path.read_text(encoding='utf-8'))) == huella(datos)
    with pytest.raises(FileExistsError):
        escribir(path, {'otro': 1})


def test_modo_base_impide_pool_incluso_si_hay_url_heredada(monkeypatch):
    import db
    from psycopg import OperationalError
    monkeypatch.setenv('ANALYTICSPREDICT_SOLO_BASE_LOCAL', '1')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://no-debe-consultarse.invalid/prueba')
    monkeypatch.setattr(db, 'PoolAplicacion', lambda **kw: pytest.fail('Creó pool'))
    with pytest.raises(OperationalError, match='deshabilitada'):
        db.obtener_pool()


def test_lanzador_rechaza_puerto_ocupado_sin_detener_al_dueno():
    import importlib.util
    from pathlib import Path
    import socket
    spec = importlib.util.spec_from_file_location('iniciar_local_producto', Path(__file__).resolve().parents[2] / 'scripts/iniciar_local.py')
    launcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
    with socket.socket() as ocupado:
        ocupado.bind(('127.0.0.1', 0)); ocupado.listen()
        with pytest.raises(ValueError, match='No se detuvo'):
            launcher.comprobar_puertos([ocupado.getsockname()[1]])
        assert ocupado.fileno() >= 0


def test_contexto_relee_despues_de_un_cambio_de_datos(monkeypatch):
    from motor.contexto import recolector_contexto as ctx
    from datetime import date
    revision = {'n': 1}
    monkeypatch.setattr(ctx, 'obtener_pool', lambda: object())
    monkeypatch.setattr(ctx, '_obtener_equipo_id', lambda pool, nombre: (nombre, nombre))
    monkeypatch.setattr(ctx, '_recolectar_contexto_ids', lambda *args: dict(revision))
    assert ctx.recolectar_contexto('l', 'v', date(2026, 1, 1)) == {'n': 1}
    revision['n'] = 2
    assert ctx.recolectar_contexto('l', 'v', date(2026, 1, 1)) == {'n': 2}


def test_cierre_windows_se_limita_al_arbol_del_proceso_propio(monkeypatch):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('inicio_cierre', Path(__file__).resolve().parents[2] / 'scripts/iniciar_local.py')
    launcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
    llamadas = []
    monkeypatch.setattr(launcher, 'os', SimpleNamespace(name='nt'))
    monkeypatch.setattr(launcher.subprocess, 'run', lambda args, **kw: llamadas.append((args, kw)))
    propio = SimpleNamespace(pid=12345, poll=lambda: None, wait=lambda **kw: None)
    launcher.cerrar_backend(propio)
    assert llamadas[0][0] == ['taskkill', '/PID', '12345', '/T', '/F']
    assert llamadas[0][1]['stdout'] == subprocess.DEVNULL
    assert not llamadas[0][1].get('shell', False)
    launcher.cerrar_backend(SimpleNamespace(pid=99999, poll=lambda: 0))
    assert len(llamadas) == 1
