"""Un clic recorre varios lotes sin confundir consultas, turnos ni cobertura."""
from datetime import date, datetime, timezone

import pytest

from servicios import etapa_agenda_multiliga as agenda


def ejecutar(monkeypatch, total, *, cupo=48, limite=200, repetidas=False):
    pendientes = list(range(total))
    calls = []

    def etapa(_conn, _execution, _ligas, _client, _hoy, _ahora, **kwargs):
        calls.append(kwargs)
        selected = pendientes[:kwargs['cupo']]
        del pendientes[:len(selected)]
        queries = [{'clave':str(i), 'url':'https://fuente/scoreboard',
                    'params':{'dates':str(i)}, 'pruebas':[]} for i in selected]
        if repetidas:
            queries += [{**q, 'clave':q['clave']+'-otra-ventana'} for q in queries]
        return {'lote':str(len(calls)), 'recibo':{'operaciones_agenda':len(selected)},
                'nuevo':True, 'preparado':{'consultas':queries}}

    monkeypatch.setattr(agenda, 'ejecutar_etapa_agenda', etapa)
    result = agenda.ejecutar_agenda_por_lotes(None, 'run', [], object(),
        date(2026,11,12), datetime(2026,11,12,tzinfo=timezone.utc),
        cupo_lote=cupo, max_turnos=limite)
    return result, pendientes, calls


def test_un_clic_cubre_184_consultas_sin_ampliar_el_cupo_de_cada_lote(monkeypatch):
    result, pending, calls = ejecutar(monkeypatch, 184)
    assert not pending
    assert [x['turnos'] for x in result['lotes']] == [48,48,48,40]
    assert result['turnos_consumidos'] == 184
    assert len(result['preparado']['consultas']) == 184
    assert result['recibo']['operaciones_agenda'] == 184
    assert result['motivo_parada'] == 'SIN_CONSULTAS_ELEGIBLES'
    assert all(x['cupo']<=48 for x in calls)


def test_presupuesto_total_es_firme_y_deja_continuidad_explicita(monkeypatch):
    result, pending, _ = ejecutar(monkeypatch, 250)
    assert result['turnos_consumidos'] == 200
    assert len(pending) == 50
    assert result['motivo_parada'] == 'LIMITE_TURNOS'


def test_dos_horizontes_de_una_url_no_son_dos_turnos_http(monkeypatch):
    result, pending, _ = ejecutar(monkeypatch, 3, repetidas=True)
    assert not pending and result['turnos_consumidos']==3
    assert len(result['preparado']['consultas'])==6
    assert result['lotes'][0]['consultas']==6


def test_consultas_ya_intentadas_se_excluyen_en_lotes_siguientes(monkeypatch):
    _, _, calls = ejecutar(monkeypatch, 60)
    assert not calls[0]['excluir_origenes']
    assert len(calls[1]['excluir_origenes'])==48


def test_cola_no_vencida_no_se_trata_como_cobertura_completa(monkeypatch):
    result, _, _ = ejecutar(monkeypatch, 0)
    assert result['lotes']==[] and result['turnos_consumidos']==0
    assert result['motivo_parada']=='SIN_CONSULTAS_ELEGIBLES'
    assert 'cobertura_oficial' not in result


@pytest.mark.parametrize('cupo,limite',[(0,200),(201,200),(48,201),(True,200),(48,1)])
def test_limites_invalidos_no_llegan_a_sql(monkeypatch,cupo,limite):
    with pytest.raises(ValueError): ejecutar(monkeypatch, 10,cupo=cupo,limite=limite)
