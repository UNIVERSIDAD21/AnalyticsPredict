from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from motor_futbol.evaluacion.estacional import PoliticaEstacional, preparar_candidato, pronosticar_sombra
from scripts.preparar_futbol_sombra import escribir_nuevo, cargar_partidos
from motor_futbol.evaluacion.cohorte_sombra import evaluar_cohorte
from motor_futbol.modelos.artefacto import sha256


UTC = timezone.utc


def datos():
    filas = []
    for i in range(720):
        # Simula receso de dos meses antes del bloque CAL; todos los clubes tienen soporte.
        dia = datetime(2024, 1, 1, tzinfo=UTC)+timedelta(days=i//5)
        if i >= 500: dia += timedelta(days=65)
        filas.append(dict(id=str(i), fecha_partido=dia, equipo_local='Casa', equipo_visitante='Fuera',
            competicion_codigo='ENG_PREMIER', local_goles_1t=1, local_goles_2t=1,
            visitante_goles_1t=0, visitante_goles_2t=1, local_goles_total=2, visitante_goles_total=1))
    return filas


def test_particion_no_rompe_empates_y_no_refit_cal():
    filas = datos()
    corte = max(p['fecha_partido'] for p in filas)+timedelta(days=1)
    a = preparar_candidato(filas, 'goles', corte)
    assert a['estado'] == 'CANDIDATO_SOMBRA' and not a['activable']
    assert a['train']['n_partidos'] >= 500 and a['cal']['n_partidos'] >= 200
    assert a['train']['fecha_max'] < a['cal']['fecha_min'] < corte.isoformat()
    assert a['calibrador'] is None
    futuro = deepcopy(filas[-1]); futuro.update(id='futuro', fecha_partido=corte+timedelta(days=20), local_goles_1t=999)
    b = preparar_candidato(filas+[futuro], 'goles', corte)
    assert a == b  # No inspecciona resultados futuros para elegir alpha ni el límite.


def test_receso_no_relaja_muestra_y_equipos_nuevos_se_reportan():
    filas = datos()
    for p in filas[-50:]: p['equipo_local'] = 'Nuevo'
    corte = max(p['fecha_partido'] for p in filas)+timedelta(days=1)
    a = preparar_candidato(filas, 'goles', corte)
    assert a['n_cal_equipo_desconocido'] == 50
    assert a['equipos_excluidos'] == [{'equipo': 'nuevo', 'partidos_previos': 0, 'motivo': 'SIN_MINIMO_O_PODA_TRAIN'}]
    viejo = preparar_candidato(filas, 'goles', corte+timedelta(days=200))
    assert viejo['estado'] == 'SIN_CANDIDATO' and 'MUESTRA_CAL_INSUFICIENTE' in viejo['motivos']


def test_reserva_100_se_declara_aparte_y_no_relaja_minimo_de_equipo():
    filas = datos()
    for p in filas[540:]: p['equipo_local'] = 'Nuevo'
    corte = max(p['fecha_partido'] for p in filas)+timedelta(days=1)
    anterior = preparar_candidato(filas, 'goles', corte)
    politica = PoliticaEstacional(objetivo_cal=100, version='estacional_sombra_v3_cal100')
    nuevo = preparar_candidato(filas, 'goles', corte, politica)
    assert anterior['estado'] == 'SIN_CANDIDATO'  # No maquillar la reserva200 previa.
    assert nuevo['estado'] == 'CANDIDATO_SOMBRA' and 'nuevo' in nuevo['entidades']
    assert nuevo['cal']['n_partidos'] >= 100
    assert nuevo['politica']['min_partidos_equipo'] == anterior['politica']['min_partidos_equipo'] == 5
    assert nuevo['politica_sha256'] != anterior['politica_sha256']
    assert not nuevo['activable']


def test_sombra_es_futura_no_lee_outcomes_y_cuenta_abstenciones():
    filas = datos(); corte = max(p['fecha_partido'] for p in filas)+timedelta(days=1)
    a = preparar_candidato(filas, 'goles', corte)
    ahora = corte+timedelta(seconds=1); inicio = corte+timedelta(days=1); fin = inicio+timedelta(days=30)
    fixture = {'id': 'A', 'fecha_partido': inicio, 'equipo_local': 'Casa', 'equipo_visitante': 'Fuera',
               'estado': 'PROGRAMADO', 'competicion_codigo': 'ENG_PREMIER'}
    desconocido = {**fixture, 'id': 'B', 'equipo_local': 'Nuevo'}
    p = pronosticar_sombra(a, [fixture, desconocido], ahora, inicio, fin)
    assert len(p['predicciones']) == len(p['abstenciones']) == 1
    assert p['predicciones'][0]['p_raw'] is None
    otros = {**fixture, 'local_goles_1t': 900}
    assert pronosticar_sombra(a, [otros, desconocido], ahora, inicio, fin) == p
    with pytest.raises(ValueError, match='duplicados'):
        pronosticar_sombra(a, [fixture, fixture], ahora, inicio, fin)
    with pytest.raises(ValueError, match='Orden obligatorio'):
        pronosticar_sombra(a, [fixture], fin, inicio, fin)


@pytest.mark.parametrize('campo,valor', [('min_cal', 99), ('min_train', 499), ('cobertura_minima', .89), ('max_dias_cal', 365)])
def test_no_baja_gates(campo, valor):
    with pytest.raises(ValueError): replace(PoliticaEstacional(), **{campo: valor}).validar()


def test_archivos_no_se_sobrescriben_y_hash_se_verifica(tmp_path):
    p = tmp_path/'cohorte.json'; escribir_nuevo(p, {'original': 1})
    with pytest.raises(FileExistsError): escribir_nuevo(p, {'original': 2})
    assert '1' in p.read_text()
    corrupto = tmp_path/'datos.json'; escribir_nuevo(corrupto, {'partidos': [], 'sha256_datos': 'incorrecto'})
    with pytest.raises(ValueError, match='hash'): cargar_partidos(corrupto)


def test_evaluacion_posterior_no_promueve_ni_borra_abstenciones():
    filas = datos(); corte = max(p['fecha_partido'] for p in filas)+timedelta(days=1)
    a = preparar_candidato(filas, 'goles', corte)
    ahora = corte+timedelta(seconds=1); inicio = corte+timedelta(days=1); fin = inicio+timedelta(days=30)
    fixture = {**filas[-1], 'id': 'A', 'estado': 'PROGRAMADO', 'fecha_partido': inicio}
    desconocido = {**fixture, 'id': 'B', 'equipo_local': 'Nuevo'}
    familia = {'candidato': a, 'cohorte': pronosticar_sombra(a, [fixture, desconocido], ahora, inicio, fin)}
    cohorte = {'congelado_en': ahora.isoformat(), 'declaracion': {'fin_eval': fin.isoformat()}, 'familias': {'goles': familia}}
    cohorte['sha256'] = sha256(cohorte)
    anterior = evaluar_cohorte(cohorte, [], ahora+timedelta(seconds=1))['familias']['goles']
    assert anterior['pendientes'] == 1 and anterior['candidatos'] == 2 and anterior['metricas']['mae'] is None
    outcome = {**fixture, 'estado': 'FINALIZADO'}
    posterior = evaluar_cohorte(cohorte, [outcome], fin+timedelta(days=1))['familias']['goles']
    assert posterior['cobertura_resuelta_total'] == .5 and not posterior['activable']
    assert 'TARGET_SIN_FRESCURA' in evaluar_cohorte(cohorte, [outcome], fin+timedelta(days=100))['familias']['goles']['motivos']
    cambio = {**outcome, 'fecha_partido': inicio+timedelta(hours=1)}
    assert evaluar_cohorte(cohorte, [cambio], fin+timedelta(days=1))['familias']['goles']['exclusiones'] == {'IDENTIDAD_O_INICIO_CAMBIADO': 1}
    corrupta = deepcopy(cohorte); corrupta['familias']['goles']['cohorte']['predicciones'][0]['p_raw'] = .99
    with pytest.raises(ValueError, match='hash'): evaluar_cohorte(corrupta, [outcome], fin+timedelta(days=1))
