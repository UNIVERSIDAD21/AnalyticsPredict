"""Actualizador manual: planes y estadísticas con identidad estricta, sin modelos."""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from psycopg.rows import dict_row
from servicios.fuentes_agenda import FUTBOL
from servicios.resolucion_multifuente_futbol import (
    extraer_evidencia_espn, construir_plan_resolucion, aplicar_plan_resolucion,
    validar_vinculo_partido, PartidoCanonico, PartidoProveedor, METODO_IDENTIDAD_ESTRICTA,
)

OBJETIVOS = tuple(f'{lado}_{campo}' for lado in ('local', 'visitante')
                  for campo in ('corners_total', 'disparos_total', 'disparos_arco'))


def catalogo(conn):
    with conn.cursor(row_factory=dict_row) as cursor:
        return cursor.execute("""SELECT codigo,nombre,'futbol' deporte FROM competiciones_futbol
            UNION ALL SELECT codigo,nombre,'baloncesto' FROM competiciones_baloncesto
            ORDER BY deporte,codigo""").fetchall()


def ventana(hoy, ultimo=None):
    """Repasa siete días; una pausa larga se recupera en lotes de 31 días."""
    start = date.fromisoformat(ultimo[:10]) - timedelta(days=7) if ultimo else hoy - timedelta(days=14)
    start = min(start, hoy - timedelta(days=7))
    return start, min(hoy, start + timedelta(days=30))


def material_estadisticas(row, payload, meta, mapas, rechazos_calidad=None):
    """Mismo resolver de NULL y vínculos acreditados utilizado por la ingesta anterior."""
    feed, event = row['liga'], str(row['id_fuente'])
    if payload.get('header', {}).get('league', {}).get('slug') != feed:
        raise ValueError('El resumen corresponde a otra liga')
    comp = payload['header']['competitions'][0]
    sides = {x['homeAway']: x for x in comp['competitors']}
    home, away = str(sides['home']['team']['id']), str(sides['away']['team']['id'])
    if str(row['temporada_id']) != mapas['temporadas'].get((feed, payload['header']['season']['year'])):
        raise ValueError('Temporada fuente/canónica distinta')
    canon = PartidoCanonico(str(row['id']), str(row['competicion_id']), str(row['equipo_local_id']),
        str(row['equipo_visitante_id']), row['fecha_partido'], str(row['estado']),
        row['local_goles_total'], row['visitante_goles_total'])
    provider = PartidoProveedor('ESPN_SOCCER', event, feed, home, away,
        datetime.fromisoformat(comp['date'].replace('Z', '+00:00')), 'finished',
        int(sides['home']['score']), int(sides['away']['score']))
    validar_vinculo_partido(canon, provider,
        mapeo_competiciones={('ESPN_SOCCER', feed): mapas['competiciones'].get(FUTBOL[feed])},
        mapeo_equipos={('ESPN_SOCCER', home): mapas['equipos'].get(home),
                      ('ESPN_SOCCER', away): mapas['equipos'].get(away)})
    expected = dict(id_fuente=event, liga=feed, inicio_utc=row['fecha_partido'],
        local_id_fuente=home, visitante_id_fuente=away,
        local_goles=row['local_goles_total'], visitante_goles=row['visitante_goles_total'])
    evidence = extraer_evidencia_espn(payload, expected,
        observado_en=datetime.fromisoformat(meta['observado_en']), rechazos_calidad=rechazos_calidad)
    identities = {('ESPN_SOCCER', event): dict(metodo=METODO_IDENTIDAD_ESTRICTA,
        canonical_competition_id=str(row['competicion_id']), provider_competition_id=feed,
        canonical_home_team_id=str(row['equipo_local_id']), provider_home_team_id=home,
        canonical_away_team_id=str(row['equipo_visitante_id']), provider_away_team_id=away,
        canonical_start_utc=row['fecha_partido'], provider_start_utc=provider.inicio_utc,
        canonical_ft=[row['local_goles_total'], row['visitante_goles_total']],
        provider_ft=[provider.goles_local, provider.goles_visitante])}
    return construir_plan_resolucion(row, evidence), identities


def pendientes(conn, desde, hasta, anteriores=()):
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute("""SELECT p.*,e.liga,e.id_fuente FROM partidos_futbol p
            JOIN partidos_fuente_espn_futbol e ON e.partido_id=p.id
            WHERE p.valido AND p.estado='FINALIZADO' AND p.local_goles_total IS NOT NULL
            AND p.visitante_goles_total IS NOT NULL
            AND ((p.fecha_partido AT TIME ZONE 'America/Bogota')::date BETWEEN %s AND %s
                 OR p.id=ANY(%s::uuid[])) AND p.fecha_partido<=now()
            AND (p.local_corners_total IS NULL OR p.visitante_corners_total IS NULL
             OR p.local_disparos_total IS NULL OR p.visitante_disparos_total IS NULL
             OR p.local_disparos_arco IS NULL OR p.visitante_disparos_arco IS NULL)
            ORDER BY p.fecha_partido,e.liga,e.id_fuente""", (desde, hasta, list(anteriores))).fetchall()
        maps = {
            'equipos': {r['id_fuente']: str(r['equipo_id']) for r in cur.execute('SELECT id_fuente,equipo_id FROM equipos_fuente_espn_futbol')},
            'competiciones': {r['codigo']: str(r['id']) for r in cur.execute('SELECT codigo,id FROM competiciones_futbol')},
            'temporadas': {(r['liga'], r['anio']): str(r['temporada_id']) for r in cur.execute('SELECT liga,anio,temporada_id FROM temporadas_fuente_espn_futbol')},
        }
    return rows, maps


def contraste_local(conn, ligas, ventanas, aceptados):
    """Un feed vacío no tapa finales locales sin vínculo, cuartos o estadísticas."""
    result = []
    accepted = {x['partido_id'] for x in aceptados}
    with conn.cursor(row_factory=dict_row) as cur:
        for liga in ligas:
            code = liga['codigo']
            if liga['deporte'] == 'futbol':
                rows = cur.execute("""SELECT p.id,
                    (local_corners_total IS NULL OR visitante_corners_total IS NULL
                     OR local_disparos_total IS NULL OR visitante_disparos_total IS NULL
                     OR local_disparos_arco IS NULL OR visitante_disparos_arco IS NULL) incompleto
                    FROM partidos_futbol p JOIN competiciones_futbol c ON c.id=p.competicion_id
                    WHERE c.codigo=%s AND p.valido AND p.estado='FINALIZADO'
                    AND (p.fecha_partido AT TIME ZONE 'America/Bogota')::date BETWEEN %s AND %s""",
                    (code, *ventanas[code])).fetchall()
            else:
                rows = cur.execute("""SELECT p.id,NOT COALESCE(
                    local_q1+local_q2+local_q3+local_q4+local_ot=local_total AND
                    visitante_q1+visitante_q2+visitante_q3+visitante_q4+visitante_ot=visitante_total
                    AND LEAST(local_q1,local_q2,local_q3,local_q4,visitante_q1,visitante_q2,visitante_q3,visitante_q4)>=0,false) incompleto
                    FROM partidos_baloncesto p JOIN competiciones_baloncesto c ON c.id=p.competicion_id
                    WHERE c.codigo=%s AND p.valido AND p.local_total>0 AND p.visitante_total>0
                    AND p.fecha_partido BETWEEN %s AND %s""", (code, *ventanas[code])).fetchall()
            for row in rows:
                if str(row['id']) not in accepted:
                    result.append({'grupo': code, 'partido_id': str(row['id']), 'motivo': 'FINAL_LOCAL_NO_CONTRASTADO_CON_FUENTE'})
                if row['incompleto']:
                    result.append({'grupo': code, 'partido_id': str(row['id']), 'motivo': 'ESTADISTICAS_LOCALES_PENDIENTES'})
    return result


def fila_actual(conn, ident):
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute('SELECT * FROM partidos_futbol WHERE id=%s', (ident,)).fetchone()


def revisar_estadisticas(conn, rows, mapas, client, *, aplicar=False,
                         observar=lambda _: None, registrar=lambda _: None, confirmar=None, anotar_error=None):
    result = {'actualizados': Counter(), 'campos': Counter(), 'campos_acreditados': Counter(),
              'campos_no_acreditados': Counter(), 'incidencias': [], 'fuentes': []}
    # Un límite explícito deja el resto pendiente; no lo declara procesado.
    for old in rows[:400]:
        feed, event = old['liga'], str(old['id_fuente'])
        if feed not in FUTBOL:
            result['incidencias'].append({'grupo': 'SIN_ADAPTADOR', 'id': event, 'motivo': 'Fuente no configurada'})
            continue
        code = FUTBOL[feed]
        observar(f'{code}: completando córners y tiros del partido {event}')
        try:
            payload, meta = client.json(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{feed}/summary', {'event': event}, ttl=300)
            result['fuentes'].append(meta)
            raw = Path(meta['archivo']).read_bytes()
            if sha256(raw).hexdigest() != meta['sha256']:
                raise ValueError('Fuente alterada')
            # Identidad y before-image se vuelven a comprobar tras el HTTP.
            with conn.transaction():
                conn.execute('SET TRANSACTION READ ONLY')
                row = fila_actual(conn, old['id'])
            rechazados = []
            plan, identities = material_estadisticas({**row, 'liga': feed, 'id_fuente': event}, payload, meta, mapas,
                                                   rechazos_calidad=rechazados)
            if rechazados:
                result['incidencias'].append({
                    'grupo': code, 'id': event, 'partido_id': str(old['id']),
                    'motivo': f'Estadísticas pendientes de acreditar en el partido ESPN {event}.',
                    'campos': [rechazo['campo'] for rechazo in rechazados],
                })
            for rejection in rechazados:
                registrar({'tipo': 'CUARENTENA_FUENTE', 'partido': str(old['id']), 'fuente': meta, **rejection})
            result['campos_no_acreditados'][code] += len(rechazados)
            if plan.conflictos:
                raise ValueError('Estadísticas en conflicto con el canon; no se sobrescriben')
            registrar({'tipo': 'PLAN_ESTADISTICAS', 'partido': str(old['id']), 'fuente': meta,
                       'antes': {k: row[k] for k in OBJETIVOS}, 'actualizaciones': dict(plan.actualizaciones)})
            receipt = None
            if confirmar is not None and aplicar:
                receipt = confirmar({**row, 'liga': feed, 'id_fuente': event}, payload, meta, plan, identities, rechazados)
            elif plan.actualizaciones and aplicar:
                with conn.transaction():
                    conn.execute("SET LOCAL lock_timeout='5s'; SET LOCAL statement_timeout='30s'")
                    receipt = aplicar_plan_resolucion(conn, partido_id=str(row['id']),
                        goles_local_ft=row['local_goles_total'], goles_visitante_ft=row['visitante_goles_total'],
                        plan=plan, identidades=identities, dry_run=False)
            if plan.actualizaciones and receipt is not None:
                registrar({'tipo': 'COMMIT_ESTADISTICAS', 'recibo': receipt})
                result['actualizados'][code] += 1
                result['campos'][code] += len(plan.actualizaciones)
                result['campos_acreditados'][code] += len(plan.actualizaciones)
            descartados = {r['campo'] for r in rechazados}
            missing = [k for k in OBJETIVOS if row[k] is None and k not in plan.actualizaciones and k not in descartados]
            if missing:
                result['incidencias'].append({'grupo': code, 'id': event, 'motivo': 'ESTADISTICAS_AUSENTES', 'campos': missing})
        except (ValueError, KeyError, TypeError, IndexError, RuntimeError) as exc:
            # No se incluyen errores SQL/conexiones; éstos abortan con causa saneada en CLI.
            result['incidencias'].append({'grupo': code, 'id': event, 'motivo': str(exc)})
            if anotar_error is not None and aplicar:
                anotar_error(old, str(exc))
    for old in rows[400:]:
        result['incidencias'].append({'grupo': FUTBOL.get(old['liga'], old['liga']),
            'id': str(old['id_fuente']), 'motivo': 'PRESUPUESTO_ESTADISTICAS: pendiente del siguiente ciclo'})
    return result


def resumen_ligas(ligas, ventanas, coverage, plan, stats, ahora):
    summary = []
    issues = plan['incidencias'] + stats['incidencias']
    for liga in ligas:
        code = liga['codigo']
        problems = [x for x in issues if x.get('grupo') == code]
        source = coverage[code]
        operations = [x for x in plan['operaciones'] if x['codigo'] == code and x['tabla'] in ('partidos_futbol', 'partidos_baloncesto')]
        state = 'PARCIAL' if problems else 'COMPLETA_EN_VENTANA' if source['finales'] else 'SIN_FINALES_EN_VENTANA'
        if any('SIN_ADAPTADOR' in x.get('motivo', '') for x in problems):
            state = 'SIN_ADAPTADOR'
        summary.append({**liga, 'estado': state, 'desde': str(ventanas[code][0]),
            'hasta': str(ventanas[code][1]), 'finales_fuente': source['finales'],
            'no_finales_excluidos': source['no_finales'], 'insertados': sum(x['antes'] is None for x in operations),
            'resultados_actualizados': sum(x['antes'] is not None for x in operations),
            'estadisticas_actualizadas': stats['actualizados'].get(code, 0),
            'campos_completados': stats['campos'].get(code, 0), 'incidencias': problems,
            'campos_escritos': stats['campos'].get(code, 0),
            'campos_acreditados': stats.get('campos_acreditados', {}).get(code, 0),
            'campos_no_acreditados': stats.get('campos_no_acreditados', {}).get(code, 0),
            'verificado_en': ahora, 'limite': 'Sólo finales y campos objetivo en la ventana; no acredita histórico íntegro.'})
    return summary
