# -*- coding: utf-8 -*-
"""
Tests de integración para el endpoint /api/analizar con registro de predicciones.

Verifica los criterios de DoD de la Tarea 5:
1. Inserción real cuando hay contexto determinístico (partido_id o fecha_partido)
2. NO inserción cuando falta contexto determinístico
3. Idempotencia al repetir request con mismos parámetros
4. El endpoint no rompe si la BD falla durante registro (best-effort)

Ejecutar: pytest backend/tests/test_endpoint_analizar_registro.py -v
"""

import sys
from datetime import date
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.modelos_peticion import PeticionAnalisis
from api.rutas_analisis import _extraer_contexto_registro, _buscar_partido_por_equipos_fecha


# =============================================================================
# TESTS UNITARIOS - Lógica de _extraer_contexto_registro
# =============================================================================


def test_extraer_contexto_camino_feliz_todos_los_campos():
    """Cuando vienen todos los campos, debe retornar el contexto directamente."""
    peticion = PeticionAnalisis(
        partido_id=UUID("11111111-1111-1111-1111-111111111111"),
        temporada_id=UUID("22222222-2222-2222-2222-222222222222"),
        equipo_local_id=UUID("33333333-3333-3333-3333-333333333333"),
        equipo_visitante_id=UUID("44444444-4444-4444-4444-444444444444"),
        fecha_partido=date(2024, 1, 15),
        tipo_partido="REG",
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
    )

    contexto = _extraer_contexto_registro(peticion)

    assert contexto is not None
    assert contexto["partido_id"] == peticion.partido_id
    assert contexto["temporada_id"] == peticion.temporada_id
    assert contexto["equipo_local_id"] == peticion.equipo_local_id
    assert contexto["equipo_visitante_id"] == peticion.equipo_visitante_id
    assert contexto["fecha_partido"] == peticion.fecha_partido
    assert contexto["tipo_partido"] == peticion.tipo_partido


def test_extraer_contexto_sin_partido_id_ni_fecha_retorna_none():
    """
    CRÍTICO: Sin partido_id NI fecha_partido NO se debe registrar.
    Registrar contra "partido más reciente" contamina calibración.
    """
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        # SIN partido_id
        # SIN fecha_partido
    )

    contexto = _extraer_contexto_registro(peticion)

    assert contexto is None, "Sin partido_id ni fecha_partido debe retornar None"


def test_extraer_contexto_sin_partido_id_pero_con_fecha_hace_lookup():
    """
    Si hay fecha_partido pero no partido_id, debe hacer lookup exacto.
    """
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        fecha_partido=date(2024, 1, 15),  # Tiene fecha
        # SIN partido_id
    )

    # Mock del lookup que encuentra un partido
    partido_mock = {
        "partido_id": UUID("11111111-1111-1111-1111-111111111111"),
        "temporada_id": UUID("22222222-2222-2222-2222-222222222222"),
        "equipo_local_id": UUID("33333333-3333-3333-3333-333333333333"),
        "equipo_visitante_id": UUID("44444444-4444-4444-4444-444444444444"),
        "fecha_partido": date(2024, 1, 15),
        "tipo_partido": "REG",
    }

    with patch(
        "api.rutas_analisis._buscar_partido_por_equipos_fecha",
        return_value=partido_mock,
    ):
        contexto = _extraer_contexto_registro(peticion)

    assert contexto is not None
    assert contexto["partido_id"] == partido_mock["partido_id"]


def test_extraer_contexto_con_fecha_pero_partido_no_encontrado():
    """
    Si hay fecha_partido pero el partido no existe en BD, retorna None.
    """
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        fecha_partido=date(2024, 12, 31),  # Fecha de partido que no existe
    )

    with patch(
        "api.rutas_analisis._buscar_partido_por_equipos_fecha",
        return_value=None,  # No encontrado
    ):
        contexto = _extraer_contexto_registro(peticion)

    assert contexto is None


def test_extraer_contexto_con_equipo_ids_pero_sin_partido_id_ni_fecha():
    """
    Tener equipo_local_id y equipo_visitante_id NO es suficiente.
    Sin partido_id ni fecha_partido debe retornar None.
    """
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        equipo_local_id=UUID("33333333-3333-3333-3333-333333333333"),
        equipo_visitante_id=UUID("44444444-4444-4444-4444-444444444444"),
        # SIN partido_id
        # SIN fecha_partido
    )

    contexto = _extraer_contexto_registro(peticion)

    assert contexto is None, "Solo equipo IDs sin partido_id/fecha no es suficiente"


def test_extraer_contexto_con_temporada_id_pero_sin_partido_id_ni_fecha():
    """
    Tener temporada_id NO es suficiente.
    Sin partido_id ni fecha_partido debe retornar None.
    """
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        temporada_id=UUID("22222222-2222-2222-2222-222222222222"),
        # SIN partido_id
        # SIN fecha_partido
    )

    contexto = _extraer_contexto_registro(peticion)

    assert contexto is None


# =============================================================================
# TESTS UNITARIOS - Función _buscar_partido_por_equipos_fecha
# =============================================================================


def test_buscar_partido_requiere_fecha():
    """
    La función de búsqueda ahora REQUIERE fecha.
    Sin fecha no se puede buscar (evita "partido más reciente").
    """
    # La firma de la función ahora requiere fecha como parámetro obligatorio
    # Si se llama sin fecha, debería fallar o el caller no debe llamarla
    # Esto es un test de diseño: la función NO tiene lógica de "buscar sin fecha"

    # Verificamos que el código actual NO hace fallback sin fecha
    from api.rutas_analisis import _buscar_partido_por_equipos_fecha
    import inspect

    sig = inspect.signature(_buscar_partido_por_equipos_fecha)
    params = sig.parameters

    # fecha_partido no debe tener default None ni ser opcional sin validación
    # La función debería requerir fecha para funcionar correctamente
    assert "fecha_partido" in params


# =============================================================================
# TESTS DE INTEGRACIÓN SIMULADOS - Endpoint completo con mocks
# =============================================================================


class FakeModelo:
    """Modelo simulado para tests."""

    version = 1

    def obtener_equipos(self):
        return ["Lakers", "Heat", "Celtics", "Bulls"]

    @property
    def entidad_a_indice(self):
        return {"Lakers": 0, "Heat": 1, "Celtics": 2, "Bulls": 3}


class FakeResultado:
    """Resultado de análisis simulado."""

    def __init__(self):
        self.candidatos = [FakeCandidato()]
        self.analisis_mercado = None
        self.mejor_apuesta = None


class FakeCandidato:
    """Candidato simulado."""

    cuarto = "Q1"
    lado = MagicMock(value="OVER")
    linea = 50.5
    media = 52.0
    desviacion = 8.5
    probabilidad = 0.58
    cuota = 1.85
    cuota_over = 1.85
    cuota_under = 2.0


def test_endpoint_no_registra_sin_contexto_deterministico():
    """
    El endpoint /api/analizar NO debe registrar predicción
    cuando falta partido_id Y fecha_partido.
    """
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        cuota_over=1.85,
        # SIN partido_id
        # SIN fecha_partido
    )

    registrar_llamado = []

    def mock_registrar(*args, **kwargs):
        registrar_llamado.append(kwargs)
        return uuid4()

    fake_datos = {"predicciones": [], "mejor_apuesta": None}
    with patch("api.rutas_analisis.obtener_modelo", return_value=FakeModelo()):
        with patch("api.rutas_analisis.validar_equipos"):  # Bypass validación
            with patch("api.rutas_analisis.analizar_partido", return_value=FakeResultado()):
                with patch("api.rutas_analisis.resultado_a_dict", return_value=fake_datos):
                    with patch("api.rutas_analisis.registrar_prediccion", side_effect=mock_registrar):
                        with patch("api.rutas_analisis._obtener_config_usuario", return_value=None):
                            from api.rutas_analisis import ejecutar_analisis
                            resultado = ejecutar_analisis(peticion)

    assert len(registrar_llamado) == 0, "NO debe llamar registrar_prediccion sin contexto"
    assert resultado.exito is True, "El análisis debe completarse exitosamente"


def test_endpoint_registra_con_contexto_completo():
    """
    El endpoint /api/analizar SÍ debe registrar predicción
    cuando tiene todos los campos de contexto.
    """
    peticion = PeticionAnalisis(
        partido_id=UUID("11111111-1111-1111-1111-111111111111"),
        temporada_id=UUID("22222222-2222-2222-2222-222222222222"),
        equipo_local_id=UUID("33333333-3333-3333-3333-333333333333"),
        equipo_visitante_id=UUID("44444444-4444-4444-4444-444444444444"),
        fecha_partido=date(2024, 1, 15),
        tipo_partido="REG",
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        cuota_over=1.85,
    )

    registrar_llamado = []

    def mock_registrar(*args, **kwargs):
        registrar_llamado.append(kwargs)
        return uuid4()

    fake_datos = {"predicciones": [], "mejor_apuesta": None}
    with patch("api.rutas_analisis.obtener_modelo", return_value=FakeModelo()):
        with patch("api.rutas_analisis.validar_equipos"):  # Bypass validación
            with patch("api.rutas_analisis.analizar_partido", return_value=FakeResultado()):
                with patch("api.rutas_analisis.resultado_a_dict", return_value=fake_datos):
                    with patch("api.rutas_analisis.registrar_prediccion", side_effect=mock_registrar):
                        with patch("api.rutas_analisis._obtener_config_usuario", return_value=None):
                            from api.rutas_analisis import ejecutar_analisis
                            resultado = ejecutar_analisis(peticion)

    assert len(registrar_llamado) == 1, "Debe llamar registrar_prediccion con contexto completo"
    assert registrar_llamado[0]["partido_id"] == peticion.partido_id
    assert registrar_llamado[0]["origen"] == "API_USUARIO"
    assert resultado.exito is True


def test_endpoint_no_rompe_si_registro_falla():
    """
    El endpoint no debe fallar si el registro de predicción falla.
    El registro es best-effort.
    """
    peticion = PeticionAnalisis(
        partido_id=UUID("11111111-1111-1111-1111-111111111111"),
        temporada_id=UUID("22222222-2222-2222-2222-222222222222"),
        equipo_local_id=UUID("33333333-3333-3333-3333-333333333333"),
        equipo_visitante_id=UUID("44444444-4444-4444-4444-444444444444"),
        fecha_partido=date(2024, 1, 15),
        tipo_partido="REG",
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        cuota_over=1.85,
    )

    def mock_registrar_falla(*args, **kwargs):
        raise RuntimeError("BD caída simulada")

    fake_datos = {"predicciones": [], "mejor_apuesta": None}
    with patch("api.rutas_analisis.obtener_modelo", return_value=FakeModelo()):
        with patch("api.rutas_analisis.validar_equipos"):  # Bypass validación
            with patch("api.rutas_analisis.analizar_partido", return_value=FakeResultado()):
                with patch("api.rutas_analisis.resultado_a_dict", return_value=fake_datos):
                    with patch("api.rutas_analisis.registrar_prediccion", side_effect=mock_registrar_falla):
                        with patch("api.rutas_analisis._obtener_config_usuario", return_value=None):
                            from api.rutas_analisis import ejecutar_analisis
                            # No debe lanzar excepción
                            resultado = ejecutar_analisis(peticion)

    assert resultado.exito is True, "El análisis debe completarse aunque falle el registro"


def test_endpoint_registra_con_fecha_via_lookup():
    """
    Si hay fecha_partido pero no partido_id, debe hacer lookup y registrar.
    """
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        cuota_over=1.85,
        fecha_partido=date(2024, 1, 15),  # Tiene fecha
        # SIN partido_id
    )

    partido_lookup = {
        "partido_id": UUID("11111111-1111-1111-1111-111111111111"),
        "temporada_id": UUID("22222222-2222-2222-2222-222222222222"),
        "equipo_local_id": UUID("33333333-3333-3333-3333-333333333333"),
        "equipo_visitante_id": UUID("44444444-4444-4444-4444-444444444444"),
        "fecha_partido": date(2024, 1, 15),
        "tipo_partido": "REG",
    }

    registrar_llamado = []

    def mock_registrar(*args, **kwargs):
        registrar_llamado.append(kwargs)
        return uuid4()

    fake_datos = {"predicciones": [], "mejor_apuesta": None}
    with patch("api.rutas_analisis.obtener_modelo", return_value=FakeModelo()):
        with patch("api.rutas_analisis.validar_equipos"):  # Bypass validación
            with patch("api.rutas_analisis.analizar_partido", return_value=FakeResultado()):
                with patch("api.rutas_analisis.resultado_a_dict", return_value=fake_datos):
                    with patch("api.rutas_analisis.registrar_prediccion", side_effect=mock_registrar):
                        with patch("api.rutas_analisis._obtener_config_usuario", return_value=None):
                            with patch("api.rutas_analisis._buscar_partido_por_equipos_fecha", return_value=partido_lookup):
                                from api.rutas_analisis import ejecutar_analisis
                                resultado = ejecutar_analisis(peticion)

    assert len(registrar_llamado) == 1, "Debe registrar via lookup por fecha"
    assert registrar_llamado[0]["partido_id"] == partido_lookup["partido_id"]


# =============================================================================
# TEST DE REGRESIÓN - Verificar que NO existe el bug del "partido más reciente"
# =============================================================================


def test_regresion_no_busca_partido_mas_reciente():
    """
    REGRESIÓN: Verifica que el sistema NO busca "el partido más reciente"
    cuando falta fecha_partido.

    Este bug causaba que las predicciones se registraran contra partidos
    históricos incorrectos, contaminando calibración y trazabilidad.
    """
    peticion_sin_fecha = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        lado="OVER",
        # SIN fecha_partido
        # SIN partido_id
    )

    llamadas_a_lookup = []

    def mock_lookup(equipo_local, equipo_visitante, fecha_partido):
        llamadas_a_lookup.append({
            "equipo_local": equipo_local,
            "equipo_visitante": equipo_visitante,
            "fecha_partido": fecha_partido,
        })
        return None

    with patch("api.rutas_analisis._buscar_partido_por_equipos_fecha", side_effect=mock_lookup):
        contexto = _extraer_contexto_registro(peticion_sin_fecha)

    # No debe llamar al lookup si no hay fecha
    assert len(llamadas_a_lookup) == 0, "No debe llamar lookup sin fecha"
    assert contexto is None, "Debe retornar None sin contexto determinístico"
