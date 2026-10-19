"""Adaptador de finales oficiales Euroliga. Solo datos explícitos, sin entrenar."""
from datetime import date, datetime
from uuid import NAMESPACE_URL, uuid5
import re

from psycopg import sql
from psycopg.rows import dict_row

FUENTE = 'EUROLEAGUE_OFFICIAL'
COLUMNAS = (
    'id', 'temporada_id', 'competicion_id', 'fecha_partido', 'tipo_partido',
    'equipo_local_id', 'equipo_visitante_id',
    'local_q1', 'local_q2', 'local_q3', 'local_q4', 'local_ot', 'local_total',
    'visitante_q1', 'visitante_q2', 'visitante_q3', 'visitante_q4', 'visitante_ot', 'visitante_total',
    'ganador_id', 'diferencia_puntos', 'hubo_overtime', 'fuente_datos',
    'source', 'source_game_id', 'url_referencia', 'valido',
)


def interpretar_boxscore(juego, payload, equipos, temporadas, competicion_id):
    anio = int(juego['season'])
    codigo = juego['gamecode']
    if (juego.get('played') != 'true' or codigo != f"E{anio}_{int(juego['gamenumber'])}"
            or juego['homecode'] == juego['awaycode']):
        raise ValueError('Identidad o final oficial no acreditados')
    fecha = date.fromisoformat(juego['fecha'])
    if fecha > datetime.now().date():
        raise ValueError('Final oficial futuro')
    fases = {'RS': 'REG', 'PO': 'POST', 'FF': 'POST', 'PI': 'POST'}
    if juego.get('round') not in fases:
        raise ValueError('Fase Euroliga desconocida')
    if payload.get('Live') is not False:
        raise ValueError('Boxscore aún en vivo o sin estado')
    cuartos = payload.get('ByQuarter') or []
    stats = payload.get('Stats') or []
    if len(cuartos) != 2 or len(stats) != 2:
        raise ValueError('Cuartos o identidades de boxscore incompletos')
    por_nombre = {c.get('Team'): c for c in cuartos}
    por_codigo = {}
    for equipo in stats:
        codigos = {p.get('Team') for p in equipo.get('PlayersStats', []) if p.get('Team')}
        if len(codigos) != 1 or equipo.get('Team') not in por_nombre:
            raise ValueError('Equipo de cuartos sin código único')
        cod = next(iter(codigos))
        if cod in por_codigo:
            raise ValueError('Local y visitante ambiguos')
        por_codigo[cod] = por_nombre[equipo['Team']]
    if set(por_codigo) != {juego['homecode'], juego['awaycode']}:
        raise ValueError('Boxscore de otros equipos')
    r = {'id': str(uuid5(NAMESPACE_URL, 'euroleague:game:' + codigo)),
         'temporada_id': str(temporadas[anio]), 'competicion_id': str(competicion_id),
         'fecha_partido': fecha, 'tipo_partido': fases[juego['round']],
         'equipo_local_id': str(equipos[juego['homecode']]),
         'equipo_visitante_id': str(equipos[juego['awaycode']]),
         'fuente_datos': FUENTE, 'source': FUENTE, 'source_game_id': codigo,
         'url_referencia': f"https://live.euroleague.net/api/Boxscore?gamecode={int(juego['gamenumber'])}&seasoncode=E{anio}",
         'valido': True}
    for lado, cod, total in (('local', juego['homecode'], juego['homescore']),
                              ('visitante', juego['awaycode'], juego['awayscore'])):
        fila = por_codigo[cod]
        valores = [fila.get('Quarter' + str(i)) for i in range(1, 5)]
        claves_extra = sorted((k for k in fila if re.fullmatch(r'Extra[1-9][0-9]*', k)),
                              key=lambda k: int(k[5:]))
        if claves_extra and claves_extra != ['Extra' + str(i) for i in range(1, len(claves_extra)+1)]:
            raise ValueError('Prórrogas discontinuas')
        extras = [fila[k] for k in claves_extra]
        if any(type(v) is not int or v < 0 for v in valores + extras):
            raise ValueError('Puntos por cuarto/OT ausentes o inválidos')
        total = int(total)
        if total <= 0 or sum(valores) + sum(extras) != total:
            raise ValueError('Cuartos/OT y resultado oficial no concilian')
        r.update({lado + '_q' + str(i): v for i, v in enumerate(valores, 1)})
        r[lado + '_ot'] = sum(extras)
        r[lado + '_total'] = total
    if r['local_total'] == r['visitante_total']:
        raise ValueError('Final de baloncesto empatado')
    r.update(ganador_id=r['equipo_local_id'] if r['local_total'] > r['visitante_total'] else r['equipo_visitante_id'],
             diferencia_puntos=r['local_total']-r['visitante_total'],
             hubo_overtime=bool(r['local_ot'] or r['visitante_ot']))
    return r


def insertar_finales(conn, registros):
    """Idempotente y atómico; jamás sobrescribe un resultado histórico distinto."""
    insertados = 0
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        for r in registros:
            if set(r) != set(COLUMNAS) or r['source'] != FUENTE or r['valido'] is not True:
                raise ValueError('Registro oficial incompleto o de otra fuente')
            for lado in ('local', 'visitante'):
                valores=[r[lado+'_q'+str(i)] for i in range(1,5)]+[r[lado+'_ot']]
                if any(type(v) is not int or v<0 for v in valores) or sum(valores)!=r[lado+'_total']:
                    raise ValueError('Registro sin cuartos/FT coherentes')
            previos = cur.execute('''SELECT * FROM partidos_baloncesto
                WHERE (source=%s AND source_game_id=%s) OR
                    (competicion_id=%s AND temporada_id=%s AND fecha_partido=%s
                     AND equipo_local_id=%s AND equipo_visitante_id=%s)''',
                (FUENTE,r['source_game_id'],r['competicion_id'],r['temporada_id'],r['fecha_partido'],
                 r['equipo_local_id'],r['equipo_visitante_id'])).fetchall()
            if previos:
                identidad=('competicion_id','temporada_id','equipo_local_id','equipo_visitante_id')
                if (len(previos)!=1 or any(str(previos[0][c])!=str(r[c]) for c in identidad)
                        or previos[0]['tipo_partido']!=r['tipo_partido']
                        or any(previos[0][c]!=r[c] for c in
                    ('fecha_partido','local_q1','local_q2','local_q3','local_q4','local_ot','local_total',
                     'visitante_q1','visitante_q2','visitante_q3','visitante_q4','visitante_ot','visitante_total'))):
                    raise ValueError('Final existente contradictorio; requiere conciliación separada')
                continue
            consulta=sql.SQL('INSERT INTO partidos_baloncesto ({}) VALUES ({}) RETURNING id').format(
                sql.SQL(',').join(map(sql.Identifier,COLUMNAS)),
                sql.SQL(',').join(sql.Placeholder() for _ in COLUMNAS))
            cur.execute(consulta,[r[c] for c in COLUMNAS])
            insertados+=int(cur.fetchone() is not None)
    return {'insertados':insertados,'existentes':len(registros)-insertados,'eventos':len(registros)}
