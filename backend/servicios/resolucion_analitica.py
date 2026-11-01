"""Diagnóstico READ ONLY y resolución explícita de registros analíticos.

No ingiere resultados, no instala tablas, no modifica apuestas financieras y nunca
reabre registros finalizados. La comparación de históricos solo es diagnóstica.
"""
from collections import Counter

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from db import obtener_pool
from motor.resolucion_analitica import evaluar, POLITICA


def procesar(*, pool=None, simular=True, limite=1000, ids=None, auditar_finalizadas=False):
    if not 1 <= limite <= 20000:
        raise ValueError('Límite entre 1 y 20000 por deporte')
    if auditar_finalizadas and not simular:
        raise ValueError('Las finalizadas solo admiten auditoría sin escritura')
    resumen = {'politica': POLITICA, 'simulacion': simular, 'baloncesto': 0, 'futbol': 0,
               'total': 0, 'examinadas': 0, 'pendientes': 0, 'errores': 0,
               'motivos': {}, 'detalles': [], 'diferencias_historicas': 0,
               'historicas_comparables': 0, 'historicas_no_comparables': 0,
               'limite_por_deporte': limite, 'posiblemente_parcial': False,
               'certificacion': 'NO_CERTIFICADO'}
    motivos = Counter()
    with (pool or obtener_pool()).connection() as conn:
        with conn.cursor(row_factory=dict_row) as c:
            if simular:
                c.execute('SET TRANSACTION READ ONLY')
            ahora = c.execute('SELECT clock_timestamp() ahora').fetchone()['ahora']
            for deporte, tabla in (('baloncesto', 'partidos_baloncesto'), ('futbol', 'partidos_futbol')):
                liga = 'cp.codigo' if deporte == 'baloncesto' else "'futbol'"
                join = 'LEFT JOIN competiciones_baloncesto cp ON cp.id=p.competicion_id' if deporte == 'baloncesto' else ''
                estados = ['PENDIENTE', 'FINALIZADA'] if auditar_finalizadas else ['PENDIENTE']
                sql = f'''SELECT to_jsonb(a) registro,to_jsonb(p) partido,{liga} liga
                    FROM apuestas_analizadas a LEFT JOIN {tabla} p ON p.id=a.partido_id
                    {join} WHERE a.deporte=%s AND a.estado=ANY(%s)'''
                params = [deporte, estados]
                if ids is not None:
                    sql += ' AND a.id=ANY(%s::bigint[])'
                    params.append(list(ids))
                sql += ' ORDER BY a.id LIMIT %s'
                params.append(limite)
                if not simular:
                    sql += ' FOR UPDATE OF a SKIP LOCKED'
                filas = c.execute(sql, params).fetchall()
                resumen['posiblemente_parcial'] |= len(filas) == limite
                for fila in filas:
                    r = fila['registro']
                    resumen['examinadas'] += 1
                    cierre, motivo = evaluar(r, fila['partido'], fila['liga'], ahora)
                    if r['estado'] == 'PENDIENTE' and (r.get('valor_real') is not None or r.get('resultado_outcome') is not None):
                        cierre, motivo = None, 'PENDIENTE_CON_OUTCOME_PREVIO_REQUIERE_REVISION'
                    d = {'id': r['id'], 'deporte': deporte, 'mercado': r.get('mercado'),
                         'estado_guardado': r['estado'], 'resoluble': cierre is not None,
                         'valor_guardado': r.get('valor_real'), 'outcome_guardado': r.get('resultado_outcome'),
                         'motivo': motivo, 'propuesta': cierre}
                    if r['estado'] == 'FINALIZADA':
                        coincide = None if cierre is None else (cierre['valor_real'] == r.get('valor_real')
                                        and cierre['resultado_outcome'] == r.get('resultado_outcome'))
                        d['coincide_con_guardado'] = coincide
                        resumen['historicas_no_comparables' if cierre is None else 'historicas_comparables'] += 1
                        if coincide is False:
                            resumen['diferencias_historicas'] += 1
                    elif motivo:
                        resumen['pendientes'] += 1
                        motivos[motivo] += 1
                    else:
                        try:
                            if not simular:
                                with conn.transaction():
                                    c.execute('''UPDATE apuestas_analizadas SET estado='FINALIZADA',
                                        valor_real=%s,resultado_outcome=%s,resultado_resumen=%s,
                                        payload=jsonb_set(CASE WHEN jsonb_typeof(payload)='object' THEN payload
                                          ELSE jsonb_build_object('payload_original',payload) END,
                                          '{resolucion_analitica}',%s,true),actualizado_en=clock_timestamp()
                                        WHERE id=%s AND estado='PENDIENTE'
                                          AND valor_real IS NULL AND resultado_outcome IS NULL''',
                                        (cierre['valor_real'], cierre['resultado_outcome'],
                                         f"{r['mercado']}: {cierre['valor_real']} ({cierre['relacion_linea']})",
                                         Jsonb(cierre), r['id']))
                                    if c.rowcount != 1:
                                        raise RuntimeError('Registro cambió durante resolución')
                            resumen[deporte] += 1
                            resumen['total'] += 1
                        except Exception:
                            resumen['errores'] += 1
                            d['motivo'] = 'ERROR_ESCRITURA_REGISTRO_CONSERVADO'
                    resumen['detalles'].append(d)
            resumen['motivos'] = dict(motivos)
    return resumen
