from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path

import pytest
from servicios.actualizador_partidos import ventana, resumen_ligas
from servicios.fuentes_resultados import Capturas, recolectar, tareas
from servicios.operacion_agendas import exclusion
from servicios.transporte_agenda import FuenteNoDisponible
from scripts.actualizar_partidos_local import configuracion


LIGA = {'codigo': 'nba', 'deporte': 'baloncesto', 'nombre': 'NBA'}


def partido():
    return {'id': '123', 'date': '2026-10-20T23:00Z', 'season': {'type': 2, 'year': 2027},
        'status': {'type': {'name': 'STATUS_FINAL', 'completed': True}},
        'competitions': [{'competitors': [
            {'homeAway': 'home', 'team': {'id': '1', 'displayName': 'Equipo A'}, 'score': '100',
             'linescores': [{'value': 25, 'period': i} for i in range(1, 5)]},
            {'homeAway': 'away', 'team': {'id': '2', 'displayName': 'Equipo B'}, 'score': '96',
             'linescores': [{'value': 24, 'period': i} for i in range(1, 5)]}]}]}


class Cliente:
    def __init__(self, payloads): self.payloads = iter(payloads)
    def json(self, *_args, **_kwargs):
        return next(self.payloads), {'observado_en': '2026-11-06T20:00:00+00:00', 'url': 'fuente-de-prueba'}


def feed(events, slug='nba'):
    return {'leagues': [{'slug': slug}], 'events': events}


def test_ventana_recupera_pausa_larga_sin_saltar_dias_y_solapa():
    start, end = ventana(date(2026, 11, 6), '2026-08-01')
    assert start == date(2026, 7, 25)
    assert (end-start).days == 30
    assert end < date(2026, 11, 6)
    assert ventana(date(2026, 11, 6), str(end))[0] == end - timedelta(days=7)
    assert ventana(date(2026, 11, 6))[0] == date(2026, 10, 23)


def test_ventana_futura_no_omite_la_revision_reciente():
    assert ventana(date(2026, 11, 6), '2099-01-01')[0] == date(2026, 10, 30)


def test_nba_conserva_espn_y_cubre_madrugada_utc():
    jobs = list(tareas(LIGA, date(2026, 11, 5), date(2026, 11, 6)))
    assert len(jobs) == 3
    assert all('espn.com' in x[0] and '/nba/' in x[0] for x in jobs)
    assert jobs[-1][1]['dates'] == '20261107'


def test_catalogo_sin_adaptador_no_se_declara_actualizado():
    league = {'codigo': 'HISTORICA', 'deporte': 'futbol', 'nombre': 'Histórica'}
    rows, errors, _, _ = recolectar(Cliente([]), league, date(2026, 11, 6), date(2026, 11, 6))
    assert not rows and 'SIN_ADAPTADOR' in errors[0]['motivo']


def test_finales_no_completos_y_ot_ausente_no_se_imputan():
    event = partido(); event['competitions'][0]['competitors'][0]['linescores'][0]['value'] = None
    rows, errors, _, _ = recolectar(Cliente([feed([event]), feed([])]), LIGA, date(2026, 10, 20), date(2026, 10, 20))
    assert not rows and errors


def test_vivos_no_son_resultados_y_liga_distinta_es_error():
    event = partido(); event['status']['type']['completed'] = False
    rows, errors, _, pending = recolectar(Cliente([feed([event]), feed([], 'otra')]), LIGA, date(2026, 10, 20), date(2026, 10, 20))
    assert not rows and pending == 1 and errors


def test_evento_repetido_no_se_duplica_y_conflicto_no_se_reintroduce():
    event = partido(); other = deepcopy(event)
    other['competitions'][0]['competitors'][0].update(score='104', linescores=[{'value': 26, 'period': i} for i in range(1, 5)])
    rows, errors, _, _ = recolectar(Cliente([feed([event, event]), feed([])]), LIGA, date(2026, 10, 20), date(2026, 10, 20))
    assert len(rows) == 1 and not errors
    rows, errors, _, _ = recolectar(Cliente([feed([event, other, event]), feed([])]), LIGA, date(2026, 10, 20), date(2026, 10, 20))
    assert not rows and errors


def test_error_fuente_es_visible_y_no_equivale_a_liga_vacia():
    class Bloqueado:
        def json(self, *_a, **_kw): raise FuenteNoDisponible('HTTP 403')
    rows, errors, _, _ = recolectar(Bloqueado(), LIGA, date(2026, 10, 20), date(2026, 10, 20))
    assert not rows and all('403' in x['motivo'] for x in errors)


def test_replay_verifica_bytes_y_no_necesita_red(tmp_path):
    blob = tmp_path / 'raw.json'; blob.write_text('{"events":[]}', encoding='utf-8')
    sources = tmp_path / 'fuentes.json'
    sources.write_text(json.dumps([{'url': 'https://site.api.espn.com/test?event=1', 'archivo': str(blob),
        'sha256': sha256(blob.read_bytes()).hexdigest(), 'observado_en': '2026-11-06T00:00:00Z'}]), encoding='utf-8')
    client = Capturas(sources)
    assert client.json('https://site.api.espn.com/test', {'event': 1})[0] == {'events': []}
    assert client.http == 0
    blob.write_text('{}', encoding='utf-8')
    with pytest.raises(FuenteNoDisponible, match='alterada'): client.json('https://site.api.espn.com/test', {'event': 1})
    with pytest.raises(FuenteNoDisponible): client.json('https://otro.example/test')


def test_bloqueo_impide_dos_actualizadores(tmp_path):
    with exclusion(tmp_path):
        with pytest.raises(RuntimeError, match='curso'):
            with exclusion(tmp_path): pytest.fail('No debe adquirir dos veces')


@pytest.mark.parametrize('param', ['host=remoto', 'hostaddr=1.2.3.4', 'dbname=otra', 'sslmode=require', 'options=-csearch_path=otro'])
def test_destinos_ajenos_o_redirecciones_no_se_admiten(tmp_path, param):
    env = tmp_path / 'producto/backend/.env'; env.parent.mkdir(parents=True)
    (tmp_path / 'RUNTIME_LOCAL.json').write_text('{"pg_bin":"C:/prueba"}')
    env.write_text('DATABASE_URL="host=127.0.0.1 port=55433 dbname=ap_unicode_20261101_044650 sslmode=disable ' + param + '"')
    with pytest.raises(ValueError): configuracion(env)


def test_estadistica_pendiente_impide_marcar_liga_completa():
    stats = {'incidencias': [{'grupo': 'nba', 'motivo': 'ESTADISTICAS_LOCALES_PENDIENTES'}], 'actualizados': {}, 'campos': {}}
    result = resumen_ligas([LIGA], {'nba': (date(2026, 11, 1), date(2026, 11, 6))},
        {'nba': {'finales': 1, 'no_finales': 0}}, {'incidencias': [], 'operaciones': []}, stats, 'ahora')
    assert result[0]['estado'] == 'PARCIAL'


def test_entrada_existente_delega_solo_la_actualizacion_normal(monkeypatch):
    from scripts import sincronizar_agendas as entry
    from scripts import actualizar_partidos_local as updated
    monkeypatch.setattr(updated, 'main', lambda args: ('nuevo', args))
    monkeypatch.setattr(entry, 'ejecutar', lambda _args: 'legado')
    monkeypatch.setattr('sys.argv', ['sincronizar_agendas.py', '--aplicar'])
    assert entry.main() == ('nuevo', ['--aplicar'])
    monkeypatch.setattr('sys.argv', ['sincronizar_agendas.py', '--aplicar', '--solo-agenda'])
    assert entry.main() == 'legado'


def test_permiso_cache_antes_del_commit_indica_que_no_se_guardaron_cambios(tmp_path, monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from scripts import actualizar_partidos_local as cli

    state = tmp_path / 'estado'
    archive = state / 'actualizaciones_partidos'
    monkeypatch.setattr(cli, 'configuracion', lambda *_: ({}, {}, tmp_path, state))
    monkeypatch.setattr(cli, 'conectar', lambda _: nullcontext(object()))
    monkeypatch.setattr(cli, 'solo_lectura', lambda _: nullcontext())
    monkeypatch.setattr(cli, 'catalogo', lambda _: [LIGA])
    monkeypatch.setattr(cli.cola, 'disponible', lambda _: False)

    def sin_permiso(client, *_args, **_kwargs):
        raise PermissionError(13, 'Acceso denegado', str(client.cache / 'red.lock'))

    monkeypatch.setattr(cli, 'recolectar', sin_permiso)
    args = SimpleNamespace(env_local=tmp_path / '.env', bd_ensayo=None, estado=state, salida=archive,
                           aplicar=True, fuentes=None, completar_capturas=False)
    with pytest.raises(PermissionError):
        cli.ejecutar(args)
    result = json.loads((state / 'estado.json').read_text(encoding='utf-8'))
    assert result['estado'] == 'ERROR'
    assert result['progreso']['ligas_revisadas'] == 0
    assert 'El intento no guardó cambios en la base' in result['detalle']
    assert 'red.lock' not in result['detalle']
    assert not (Path(result['directorio']) / 'PRECOMMIT_RESULTADOS.json').exists()


def test_recibo_de_datos_no_modifica_artefactos_ni_seleccion(tmp_path):
    from scripts.actualizar_partidos_local import recibo_nba
    from contextlib import nullcontext
    protected = tmp_path / 'estado/modelo_nba_activo.npz'
    protected.parent.mkdir(parents=True); protected.write_bytes(b'pesos-congelados')
    selection = tmp_path / 'estado/nba_exploratorio/seleccion.json'
    selection.parent.mkdir(); selection.write_text('{"version":2191}')
    class Conn:
        def transaction(self): return nullcontext()
        def execute(self, *_a): return self
        def fetchone(self): return (date(2026, 11, 6),)
    recibo_nba(Conn(), tmp_path, tmp_path/'run',
        {'aceptados': [], 'fuentes': [], 'sha256': 'plan'},
        [{'codigo':'nba','desde':'2026-11-01','hasta':'2026-11-06','insertados':0,
          'resultados_actualizados':1,'finales_fuente':2,'no_finales_excluidos':1,'incidencias':[]}], '2026-11-07T02:00:00Z')
    assert protected.read_bytes() == b'pesos-congelados'
    assert selection.read_text() == '{"version":2191}'
    receipt = json.loads((selection.parent/'ultima_revision.json').read_text())
    assert receipt['ultimo_final_validado'] == '2026-11-06'
    assert receipt['historico_integro_acreditado'] is False
    class SinFinal(Conn):
        def fetchone(self): return (None,)
    recibo_nba(SinFinal(), tmp_path, tmp_path/'run_parcial',
        {'aceptados': [], 'fuentes': [], 'sha256': 'plan-parcial'},
        [{'codigo':'nba','desde':'2026-11-01','hasta':'2026-11-06','insertados':0,
          'resultados_actualizados':0,'finales_fuente':0,'no_finales_excluidos':0,
          'incidencias':[{'motivo':'HTTP403'}]}], '2026-11-07T03:00:00Z')
    receipt = json.loads((selection.parent/'ultima_revision.json').read_text())
    assert receipt['ultimo_final_validado'] == '2026-11-06'
    assert receipt['estado'] == 'PARCIAL'
    assert protected.read_bytes() == b'pesos-congelados'
