"""Inventario READ ONLY por código/temporada; no certifica identidad ni eficacia."""
from uuid import uuid4
from psycopg.rows import dict_row
from calidad.elegibilidad_futbol import METRICAS, DERIVADAS, POLITICA, seleccionar, clasificar, Dato


def normalizar_estadistico(fila):
    """DTO histórico con el mismo criterio que el cálculo, sin alterar la fila."""
    datos = {k:fila[k] for k in ('id','fecha_partido','equipo_local_id','equipo_visitante_id','equipo_local','equipo_visitante')}
    for metrica in METRICAS:
        for lado in ('local','visitante'):
            base, periodo = metrica.rsplit('_',1)
            key = f'{base}_{lado}' + (f'_{periodo}' if periodo != 'ft' else '')
            datos[key] = clasificar(fila,metrica,lado).valor
    return datos


def _nuevo():
    return {'denominador': 0, 'observados': 0, 'estimados': 0, 'ausentes': 0, 'invalidos': 0,
            'ceros': 0, 'utilizables': 0, 'con_null': 0, 'motivos': {}, 'fecha_max': None}


def leer_elegibilidad(conn, corte):
    columnas = sorted({c for cols in METRICAS.values() for c in cols})
    seleccion = ','.join(f'p.{c}' for c in columnas)
    consulta = f'''SELECT p.competicion_id,p.temporada_id,t.nombre temporada,p.fecha_partido,
        p.valido,p.estado,p.hubo_tiempo_extra,p.local_goles_et,p.visitante_goles_et,{seleccion}
        FROM partidos_futbol p LEFT JOIN temporadas_futbol t ON t.id=p.temporada_id
        WHERE p.valido IS TRUE AND p.estado='FINALIZADO' AND p.fecha_partido<%s'''
    agregados, temporadas = {}, {}
    with conn.cursor(name='elegibilidad_' + uuid4().hex, row_factory=dict_row) as cur:
        cur.execute(consulta, (corte,))
        while filas := cur.fetchmany(5000):
            for p in filas:
                cid, tid = str(p['competicion_id']), str(p['temporada_id'])
                if cid not in agregados:
                    agregados[cid] = {'finales_validos': 0, 'finales_sin_ft': 0, 'mercados': {m:_nuevo() for m in (*METRICAS,*DERIVADAS)}}
                if (cid,tid) not in temporadas:
                    temporadas[cid,tid] = {'temporada_id': tid, 'temporada': p['temporada'], 'finales_validos': 0, 'finales_sin_ft': 0, 'mercados': {m:_nuevo() for m in (*METRICAS,*DERIVADAS)}}
                agregado, temp = agregados[cid], temporadas[cid,tid]
                fecha = p['fecha_partido'].isoformat()
                clasificados = {m:seleccionar(p,m) for m in METRICAS}
                for m in DERIVADAS:
                    base = clasificados[m.rsplit('_',1)[0]+'_ft']
                    clasificados[m] = Dato('ESTIMADO',None,'REPARTO_HEURISTICO_DESDE_FT') if base.estado=='OBSERVADO' else base
                con_ft = p['local_goles_total'] is not None and p['visitante_goles_total'] is not None
                for grupo in (agregado, temp):
                    grupo['finales_validos'] += 1
                    grupo['finales_sin_ft'] += int(not con_ft)
                for metrica in (*METRICAS, *DERIVADAS):
                    if metrica != 'goles_ft' and not con_ft:
                        continue
                    dato = clasificados[metrica]
                    con_null = any(p[c] is None for c in METRICAS.get(metrica, ()))
                    for grupo in (agregado, temp):
                        m = grupo['mercados'][metrica]
                        m['denominador'] += 1
                        m[{'OBSERVADO':'observados', 'ESTIMADO':'estimados', 'AUSENTE':'ausentes', 'INVALIDO':'invalidos'}[dato.estado]] += 1
                        m['con_null'] += int(con_null)
                        if dato.motivo:
                            m['motivos'][dato.motivo] = m['motivos'].get(dato.motivo, 0) + 1
                        if dato.estado in ('OBSERVADO', 'ESTIMADO'):
                            m['utilizables'] += 1
                            m['ceros'] += int(dato.valor == 0)
                            m['fecha_max'] = max(m['fecha_max'] or fecha, fecha)
    for cid, datos in agregados.items():
        datos.update(politica=POLITICA, corte=corte.isoformat(), identidad='CODIGO_GUARDADO_NO_RECERTIFICADO',
                     criterio='Goles FT: finales válidos; demás objetivos: finales con ambos goles FT. Observado significa utilizable por reglas, no dato externo recertificado. FT es regulación sin ET.',
                     por_temporada=sorted([t for (c,_),t in temporadas.items() if c==cid],key=lambda t: str(t['temporada'])))
        for metrica in (*METRICAS, *DERIVADAS):
            datos['mercados'].setdefault(metrica, _nuevo())
    return agregados
