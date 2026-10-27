"""Agenda diaria de las tres ligas. Lectura local; nunca inventa horas ni FT."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row

from servicios.predictor_euroliga import conexion_lectura

BOGOTA = ZoneInfo('America/Bogota')
LIGAS = {'nba': 'NBA', 'euroleague': 'Euroliga', 'wnba': 'WNBA'}


def ahora():
    return datetime.now(BOGOTA)


def resumir(r, instante):
    inicio = r.get('inicio_utc')
    if inicio:
        inicio=inicio.astimezone(timezone.utc)
    fecha = inicio.astimezone(BOGOTA).date() if inicio else r['fecha_local']
    final = r['estado'] == 'FINALIZADO'
    pasado = inicio <= instante if inicio else fecha <= instante.date()
    reconstruccion = not inicio or pasado or r['estado']!='PROGRAMADO'
    permitido = pasado or r['estado'] == 'PROGRAMADO'
    return {
        **{k: str(r[k]) for k in ('id', 'equipo_local_id', 'equipo_visitante_id', 'temporada_id')},
        'liga': 'euroliga' if r['codigo'] == 'euroleague' else r['codigo'],
        'competicion_nombre': LIGAS[r['codigo']],
        'fecha_partido': fecha.isoformat(), 'inicio_utc': inicio.isoformat() if inicio else None,
        'precision_fecha': 'HORA' if inicio else 'DIA',
        'equipo_local_nombre': r['local'], 'equipo_visitante_nombre': r['visitante'],
        'temporada_nombre': r['temporada'], 'tipo_partido': r['fase'],
        'estado': r['estado'], 'condicional': bool(r.get('condicional')),
        'local_total': r['local_total'] if final else None,
        'visitante_total': r['visitante_total'] if final else None,
        'finalizado': final, 'analizable': permitido,
        'reconstruccion': reconstruccion,
        'fuente_verificada_en': r.get('observado_en').isoformat() if r.get('observado_en') else None,
        'actualizado_en': r['actualizado_en'].isoformat() if r.get('actualizado_en') else None,
    }


def consultar(fecha: date, liga='', buscar='', estado='todos', pagina=1, tamano=50):
    instante = ahora()
    desde = datetime.combine(fecha, datetime.min.time(), BOGOTA)
    hasta = desde + timedelta(days=1)
    with conexion_lectura() as conn, conn.cursor(row_factory=dict_row) as cur:
        # Compatibilidad de lectura antes de la migración aditiva: no ejecuta DDL.
        cur.execute("SELECT to_regclass('horarios_baloncesto') tabla")
        metadata = cur.fetchone()['tabla'] is not None
        join = 'LEFT JOIN horarios_baloncesto hb ON hb.partido_id=p.id' if metadata else 'LEFT JOIN (SELECT NULL::uuid partido_id,NULL::timestamptz inicio_utc,NULL::text estado,NULL::timestamptz observado_en,NULL::timestamptz actualizado_en) hb ON false'
        cur.execute("""
            SELECT DISTINCT ON (c.codigo,p.fecha_partido,p.equipo_local_id,p.equipo_visitante_id,p.tipo_partido)
              COALESCE(fx.id,p.id) id,c.codigo,p.fecha_partido fecha_local,
              COALESCE(hb.inicio_utc,fx.inicio_utc,fw.inicio_utc) inicio_utc,
              p.equipo_local_id,p.equipo_visitante_id,p.temporada_id,
              e.nombre local,v.nombre visitante,t.nombre temporada,p.tipo_partido fase,
              CASE WHEN p.local_total>0 AND p.visitante_total>0 THEN 'FINALIZADO'
                   ELSE COALESCE(hb.estado,fx.estado,fw.estado,'PROGRAMADO') END estado,
              p.local_total,p.visitante_total,GREATEST(p.actualizado_en,hb.actualizado_en,fx.actualizado_en) actualizado_en,
              COALESCE((fx.registro->>'condicional')::boolean,false) condicional,hb.observado_en
            FROM partidos_baloncesto p
            JOIN competiciones_baloncesto c ON c.id=p.competicion_id
            JOIN equipos e ON e.id=p.equipo_local_id
            JOIN equipos v ON v.id=p.equipo_visitante_id
            JOIN temporadas_baloncesto t ON t.id=p.temporada_id
            LEFT JOIN partidos_fuente_wnba fw ON fw.partido_id=p.id AND fw.competicion_id=c.id
            LEFT JOIN fixtures_wnba fx ON fx.resultado_id=p.id AND fx.competicion_id=c.id
            """ + join + """
            WHERE p.valido IS TRUE AND c.codigo IN ('nba','euroleague','wnba')
              AND p.tipo_partido IN ('PRE','REG','POST')
              AND (CASE WHEN COALESCE(hb.inicio_utc,fx.inicio_utc,fw.inicio_utc) IS NOT NULL
                   THEN COALESCE(hb.inicio_utc,fx.inicio_utc,fw.inicio_utc) >= %s AND COALESCE(hb.inicio_utc,fx.inicio_utc,fw.inicio_utc) < %s
                   ELSE p.fecha_partido=%s END)
            ORDER BY c.codigo,p.fecha_partido,p.equipo_local_id,p.equipo_visitante_id,p.tipo_partido,
                     (p.espn_game_id IS NOT NULL) DESC,p.actualizado_en DESC,p.id
        """, (desde, hasta, fecha))
        filas = cur.fetchall()
        cur.execute("""
            SELECT fx.id,c.codigo,fx.fecha_local,fx.inicio_utc,
              fx.equipo_local_id,fx.equipo_visitante_id,fx.temporada_id,
              e.nombre local,v.nombre visitante,t.nombre temporada,fx.fase,fx.estado,
              NULL::integer local_total,NULL::integer visitante_total,fx.actualizado_en,
              COALESCE((fx.registro->>'condicional')::boolean,false) condicional
            FROM fixtures_wnba fx
            JOIN competiciones_baloncesto c ON c.id=fx.competicion_id AND c.codigo='wnba'
            JOIN equipos e ON e.id=fx.equipo_local_id
            JOIN equipos v ON v.id=fx.equipo_visitante_id
            JOIN temporadas_baloncesto t ON t.id=fx.temporada_id
            WHERE fx.fase IN ('REG','POST')
              AND ((fx.inicio_utc >= %s AND fx.inicio_utc < %s)
                   OR (fx.inicio_utc IS NULL AND fx.fecha_local=%s))
              AND NOT EXISTS (SELECT 1 FROM partidos_baloncesto p
                              WHERE p.id=fx.resultado_id AND p.valido IS TRUE)
        """, (desde, hasta, fecha))
        filas.extend(cur.fetchall())
    partidos = [resumir(r, instante) for r in filas]
    partidos.sort(key=lambda p: (p['inicio_utc'] is None, p['inicio_utc'] or '', p['competicion_nombre'], p['equipo_local_nombre'], p['id']))
    if liga:
        partidos = [p for p in partidos if p['liga'] == liga]
    if buscar.strip():
        patron = buscar.strip().casefold()
        partidos = [p for p in partidos if patron in (p['equipo_local_nombre']+' '+p['equipo_visitante_nombre']).casefold()]
    if estado == 'finalizados':
        partidos = [p for p in partidos if p['finalizado']]
    elif estado == 'pendientes':
        partidos = [p for p in partidos if not p['finalizado']]
    cambios = [p['actualizado_en'] for p in partidos if p['actualizado_en']]
    return {'exito': True, 'fecha': fecha, 'zona_horaria': 'America/Bogota',
            'consultado_en': instante.isoformat(), 'datos_actualizados_en': max(cambios, default=None),
            'total': len(partidos), 'pagina': pagina, 'tamano': tamano,
            'competiciones': sorted({p['competicion_nombre'] for p in partidos}),
            'partidos': partidos[(pagina-1)*tamano:pagina*tamano]}
