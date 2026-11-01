"""Inventario operativo agregado. Solo SELECT y lectura de artefactos locales."""
from calendar import monthrange
from datetime import datetime
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row

from motor.euroliga import cargar as cargar_euroliga
from servicios.predictor_wnba import cargar as cargar_wnba
from servicios.calidad_futbol import leer_elegibilidad

BOGOTA = ZoneInfo('America/Bogota')
BB_FINAL = 'p.valido AND p.local_total > 0 AND p.visitante_total > 0 AND p.local_total <> p.visitante_total'
FT_FINAL = "p.valido AND p.estado='FINALIZADO' AND p.local_goles_total IS NOT NULL AND p.visitante_goles_total IS NOT NULL"
BB_CAMPOS = tuple(f'{lado}_{q}' for lado in ('local', 'visitante') for q in ('q1', 'q2', 'q3', 'q4', 'ot', 'total'))
FT_CAMPOS = tuple(f'{lado}_{q}' for lado in ('local', 'visitante') for q in ('goles_total', 'corners_total', 'disparos_arco'))


def ventana_calendario(ahora=None):
    ahora = (ahora or datetime.now(BOGOTA)).astimezone(BOGOTA)
    mes = ahora.year * 12 + ahora.month - 1 + 3
    anio, m = divmod(mes, 12)
    hasta = ahora.replace(year=anio, month=m+1, day=min(ahora.day, monthrange(anio, m+1)[1]))
    return ahora, hasta


def _inventario(c, tabla, catalogo, filtro, campos, desde, hasta, baloncesto=False):
    # Identificadores proceden exclusivamente de las constantes del módulo.
    faltantes = ','.join(f'count(*) FILTER(WHERE {filtro} AND p.{campo} IS NULL) AS falta_{campo}' for campo in campos)
    fecha = 'p.fecha_partido'
    proximo = (f'p.fecha_partido >= %s::date AND p.fecha_partido <= %s::date AND p.valido IS NOT FALSE AND NOT COALESCE(({filtro}),false)' if baloncesto
               else "p.fecha_partido >= %s AND p.fecha_partido <= %s AND p.valido IS NOT FALSE AND p.estado IN ('PROGRAMADO','POSPUESTO')")
    extra = "WHERE c.codigo IN ('nba','wnba','euroleague')" if baloncesto else ''
    filas = c.execute(f'''SELECT c.codigo,c.nombre,count(p.id) registros,
        count(*) FILTER(WHERE {filtro}) finales_con_marcador,
        max({fecha}) FILTER(WHERE {filtro}) ultimo_final,
        count(*) FILTER(WHERE p.valido IS FALSE) invalidados,
        count(*) FILTER(WHERE {proximo}) proximos_registrados,
        {faltantes}
        FROM {catalogo} c LEFT JOIN {tabla} p ON p.competicion_id=c.id
        {extra} GROUP BY c.id,c.codigo,c.nombre ORDER BY c.codigo''', (desde, hasta)).fetchall()
    for fila in filas:
        fila['faltantes_por_campo'] = {campo: fila.pop(f'falta_{campo}') for campo in campos}
        fila['calendario'] = {'estado': 'REGISTROS_LOCALES', 'proximos': fila.pop('proximos_registrados'), 'completo_acreditado': False}
    return filas


def modelo_local(cargar, liga):
    try:
        m = cargar()
        if liga == 'wnba':
            ajuste = m['ajuste_final']
            return {'estado': 'DISPONIBLE', 'version': m['version'], 'ultimo_dato': ajuste['fecha_max'],
                    'partidos': ajuste['n'], 'calibracion': 'SIN_CALIBRAR',
                    'alcance': 'Publicación REG; el análisis reajusta en memoria las temporadas elegidas.'}
        return {'estado': 'DISPONIBLE', 'version': m['version'], 'ultimo_dato': m['fecha_max'],
                'partidos': m['partidos_entrenamiento'], 'calibracion': 'SIN_CALIBRAR',
                'alcance': 'Artefacto local Euroliga.'}
    except FileNotFoundError:
        return {'estado': 'NO_DISPONIBLE', 'calibracion': 'NO_VERIFICADA'}
    except (ValueError, RuntimeError, OSError, KeyError, TypeError):
        return {'estado': 'NO_DISPONIBLE_O_NO_APTO', 'calibracion': 'NO_VERIFICADA'}


def leer_competiciones(conn, ahora=None):
    desde, hasta = ventana_calendario(ahora)
    with conn.cursor(row_factory=dict_row) as c:
        basket = _inventario(c, 'partidos_baloncesto', 'competiciones_baloncesto', BB_FINAL, BB_CAMPOS, desde.date(), hasta.date(), True)
        futbol = _inventario(c, 'partidos_futbol', 'competiciones_futbol', FT_FINAL, FT_CAMPOS, desde, hasta)
        por_codigo = {r['codigo']: r for r in basket}
        wnba = por_codigo.get('wnba')
        if wnba is not None:
            wnba['calendario'] = {'estado': 'ALMACEN_NO_INSTALADO', 'proximos': None, 'completo_acreditado': False}
            if c.execute("SELECT to_regclass('public.fixtures_wnba') tabla").fetchone()['tabla']:
                resumen = c.execute("""SELECT count(*) n,
                    count(*) FILTER(WHERE registro->>'condicional'='true') condicionales FROM fixtures_wnba
                    WHERE fecha_local BETWEEN %s AND %s AND estado IN ('PROGRAMADO','EN_VIVO','POSPUESTO','DEMORADO','SUSPENDIDO')
                    AND (inicio_utc IS NULL OR inicio_utc BETWEEN %s AND %s)""", (desde.date(), hasta.date(), desde, hasta)).fetchone()
                wnba['calendario'].update(estado='REGISTROS_LOCALES', proximos=resumen['n'], condicionales=resumen['condicionales'])
            if c.execute("SELECT to_regclass('public.comprobaciones_calendario_wnba') tabla").fetchone()['tabla']:
                comprobacion = c.execute('SELECT desde,hasta,comprobado_utc FROM comprobaciones_calendario_wnba ORDER BY comprobado_utc DESC LIMIT 1').fetchone()
                wnba['calendario']['ultima_comprobacion'] = comprobacion
        for codigo, cargar in (('wnba', cargar_wnba), ('euroleague', cargar_euroliga)):
            if codigo in por_codigo:
                por_codigo[codigo]['modelo'] = modelo_local(cargar, codigo)
    if futbol:
        calidad = leer_elegibilidad(conn, desde)
        # El ID se resuelve por catálogo, no por nombres de competición.
        with conn.cursor(row_factory=dict_row) as c:
            catalogo = c.execute('SELECT id,codigo FROM competiciones_futbol').fetchall()
        por_id = {r['codigo']: str(r['id']) for r in catalogo}
        for fila in futbol:
            fila['elegibilidad'] = calidad.get(por_id[fila['codigo']], {
                'finales_validos': 0, 'finales_sin_ft': 0, 'mercados': {}, 'por_temporada': [],
                'criterio': 'Sin finales anteriores al corte; no hay muestra acreditada.', 'corte': desde.isoformat(),
            })
    return {'baloncesto': por_codigo, 'futbol': futbol,
            'ventana_calendario': {'desde': desde, 'hasta': hasta, 'zona': 'America/Bogota'},
            'criterio': 'Campos faltantes medidos solo en finales válidos con marcador; cero publicado se conserva. No certifica integridad histórica ni elegibilidad del modelo. NBA y Euroliga tienen fecha diaria: el calendario puede incluir partidos de hoy sin hora.'}
