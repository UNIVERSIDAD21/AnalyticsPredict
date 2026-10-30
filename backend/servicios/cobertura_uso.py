"""Inventario agregado de registros, no certificación del calendario ni del modelo."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row

BOGOTA = ZoneInfo('America/Bogota')


def leer_cobertura(conn, dias=365, ahora=None):
    if not 1 <= dias <= 1095:
        raise ValueError('Ventana entre 1 y 1095 días')
    ahora = ahora or datetime.now(timezone.utc)
    if ahora.tzinfo is None:
        raise ValueError('El instante de observación debe incluir zona')
    hasta = ahora.astimezone(BOGOTA)
    desde = datetime.combine(hasta.date() - timedelta(days=dias-1), time.min, BOGOTA)
    especificaciones = (
        ('baloncesto', 'competiciones_baloncesto', 'partidos_baloncesto',
         'p.valido IS TRUE AND p.local_total>0 AND p.visitante_total>0 AND p.local_total<>p.visitante_total',
         {'cuartos': ' AND '.join(f'p.{lado}_q{q} IS NOT NULL' for lado in ('local','visitante') for q in range(1,5))},
         desde.date(), hasta.date(), "WHERE c.codigo IN ('nba','wnba','euroleague')"),
        ('futbol', 'competiciones_futbol', 'partidos_futbol',
         "p.valido IS TRUE AND p.estado='FINALIZADO' AND p.local_goles_total IS NOT NULL AND p.visitante_goles_total IS NOT NULL",
         {'corners': 'p.local_corners_total IS NOT NULL AND p.visitante_corners_total IS NOT NULL',
          'disparos_arco': 'p.local_disparos_arco IS NOT NULL AND p.visitante_disparos_arco IS NOT NULL'},
         desde, hasta, ''),
    )
    filas = []
    with conn.cursor(row_factory=dict_row) as c:
        for deporte, catalogo, tabla, final, campos, inicio, fin, filtro in especificaciones:
            # Solo identificadores constantes de este módulo; fechas parametrizadas.
            completos = ','.join(f'count(p.id) FILTER(WHERE {final} AND ({condicion})) AS completos_{nombre}' for nombre, condicion in campos.items())
            c.execute(f'''SELECT c.id::text competicion_id,c.codigo,c.nombre,
                count(p.id) registros,
                count(p.id) FILTER(WHERE {final}) finales_con_marcador,
                max(p.fecha_partido) FILTER(WHERE {final}) ultimo_final,
                {completos}
                FROM {catalogo} c LEFT JOIN {tabla} p ON p.competicion_id=c.id
                  AND p.fecha_partido >= %s AND p.fecha_partido <= %s
                {filtro} GROUP BY c.id,c.codigo,c.nombre ORDER BY c.codigo''', (inicio, fin))
            for fila in c.fetchall():
                fila['liga'] = 'futbol' if deporte == 'futbol' else {'euroleague': 'euroliga'}.get(fila['codigo'], fila['codigo'])
                fila['completos_por_campo'] = {nombre: fila.pop('completos_'+nombre) for nombre in campos}
                filas.append(fila)
    return {'formato': 'cobertura-registros-v1', 'observado_en': ahora.astimezone(timezone.utc),
            'ventana': {'desde': desde, 'hasta': hasta, 'dias': dias, 'zona': 'America/Bogota'},
            'competiciones': filas, 'calendario_oficial_completo': None,
            'criterio': 'Registros existentes dentro de la ventana; cero no acredita ausencia de partidos. Campos presentes no acreditan coherencia, elegibilidad, frescura de fuente ni aptitud del modelo. Baloncesto tiene fecha diaria, sin hora certificada.'}
