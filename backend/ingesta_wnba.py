"""Ingesta exclusivamente local WNBA. Sin HTTP, entrenamiento ni serving.

Los resultados compartidos solo reciben finales; los no finales quedan en la tabla
fuente con sus NULL originales. Un ID publicado con otra versión es conflicto, no
permiso para reemplazar datos. La transacción pertenece al llamador.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

MIGRACION = Path(__file__).parent / 'migrations/2026-10-25_ingesta_wnba.sql'
BOGOTA = ZoneInfo('America/Bogota')
ESTADOS = {'FINALIZADO', 'PROGRAMADO', 'POSPUESTO', 'CANCELADO', 'EN_VIVO', 'DEMORADO', 'SUSPENDIDO'}
METRICAS = {'asistencias', 'campo_anotados', 'campo_intentados', 'faltas',
            'libres_anotados', 'libres_intentados', 'perdidas_equipo', 'perdidas_jugadoras',
            'perdidas_totales', 'rebotes', 'rebotes_defensivos', 'rebotes_ofensivos',
            'robos', 'tapones', 'triples_anotados', 'triples_intentados'}
PUNTOS = tuple(f'{lado}_{k}' for lado in ('local', 'visitante')
               for k in ('q1', 'q2', 'q3', 'q4', 'regulacion', 'ot', 'total', 'prorrogas'))


def exigir(ok, mensaje):
    if not ok:
        raise ValueError(mensaje)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonico(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def huella(value) -> str:
    return digest(canonico(value).encode())


def uid(clase, value) -> str:
    return str(uuid5(NAMESPACE_URL, f'AnalyticsPredict:wnba:ESPN:{clase}:{value}'))


def numero(value):
    return type(value) is int and value >= 0


def alias_tecnico(tid, usados):
    """Etiqueta interna de tres caracteres; nunca abreviatura oficial inferida.

    El ID/identidad vive en el vínculo ESPN de la competición. Resuelve colisiones
    con etiquetas existentes sin cambiarlas ni tocar una vista dependiente legacy.
    """
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    start = int(huella(['wnba','ESPN',tid])[:8],16) % 1296
    for step in range(1296):
        n = (start+step) % 1296
        alias = 'W'+alphabet[n//36]+alphabet[n%36]
        if alias not in usados:
            return alias
    raise ValueError('No hay alias técnico WNBA libre en el catálogo legacy')


def instante(value):
    exigir(isinstance(value, str), 'Instante ausente')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    exigir(dt.tzinfo is not None, 'Instante sin zona')
    return dt


def validar_registro(r):
    exigir(isinstance(r, dict), 'Registro no es objeto')
    exigir(r.get('competicion') == 'wnba' and r.get('fuente') == 'ESPN'
           and r.get('contrato') == 'espn_wnba_v1', 'Competición/fuente/contrato incompatible')
    for k in ('source_game_id', 'local_id_fuente', 'visitante_id_fuente'):
        exigir(isinstance(r.get(k), str) and re.fullmatch(r'[0-9]{1,20}', r[k]), f'ID inválido: {k}')
    exigir(r['local_id_fuente'] != r['visitante_id_fuente'], 'Equipos iguales')
    for lado in ('local', 'visitante'):
        exigir(isinstance(r.get(lado+'_nombre'), str) and 0 < len(r[lado+'_nombre'].strip()) <= 50,
               'Nombre ausente o fuera del catálogo')
    dt = instante(r.get('inicio_utc'))
    cot = instante(r.get('inicio_colombia'))
    exigir(dt.utcoffset().total_seconds() == 0 and cot == dt
           and cot.utcoffset() == dt.astimezone(BOGOTA).utcoffset(), 'Fecha UTC/Colombia discordante')
    exigir(type(r.get('temporada')) is int and r['temporada'] >= 2006
           and dt.astimezone(BOGOTA).year == r['temporada'], 'Temporada anual inválida')
    exigir(r.get('duracion_regulacion_minutos') == 40, 'Regulación distinta de 40 minutos')
    exigir(r.get('estado') in ESTADOS and r.get('fase') in {'PRE', 'REG', 'POST', 'COPA'}, 'Estado/fase inválido')
    exigir(r.get('final_completo') is (r['estado'] == 'FINALIZADO'), 'Estado final contradictorio')
    exigir(isinstance(r.get('sede_neutral'), bool) or r.get('sede_neutral') is None, 'Sede inválida')
    exigir(isinstance(r.get('evidencia'), list) and r['evidencia'], 'Sin evidencia')
    exigir(r.get('url_fuente') == f"https://www.espn.com/wnba/game/_/gameId/{r['source_game_id']}", 'URL de otro evento')
    for e in r['evidencia']:
        exigir(isinstance(e, dict) and re.fullmatch(r'[0-9a-f]{64}', str(e.get('sha256', '')))
               and isinstance(e.get('url'), str) and e['url'].startswith('https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/'),
               'Procedencia incompleta')
        obs = instante(e.get('observado_utc'))
        if r['final_completo']:
            exigir(obs >= dt, 'Final observado antes de inicio')
    exigir(isinstance(r.get('incidencias_estadisticas', []), list), 'Incidencias no son lista')
    if not r['final_completo']:
        exigir(all(k in r and r[k] is None for k in PUNTOS), 'No final con puntos inventados')
        exigir(r.get('ganador_id_fuente') is None and r.get('numero_prorrogas') is None
               and r.get('estadisticas') is None, 'No final con resultado inventado')
        return
    n = r.get('numero_prorrogas')
    exigir(numero(n) and n <= 16, 'Número OT inválido')
    for lado in ('local', 'visitante'):
        exigir(all(k in r and numero(r[k]) for k in PUNTOS if k.startswith(lado+'_') and not k.endswith('_prorrogas')),
               'Puntos finales incompletos')
        ot = r[lado+'_prorrogas']
        exigir(isinstance(ot, list) and len(ot) == n and all(numero(p) for p in ot), 'Detalle OT inválido')
        exigir(sum(r[f'{lado}_q{i}'] for i in range(1, 5)) == r[lado+'_regulacion']
               and sum(ot) == r[lado+'_ot'] and r[lado+'_regulacion'] + sum(ot) == r[lado+'_total']
               and r[lado+'_total'] > 0, 'Suma de marcadores discordante')
    exigir(r['local_total'] != r['visitante_total'], 'Final con empate')
    ganador = 'local' if r['local_total'] > r['visitante_total'] else 'visitante'
    exigir(r.get('ganador_id_fuente') == r[ganador+'_id_fuente'], 'Ganador discordante')
    for i in range(n):
        exigir(r['local_regulacion'] + sum(r['local_prorrogas'][:i]) ==
               r['visitante_regulacion'] + sum(r['visitante_prorrogas'][:i]), 'OT sin empate previo')
    stats = r.get('estadisticas')
    exigir(isinstance(stats, dict) and set(stats) == {'home', 'away'}, 'Estadísticas incompletas')
    for side, lado in (('home', 'local'), ('away', 'visitante')):
        s = stats[side]
        exigir(isinstance(s, dict) and set(s) == METRICAS
               and all(v is None or numero(v) for v in s.values()), 'Métrica inválida')
        for tiro in ('campo', 'triples', 'libres'):
            a, b = s[tiro+'_anotados'], s[tiro+'_intentados']
            if a is not None and b is not None:
                exigir(a <= b, 'Tiros inconsistentes')
        fg, th, ft = (s[k+'_anotados'] for k in ('campo', 'triples', 'libres'))
        if fg is not None and th is not None:
            exigir(th <= fg, 'Triples superan campo')
        if None not in (fg, th, ft):
            exigir(2*fg+th+ft == r[lado+'_total'], 'Tiros no concilian FT')
        reb = [s[k] for k in ('rebotes', 'rebotes_ofensivos', 'rebotes_defensivos')]
        if None not in reb:
            exigir(reb[0] == reb[1]+reb[2], 'Rebotes inconsistentes')
        a, b, c = (s[k] for k in ('perdidas_jugadoras', 'perdidas_equipo', 'perdidas_totales'))
        if None not in (a, c):
            exigir(c >= a and (b is None or a+b == c), 'Pérdidas inconsistentes')
    for issue in r.get('incidencias_estadisticas', []):
        exigir(isinstance(issue, dict) and issue.get('lado') in stats
               and issue.get('campo') in METRICAS and stats[issue['lado']][issue['campo']] is None,
               'Campo apartado no permanece NULL')


def leer_lote(carpeta: Path) -> dict:
    carpeta = carpeta.resolve()
    hashes, contents = {}, {}
    for line in (carpeta/'SHA256SUMS').read_text().splitlines():
        m = re.fullmatch(r'([0-9a-f]{64})  ([a-zA-Z0-9_.-]+)', line)
        exigir(m is not None, 'Manifiesto inválido')
        expected, name = m.groups()
        path = carpeta/name
        exigir(name not in hashes and not path.is_symlink() and path.is_file(), 'Archivo ambiguo')
        raw = path.read_bytes()
        exigir(digest(raw) == expected, f'Hash discordante: {name}')
        hashes[name], contents[name] = expected, raw
    needed = {'partidos.jsonl', 'partidos.csv', 'reporte.json', 'cuarentena.jsonl',
              'pendientes.jsonl', 'advertencias_estadisticas.jsonl'}
    exigir(needed <= hashes.keys(), 'Faltan archivos del contrato')
    def jsonl(name):
        return [json.loads(line) for line in contents[name].splitlines() if line.strip()]
    report = json.loads(contents['reporte.json'])
    exigir(report.get('estado') in {'COMPLETO_EN_VENTANA_ESPN', 'COMPLETO_CON_INCIDENCIAS', 'CON_CUARENTENA'}
           and not report.get('ventanas_pendientes') and not report.get('error'), 'Recorrido incompleto')
    seen, by_natural = {}, {}
    duplicated = 0
    start, end = date.fromisoformat(report['desde']), date.fromisoformat(report['hasta'])
    rows = jsonl('partidos.jsonl')
    for r in rows:
        validar_registro(r)
        exigir(start <= instante(r['inicio_utc']).astimezone(BOGOTA).date() <= end, 'Fuera de ventana')
        eid = r['source_game_id']
        if eid in seen:
            exigir(seen[eid] == r, 'ID duplicado conflictivo')
            duplicated += 1
        if r['final_completo']:
            natural = (r['temporada'], r['inicio_colombia'][:10], r['fase'], r['local_id_fuente'], r['visitante_id_fuente'])
            exigir(natural not in by_natural or by_natural[natural] == eid, 'Final duplicado con otro ID')
            by_natural[natural] = eid
        seen[eid] = r
    quarantine = jsonl('cuarentena.jsonl')
    exigir(not ({r.get('source_game_id') for r in quarantine} & seen.keys()), 'Cuarentena dentro de aceptados')
    exigir(report.get('partidos_exportados') == len(rows)
           and report.get('finales_completos') == sum(r['final_completo'] for r in rows)
           and report.get('no_finales') == sum(not r['final_completo'] for r in rows)
           and report.get('incidencias_cuarentena') == len(quarantine), 'Conteos del reporte discordantes')
    return {'sha256': hashes['partidos.jsonl'], 'archivos': hashes, 'reporte': report,
            'registros': list(seen.values()), 'cuarentena': quarantine, 'duplicados_entrada': duplicated,
            'pendientes_fuente': jsonl('pendientes.jsonl'),
            'advertencias_estadisticas': jsonl('advertencias_estadisticas.jsonl')}


def resumen(lote):
    rs = lote['registros']
    return {'aceptados': len(rs), 'finales': sum(r['final_completo'] for r in rs),
            'no_finales': sum(not r['final_completo'] for r in rs), 'cuarentena': len(lote['cuarentena']),
            'duplicados_entrada': lote['duplicados_entrada'], 'por_temporada': dict(Counter(str(r['temporada']) for r in rs)),
            'por_estado': dict(Counter(r['estado'] for r in rs)), 'por_fase': dict(Counter(r['fase'] for r in rs))}


def _filas(conn, sql, params=()):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def importar(conn, lote):
    """Sin commit implícito. Requiere migración aplicada; conflicto => revertir todo.

    Solo inserta o reconoce equivalencia exacta. No actualiza versiones publicadas.
    """
    conn.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:wnba:import'))")
    rs = lote['registros']; result = {**resumen(lote), 'insertados': 0, 'ya_existentes': 0,
         'actualizados': 0, 'resultados_insertados': 0, 'resultados_existentes': 0,
         'equipos_creados': 0, 'temporadas_creadas': 0, 'competiciones_creadas': 0,
         'omitidos': len(lote['cuarentena']), 'pendientes_resultado': sum(not r['final_completo'] for r in rs)}
    comps = _filas(conn, "SELECT id::text,espn_league_id FROM public.competiciones_baloncesto WHERE codigo='wnba'")
    if comps:
        exigir(len(comps) == 1 and comps[0]['espn_league_id'] == 'wnba', 'Competición existente incompatible')
        cid = comps[0]['id']
    else:
        cid = uid('competicion', 'wnba')
        conn.execute("""INSERT INTO public.competiciones_baloncesto
            (id,nombre,nombre_corto,codigo,tipo,espn_league_id,formato_competicion,tiene_playoffs,activo)
            VALUES (%s,'Women’s National Basketball Association','WNBA','wnba','LIGA_PROFESIONAL',
                    'wnba','anual;pre+regular+playoffs+copa',true,true)""", (cid,))
        result['competiciones_creadas'] = 1
    teams = {}
    for r in rs:
        for lado in ('local', 'visitante'):
            tid, name = r[lado+'_id_fuente'], r[lado+'_nombre']
            exigir(tid not in teams or teams[tid] == name, 'Nombre de ID ambiguo; requiere crosswalk explícito')
            teams[tid] = name
    dbteams = _filas(conn, "SELECT id::text,espn_team_id,nombre FROM public.equipos_baloncesto WHERE competicion_principal_id=%s", (cid,))
    mapped = {}
    for t in dbteams:
        if t['espn_team_id'] in teams:
            exigir(t['espn_team_id'] not in mapped and t['nombre'] == teams[t['espn_team_id']], 'Identidad de equipo ambigua')
            mapped[t['espn_team_id']] = t['id']
    legacy = {r['id']: r for r in _filas(conn, 'SELECT id::text,nombre,abreviatura,competicion_principal_id::text FROM public.equipos')}
    usados = {r['abreviatura'] for r in legacy.values()}
    for tid, name in teams.items():
        if tid in mapped:
            t = legacy.get(mapped[tid])
            exigir(t and t['nombre'] == name and t['competicion_principal_id'] == cid, 'Catálogos de equipo discordantes')
            continue
        team_uid = uid('equipo', tid)
        exigir(team_uid not in legacy and not any(t['nombre'] == name for t in legacy.values()), 'Equipo sin vínculo explícito ya existente')
        # Alias técnico único, NO abreviatura oficial ni afiliación NBA inferida.
        alias = alias_tecnico(tid, usados)
        usados.add(alias)
        conn.execute("""INSERT INTO public.equipos(id,nombre,nombre_corto,abreviatura,competicion_principal_id)
                        VALUES (%s,%s,%s,%s,%s)""", (team_uid,name,name,alias,cid))
        conn.execute("""INSERT INTO public.equipos_baloncesto(id,nombre,nombre_corto,abreviatura,espn_team_id,competicion_principal_id)
                        VALUES (%s,%s,%s,%s,%s,%s)""", (team_uid,name,name,alias,tid,cid))
        mapped[tid] = team_uid
        result['equipos_creados'] += 1
    seasons = {}
    for t in _filas(conn, 'SELECT id::text,nombre,anio_inicio,anio_fin,es_anual FROM public.temporadas_baloncesto WHERE competicion_id=%s', (cid,)):
        exigir(t['es_anual'] and t['anio_inicio'] == t['anio_fin'] and t['nombre'] == str(t['anio_inicio']), 'Temporada WNBA no anual')
        seasons[t['anio_inicio']] = t['id']
    for year in sorted({r['temporada'] for r in rs}):
        if year not in seasons:
            seasons[year] = uid('temporada', str(year))
            conn.execute("""INSERT INTO public.temporadas_baloncesto(id,competicion_id,nombre,anio_inicio,anio_fin,es_anual)
                            VALUES (%s,%s,%s,%s,%s,true)""", (seasons[year],cid,str(year),year,year))
            result['temporadas_creadas'] += 1
    old_batches = _filas(conn, 'SELECT archivos FROM public.lotes_ingesta_wnba WHERE sha256=%s', (lote['sha256'],))
    if old_batches:
        exigir(old_batches[0]['archivos'] == lote['archivos'], 'Mismo JSONL con artefactos de lote diferentes')
    else:
        conn.execute('''INSERT INTO public.lotes_ingesta_wnba(sha256,archivos,reporte_fuente,cuarentena,pendientes_fuente,advertencias_estadisticas)
                        VALUES(%s,%s,%s,%s,%s,%s)''', (lote['sha256'], Jsonb(lote['archivos']),Jsonb(lote['reporte']),
                        Jsonb(lote['cuarentena']),Jsonb(lote['pendientes_fuente']),Jsonb(lote['advertencias_estadisticas'])))
    old_source = {r['source_game_id']:r for r in _filas(conn, 'SELECT * FROM public.partidos_fuente_wnba WHERE competicion_id=%s', (cid,))}
    canonical = {r['source_game_id']:r for r in _filas(conn, "SELECT * FROM public.partidos_baloncesto WHERE source='ESPN' AND source_game_id=ANY(%s)", ([r['source_game_id'] for r in rs],))}
    new_finals, new_source = [], []
    for r in rs:
        eid = r['source_game_id']
        pid = uid('partido', eid) if r['final_completo'] else None
        core = {'id':pid, 'competicion_id':cid, 'temporada_id':seasons[r['temporada']],
                'fecha_partido':instante(r['inicio_utc']).astimezone(BOGOTA).date(), 'tipo_partido':r['fase'],
                'equipo_local_id':mapped[r['local_id_fuente']], 'equipo_visitante_id':mapped[r['visitante_id_fuente']],
                'source':'ESPN','source_game_id':eid,'espn_game_id':eid,
                'ganador_id':mapped.get(r['ganador_id_fuente']), 'diferencia_puntos':None,
                'hubo_overtime': None, 'fuente_datos':'ESPN','url_referencia':r['url_fuente'], 'valido':True}
        if r['final_completo']:
            core.update({k:r[k] for k in PUNTOS if not k.endswith(('_regulacion', '_prorrogas'))})
            core.update(diferencia_puntos=abs(r['local_total']-r['visitante_total']), hubo_overtime=r['numero_prorrogas'] > 0)
        if eid in old_source:
            o = old_source[eid]
            exigir(o['source'] == 'ESPN' and o['registro'] == r and o['registro_sha256'] == huella(r)
                   and str(o['temporada_id']) == core['temporada_id']
                   and str(o['equipo_local_id']) == core['equipo_local_id']
                   and str(o['equipo_visitante_id']) == core['equipo_visitante_id']
                   and o['inicio_utc'] == instante(r['inicio_utc']) and o['estado'] == r['estado']
                   and o['fase'] == r['fase'], f'Versión o identidad fuente conflictiva: {eid}')
            pid = str(o['partido_id']) if o['partido_id'] else None
            core['id'] = pid
            result['ya_existentes'] += 1
        else:
            result['insertados'] += 1
        if eid in canonical:
            old = canonical[eid]
            # Admitir ID canónico previo solo si hay vínculo fuente validado.
            exigir(eid in old_source and r['final_completo']
                   and all((str(old[k]) if k.endswith('_id') or k == 'id' else old[k]) == v for k,v in core.items()),
                   f'Colisión canónica (no sobrescribir): {eid}')
            result['resultados_existentes'] += 1
        elif r['final_completo']:
            exigir(eid not in old_source, f'Vínculo a resultado ausente: {eid}')
            new_finals.append(core)
            result['resultados_insertados'] += 1
        if eid not in old_source:
            new_source.append((cid,'ESPN',eid,seasons[r['temporada']],core['equipo_local_id'],core['equipo_visitante_id'],
                               pid,instante(r['inicio_utc']),r['estado'],r['fase'],Jsonb(r),huella(r),lote['sha256']))
        else:
            exigir((pid is not None) == r['final_completo'], 'Vínculo final discordante')
    with conn.cursor() as cur:
        if new_finals:
            keys = list(new_finals[0])
            cur.executemany('INSERT INTO public.partidos_baloncesto('+','.join(keys)+') VALUES ('+
                            ','.join('%('+k+')s' for k in keys)+')', new_finals)
        cur.executemany('''INSERT INTO public.partidos_fuente_wnba(competicion_id,source,source_game_id,temporada_id,
             equipo_local_id,equipo_visitante_id,partido_id,inicio_utc,estado,fase,registro,registro_sha256,lote_sha256)
             VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', new_source)
    # Una segunda llamada en la misma transacción también debe ser NO-OP.
    result['competicion_id'] = cid
    return result
