"""El recordatorio no confunde intentos, escrituras y cobertura completa."""
import pytest
from servicios.actualizacion_ligas import combinar
from api import rutas_agendas


def test_parcial_con_cambio_reciente_no_certifica_todas_ligas():
    ligas = [{'codigo': 'nba', 'cambio_en': '2026-11-01'}, {'codigo': 'euroleague'}]
    agenda = {'terminado_en': '2026-11-01T18:00:00Z', 'estado': 'PARCIAL', 'resumen': {
        'cobertura': [{'competicion': 'nba', 'incidencias': 0}, {'competicion': 'euroleague', 'incidencias': 1}]}}
    r = combinar(ligas, agenda, None, None)
    assert r['ultima_completa_en'] is None
    assert r['ligas'][0]['estado_agenda'] == 'VERIFICADA'
    assert r['ligas'][1]['estado_agenda'] == 'CON_INCIDENCIAS'
    assert r['ligas'][0]['estadisticas']['estado'] == 'SIN_ACREDITAR'


def test_torneo_sin_recibo_no_se_da_por_actualizado_y_completa_previa_persiste():
    completa = {'terminado_en': '2026-10-01T00:00:00Z'}
    integral = {'terminado_en': '2026-11-01T18:00:00Z', 'estado': 'PARCIAL', 'resumen': {
        'estadisticas': {'USA_MLS': {'estado': 'PARCIAL', 'detalle': 'Faltan estadísticas'}}}}
    r = combinar([{'codigo': 'USA_MLS'}, {'codigo': 'USA_MLS_BACK'}], None, integral, completa)
    assert r['ultima_completa_en'] == completa['terminado_en']
    assert r['ultimo_ciclo_integral']['estado'] == 'PARCIAL'
    assert r['ligas'][0]['estadisticas']['estado'] == 'PARCIAL'
    assert r['ligas'][1]['estado_agenda'] == 'SIN_ACREDITAR'


def test_modo_base_no_abre_bd(monkeypatch):
    monkeypatch.setenv('ANALYTICSPREDICT_SOLO_BASE_LOCAL', '1')
    monkeypatch.setattr(rutas_agendas, 'estado_local', lambda: {'estado': 'SIN_SINCRONIZAR'})
    monkeypatch.setattr(rutas_agendas, 'obtener_actualizacion_ligas', lambda: pytest.fail('No abrir BD'))
    assert rutas_agendas.estado_sincronizacion()['actualizacion_ligas'] is None


def test_error_sql_no_rompe_estado_ni_filtra_conexion(monkeypatch):
    monkeypatch.delenv('ANALYTICSPREDICT_SOLO_BASE_LOCAL', raising=False)
    monkeypatch.setattr(rutas_agendas, 'estado_local', lambda: {'estado': 'EN_CURSO'})
    def fallar(): raise RuntimeError('cadena-privada-no-publicar')
    monkeypatch.setattr(rutas_agendas, 'obtener_actualizacion_ligas', fallar)
    r = rutas_agendas.estado_sincronizacion()
    assert r['estado'] == 'EN_CURSO'
    assert r['actualizacion_ligas'] is None
    assert 'cadena-privada' not in str(r)
