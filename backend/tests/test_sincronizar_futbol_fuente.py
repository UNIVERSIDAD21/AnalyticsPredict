"""Un proveedor bloqueado no se confunde con cero eventos ni escribe en dry-run."""

from scripts import sincronizar_futbol as sync


class Respuesta:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = payload or {}

    def json(self):
        return self.payload


def test_403_corta_sin_reintento_ni_sorteo(monkeypatch):
    cliente = sync.SofascoreClientInteligente(min_intervalo=0)
    llamadas = []
    monkeypatch.setattr(cliente.session, "get", lambda *args, **kwargs: llamadas.append(args) or Respuesta(403))
    try:
        assert cliente.get('/unique-tournament/8/seasons') is None
        assert len(llamadas) == 1
        assert cliente.total_bloqueos == 1
        assert cliente.fuente_no_disponible is True
        assert cliente.ultima_respuesta_exitosa_utc is None
    finally:
        cliente.cerrar()


def test_dry_run_observa_eventos_sin_crear_equipos_ni_partidos(monkeypatch):
    cliente = sync.SofascoreClientInteligente(min_intervalo=0)
    monkeypatch.setattr(sync, 'obtener_competicion_id', lambda *args: 'comp')
    monkeypatch.setattr(sync, 'obtener_temporada_activa', lambda *args: {
        'id': 'temporada', 'nombre': '2026-27', 'sofascore_season_id': 123,
    })
    monkeypatch.setattr(sync, 'obtener_partidos_pasados', lambda *args: [{'id': 1}])
    monkeypatch.setattr(sync, 'obtener_o_crear_equipo', lambda *args: (_ for _ in ()).throw(AssertionError('escritura')))
    monkeypatch.setattr(sync, 'insertar_o_actualizar_partido', lambda *args: (_ for _ in ()).throw(AssertionError('escritura')))
    try:
        resultado = sync.sincronizar_liga(None, cliente, 'laliga', 7, 0, False, True, dry_run=True)
        assert resultado['estado_fuente'] == 'OK'
        assert resultado['eventos_observados'] == 1
        assert resultado['insertados'] == resultado['actualizados'] == 0
    finally:
        cliente.cerrar()


def test_fuente_caida_no_es_no_data(monkeypatch):
    cliente = sync.SofascoreClientInteligente(min_intervalo=0)
    monkeypatch.setattr(sync, 'obtener_competicion_id', lambda *args: 'comp')
    monkeypatch.setattr(sync, 'obtener_temporada_activa', lambda *args: {
        'id': 'temporada', 'nombre': '2026-27', 'sofascore_season_id': 123,
    })

    def fallar(*args):
        cliente.fuente_no_disponible = True
        return []

    monkeypatch.setattr(sync, 'obtener_partidos_pasados', fallar)
    try:
        resultado = sync.sincronizar_liga(None, cliente, 'laliga', 7, 0, False, True, dry_run=True)
        assert resultado['estado_fuente'] == 'SOURCE_UNAVAILABLE'
        assert resultado['errores'] == 1
    finally:
        cliente.cerrar()


class CursorFalso:
    def __init__(self):
        self.consultas = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, parametros):
        self.consultas.append((sql, parametros))

    def fetchone(self):
        return None


class ConexionFalsa:
    def __init__(self):
        self.cursor_falso = CursorFalso()
        self.commits = 0

    def cursor(self):
        return self.cursor_falso

    def commit(self):
        self.commits += 1

    def rollback(self):
        raise AssertionError('rollback inesperado')


def test_gol_cero_no_se_sustituye_y_cobertura_estadistica_no_se_inventa():
    conn = ConexionFalsa()
    evento = {
        'id': 123, 'startTimestamp': 1790000000,
        'homeTeam': {'id': 1}, 'awayTeam': {'id': 2},
        'homeScore': {'current': 0, 'normaltime': 2},
        'awayScore': {'current': 1},
        'status': {'type': 'finished'},
    }
    assert sync.insertar_o_actualizar_partido(conn, evento, 'comp', 'temporada', {1: 'local', 2: 'visitante'}) == (True, True)
    parametros = conn.cursor_falso.consultas[-1][1]
    assert parametros[10] == 0  # homeScore.current; no fallback a 2
    assert parametros[13] == 1
    assert parametros[4].tzinfo is not None

    assert sync.actualizar_estadisticas_partido(conn, 123, {
        'disparos_local_total': 3, 'disparos_visitante_total': 0,
        'disparos_local_arco': 1, 'disparos_visitante_arco': 0,
    }) is True
    parametros = conn.cursor_falso.consultas[-1][1]
    assert parametros[-3:-1] == (False, True)
