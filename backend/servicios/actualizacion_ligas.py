"""Recordatorio de frescura desde datos y recibos persistentes; nunca ingiere."""
from datetime import date, datetime, timezone

from psycopg.rows import dict_row
from db import obtener_pool


# Los placeholders de baloncesto no tienen estado: se exigen FT y cuartos coherentes.
CONSULTA = """
SELECT c.codigo,c.nombre,'baloncesto' deporte,max(p.actualizado_en) cambio_en,
 (max(p.fecha_partido) FILTER (WHERE p.valido AND p.local_total>0 AND p.visitante_total>0
  AND p.local_total<>p.visitante_total AND p.fecha_partido<=(now() AT TIME ZONE 'America/Bogota')::date))::text resultados_hasta,
 (max(p.fecha_partido) FILTER (WHERE p.valido AND p.local_total>0 AND p.visitante_total>0
  AND p.local_total<>p.visitante_total AND p.fecha_partido<=(now() AT TIME ZONE 'America/Bogota')::date
  AND p.local_q1+p.local_q2+p.local_q3+p.local_q4+COALESCE(p.local_ot,0)=p.local_total
  AND p.visitante_q1+p.visitante_q2+p.visitante_q3+p.visitante_q4+COALESCE(p.visitante_ot,0)=p.visitante_total
  AND LEAST(p.local_q1,p.local_q2,p.local_q3,p.local_q4,p.visitante_q1,p.visitante_q2,p.visitante_q3,p.visitante_q4)>=0))::text estadisticas_hasta
FROM competiciones_baloncesto c LEFT JOIN partidos_baloncesto p ON p.competicion_id=c.id
GROUP BY c.id,c.codigo,c.nombre
UNION ALL
SELECT c.codigo,c.nombre,'futbol',max(p.actualizado_en),
 (max(p.fecha_partido) FILTER (WHERE p.valido AND p.estado::text='FINALIZADO'
  AND p.local_goles_total>=0 AND p.visitante_goles_total>=0 AND p.fecha_partido<=now()))::text,
 (max(p.fecha_partido) FILTER (WHERE p.valido AND p.estado::text='FINALIZADO'
  AND p.local_goles_total>=0 AND p.visitante_goles_total>=0 AND p.fecha_partido<=now()
  AND p.local_corners_total IS NOT NULL AND p.visitante_corners_total IS NOT NULL
  AND p.local_disparos_arco IS NOT NULL AND p.visitante_disparos_arco IS NOT NULL
  AND p.local_disparos_total IS NOT NULL AND p.visitante_disparos_total IS NOT NULL))::text
FROM competiciones_futbol c LEFT JOIN partidos_futbol p ON p.competicion_id=c.id
GROUP BY c.id,c.codigo,c.nombre ORDER BY deporte,codigo
"""


def combinar(ligas, agenda, integral, completa):
    """Un ciclo parcial o una fila reciente jamás certifican todas las ligas."""
    cobertura = {r['competicion']: r for r in (agenda or {}).get('resumen', {}).get('cobertura', [])}
    estadisticas = (integral or {}).get('resumen', {}).get('estadisticas', {})
    for liga in ligas:
        recibo = cobertura.get(liga['codigo'])
        liga['verificacion_agenda_en'] = agenda['terminado_en'] if recibo else None
        liga['estado_agenda'] = ('CON_INCIDENCIAS' if recibo.get('incidencias') else 'VERIFICADA') if recibo else 'SIN_ACREDITAR'
        liga['estadisticas'] = estadisticas.get(liga['codigo'], {'estado': 'SIN_ACREDITAR'})
    return {
        'consultado_en': datetime.now(timezone.utc).isoformat(),
        'ultimo_ciclo_agendas': {k: agenda[k] for k in ('terminado_en', 'estado')} if agenda else None,
        'ultimo_ciclo_integral': {k: integral[k] for k in ('terminado_en', 'estado')} if integral else None,
        'ultima_completa_en': completa['terminado_en'] if completa else None,
        'ligas': ligas,
    }


def obtener_actualizacion_ligas():
    with obtener_pool().connection() as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY; SET LOCAL statement_timeout='8s'")
            with conn.cursor(row_factory=dict_row) as cur:
                ligas = cur.execute(CONSULTA).fetchall()
                # La ausencia de un archivo de instalación no borra los recibos SQL.
                ledger = cur.execute("""SELECT terminado_en,estado,informe AS resumen FROM sincronizaciones_agenda
                    WHERE informe->>'tipo' IS DISTINCT FROM 'ACTUALIZACION_INTEGRAL'
                    ORDER BY terminado_en DESC LIMIT 1""").fetchone()
                integral = cur.execute("""SELECT terminado_en,estado,informe AS resumen FROM sincronizaciones_agenda
                    WHERE informe->>'tipo'='ACTUALIZACION_INTEGRAL'
                    ORDER BY terminado_en DESC LIMIT 1""").fetchone()
                completa = cur.execute("""SELECT terminado_en FROM sincronizaciones_agenda
                    WHERE informe->>'tipo'='ACTUALIZACION_INTEGRAL' AND estado='COMPLETO'
                    AND (informe->>'todas_ligas_verificadas')='true'
                    ORDER BY terminado_en DESC LIMIT 1""").fetchone()
    def plano(v):
        if isinstance(v, (datetime, date)): return v.isoformat()
        if isinstance(v, dict): return {k: plano(x) for k, x in v.items()}
        if isinstance(v, list): return [plano(x) for x in v]
        return v
    return plano(combinar(ligas, ledger, integral, completa))
