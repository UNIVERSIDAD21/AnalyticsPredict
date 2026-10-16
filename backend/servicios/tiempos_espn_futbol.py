"""Goles por mitades explícitos de ESPN: identidad exacta y ausencia sin imputar."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from scripts.auditar_fuente_espn_soccer import (
    FuenteNoDisponible, _entero_no_negativo, _instante_utc, interpretar_estadisticas,
)

CONTRATO_GOLES = 'ESPN_REGULATION_TWO_HALVES_EXPLICIT_LINESCORES_V1'
CONTRATO_COMPLETO = 'ESPN_HALVES_LINESCORES_AND_RECONCILED_CORNERS_V2'


def interpretar_tiempos(payload: dict, esperado: dict) -> dict:
    """Solo dos líneas de dos mitades declaradas; nunca deduce HT de un FT.

    ESPN puede omitir period.number en linescores. En ese contrato el orden solo
    se admite si regulation declara exactamente dos halves y ambos equipos
    entregan exactamente dos valores cuya suma coincide con su FT acreditado.
    """
    formato = (payload.get('format') or {}).get('regulation') or {}
    if formato.get('periods') != 2 or formato.get('slug') != 'half':
        raise FuenteNoDisponible('Formato distinto de dos mitades')
    header = payload.get('header') or {}
    competiciones = header.get('competitions') or []
    if str(header.get('id')) != esperado['id_fuente'] or len(competiciones) != 1:
        raise FuenteNoDisponible('Evento ausente o ambiguo')
    partido = competiciones[0]
    if str(partido.get('id')) != esperado['id_fuente']:
        raise FuenteNoDisponible('Competición de otro evento')
    if _instante_utc(partido.get('date')) != _instante_utc(esperado['inicio_utc']):
        raise FuenteNoDisponible('Cambio de inicio: requiere reconciliación')
    estado = (partido.get('status') or {}).get('type') or {}
    if estado.get('completed') is not True or estado.get('name') != 'STATUS_FULL_TIME':
        raise FuenteNoDisponible('No es final reglamentario acreditado')
    participantes = partido.get('competitors') or []
    por_lado = {x.get('homeAway'): x for x in participantes}
    if len(participantes) != 2 or set(por_lado) != {'home', 'away'}:
        raise FuenteNoDisponible('Local/visitante ambiguos')
    salida = {'liga': esperado['liga'], 'id_fuente': esperado['id_fuente'],
              'inicio_utc': _instante_utc(esperado['inicio_utc']),
              'contrato': CONTRATO_GOLES}
    for lado, etiqueta in (('home', 'local'), ('away', 'visitante')):
        item = por_lado[lado]
        equipo_id = str((item.get('team') or {}).get('id'))
        if equipo_id != esperado[f'{etiqueta}_id_fuente']:
            raise FuenteNoDisponible('Identidad de equipo distinta')
        ft = _entero_no_negativo(item.get('score'))
        if ft is None or ft != esperado[f'{etiqueta}_goles']:
            raise FuenteNoDisponible('Cambio de marcador FT')
        lineas = item.get('linescores') or []
        if len(lineas) != 2:
            raise FuenteNoDisponible('Mitades ausentes o periodo adicional')
        valores = []
        for numero, linea in enumerate(lineas, 1):
            periodo = linea.get('period', numero)
            if isinstance(periodo, dict):
                periodo = periodo.get('number')
            if periodo != numero:
                raise FuenteNoDisponible('Orden de periodos incompatible')
            valor = _entero_no_negativo(linea.get('displayValue'))
            if valor is None:
                raise FuenteNoDisponible('Marcador por mitad no numérico')
            valores.append(valor)
        if sum(valores) != ft:
            raise FuenteNoDisponible('Mitades no concilian con FT')
        salida[f'{etiqueta}_id_fuente'] = equipo_id
        salida[f'{etiqueta}_goles_total'] = ft
        salida[f'{etiqueta}_goles_1t'], salida[f'{etiqueta}_goles_2t'] = valores
    salida['sha256_payload'] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return salida


def interpretar_tiempos_completos(payload: dict, esperado: dict) -> dict:
    """Corners contados desde jugadas tipadas, nunca repartidos desde su FT.

    Exige cronología completa, secuencia continua, límites explícitos, eventos
    únicos, equipo exacto y periodo explícito. El total de ambos equipos debe
    conciliar tanto con boxscore como con el FT ya capturado y acreditado.
    """
    salida = interpretar_tiempos(payload, esperado)
    partido = payload['header']['competitions'][0]
    if partido.get('playByPlaySource') != 'full' or partido.get('commentaryAvailable') is not True:
        raise FuenteNoDisponible('Cronología no declarada completa')
    comentarios = payload.get('commentary') or []
    if not comentarios or [x.get('sequence') for x in comentarios] != list(range(len(comentarios))):
        raise FuenteNoDisponible('Cronología truncada o secuencia discontinua')
    limites = {}
    # Los límites tipados están completos en keyEvents aunque la entrada de
    # comentario correspondiente no lleve play. No inferir el periodo del texto.
    for play in payload.get('keyEvents') or []:
        tipo = (play.get('type') or {}).get('type')
        if tipo in {'kickoff', 'halftime', 'end-regular-time'}:
            if tipo in limites:
                raise FuenteNoDisponible('Límites de periodo ambiguos')
            limites[tipo] = (datetime.fromisoformat(_instante_utc(play.get('wallclock'))),
                            (play.get('period') or {}).get('number'))
    if (set(limites) != {'kickoff', 'halftime', 'end-regular-time'}
            or [limites[x][1] for x in ('kickoff','halftime','end-regular-time')] != [1,1,2]):
        raise FuenteNoDisponible('No están acreditados los límites de ambas mitades')
    inicio, mitad, fin = [limites[x][0] for x in ('kickoff','halftime','end-regular-time')]
    if not inicio < mitad < fin:
        raise FuenteNoDisponible('Orden de límites incompatible')
    nombres = {esperado[f'{lado}_nombre']: lado for lado in ('local','visitante')}
    if len(nombres) != 2:
        raise FuenteNoDisponible('Nombres de equipos ambiguos')
    contadores = {(lado, numero): 0 for lado in ('local','visitante') for numero in (1,2)}
    ids = set()
    for comentario in comentarios:
        play = comentario.get('play') or {}
        if (play.get('type') or {}).get('type') != 'corner-awarded':
            continue
        ident = play.get('id')
        periodo = (play.get('period') or {}).get('number')
        equipo = play.get('team') or {}
        lado = nombres.get(equipo.get('displayName'))
        instante = datetime.fromisoformat(_instante_utc(play.get('wallclock')))
        if (not ident or ident in ids or lado is None or isinstance(periodo, bool) or periodo not in (1,2)
                or (periodo == 1 and not inicio <= instante <= mitad)
                or (periodo == 2 and not mitad <= instante <= fin)):
            raise FuenteNoDisponible('Corner sin identidad/periodo único acreditado')
        if equipo.get('id') is not None and str(equipo['id']) != esperado[f'{lado}_id_fuente']:
            raise FuenteNoDisponible('ID de equipo de corner contradictorio')
        ids.add(ident)
        contadores[lado, periodo] += 1
    estadisticas = interpretar_estadisticas(payload, esperado)
    for lado in ('local','visitante'):
        ft = estadisticas.get(f'{lado}_corners')
        if ft is None or ft != esperado.get(f'{lado}_corners') or sum(contadores[lado,p] for p in (1,2)) != ft:
            raise FuenteNoDisponible('Corners por periodo no concilian con FT')
        salida[f'{lado}_corners_total'] = ft
        for periodo in (1,2):
            salida[f'{lado}_corners_{periodo}t'] = contadores[lado, periodo]
    salida['contrato'] = CONTRATO_COMPLETO
    return salida


def validar_observacion(fila: dict) -> None:
    """Valida antes de planificar DML; una observación no puede ser prepartido."""
    instante = datetime.fromisoformat(_instante_utc(fila['observado_en']))
    inicio = datetime.fromisoformat(_instante_utc(fila['inicio_utc']))
    if instante <= inicio or instante > datetime.now(timezone.utc):
        raise ValueError('Instante de observación incompatible')
    if len(fila.get('sha256_payload', '')) != 64:
        raise ValueError('Hash de evidencia ausente')
    if fila.get('contrato') not in {CONTRATO_GOLES, CONTRATO_COMPLETO}:
        raise ValueError('Contrato no admitido')
    for lado in ('local', 'visitante'):
        valores = [fila.get(f'{lado}_goles_{p}') for p in ('1t', '2t', 'total')]
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in valores):
            raise ValueError('Marcadores inválidos')
        if valores[0] + valores[1] != valores[2]:
            raise ValueError('Mitades incompatibles')
        if fila['contrato'] == CONTRATO_COMPLETO:
            corners = [fila.get(f'{lado}_corners_{p}') for p in ('1t','2t','total')]
            if (any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in corners)
                    or corners[0] + corners[1] != corners[2]):
                raise ValueError('Corners por mitades incompatibles')


CAMPOS = ('local_goles_1t', 'local_goles_2t', 'visitante_goles_1t', 'visitante_goles_2t')
CAMPOS_CORNERS = ('local_corners_1t', 'local_corners_2t', 'visitante_corners_1t', 'visitante_corners_2t')


def campos_observacion(obs):
    return CAMPOS + CAMPOS_CORNERS if obs['contrato'] == CONTRATO_COMPLETO else CAMPOS


def construir_plan(conn, observaciones: list[dict], *, bloquear=False) -> list[dict]:
    """No busca por nombres: usa exclusivamente vínculos ESPN ya acreditados."""
    vistos = set()
    plan = []
    with conn.cursor(row_factory=dict_row) as cur:
        for obs in observaciones:
            validar_observacion(obs)
            clave = (obs['liga'], obs['id_fuente'])
            if clave in vistos:
                raise ValueError('Evento repetido en el lote')
            vistos.add(clave)
            cur.execute('''SELECT p.*, v.evidencia AS evidencia_vinculo,
                v.partido_id AS partido_id_vinculo
                FROM partidos_fuente_espn_futbol v JOIN partidos_futbol p ON p.id=v.partido_id
                WHERE v.liga=%s AND v.id_fuente=%s''' + (' FOR UPDATE OF p' if bloquear else ''), clave)
            filas = cur.fetchall()
            if len(filas) != 1:
                raise ValueError('Vínculo ausente o ambiguo')
            fila = filas[0]
            ev = fila['evidencia_vinculo']
            if (str(fila['id']) != str(obs['partido_id'])
                    or fila['fuente_datos'] != 'ESPN_SOCCER' or fila['estado'] != 'FINALIZADO'
                    or fila['valido'] is not True
                    or _instante_utc(fila['fecha_partido'].isoformat()) != obs['inicio_utc']):
                raise ValueError('Cambio de identidad, fuente o estado canónico')
            for lado in ('local', 'visitante'):
                if fila.get(f'{lado}_goles_et') not in (None, 0):
                    raise ValueError('Prórroga canónica incompatible con final reglamentario')
                if (ev[f'{lado}_id_fuente'] != obs[f'{lado}_id_fuente']
                        or fila[f'{lado}_goles_total'] != obs[f'{lado}_goles_total']):
                    raise ValueError('Cambio de equipos o marcador canónico')
                if obs['contrato'] == CONTRATO_COMPLETO and fila[f'{lado}_corners_total'] != obs[f'{lado}_corners_total']:
                    raise ValueError('Cambio de corners FT canónicos')
            campos = campos_observacion(obs)
            if any(fila[c] is not None and fila[c] != obs[c] for c in campos):
                raise ValueError('No sobrescribir una mitad contradictoria')
            plan.append({'observacion': obs, 'cambia': any(fila[c] is None for c in campos)})
    return plan


def aplicar_observaciones(conn, observaciones: list[dict]) -> dict:
    """Transacción atómica/idempotente. La tabla de evidencia debe estar instalada.

    No escribe FT, tiros, equipos, flags ni las capturas previas directamente.
    El trigger canónico deriva datos_completos de golesFT y la completitud de
    córners de sus cuatro mitades; el flag genérico no acredita todos los targets.
    La evidencia original del vínculo y su hash permanecen íntegros.
    """
    cambios = evidencias = 0
    with conn.transaction():
        plan = construir_plan(conn, observaciones, bloquear=True)
        for item in plan:
            obs = item['observacion']
            cursor = conn.execute('''INSERT INTO observaciones_tiempos_espn_futbol
                (liga,id_fuente,partido_id,observado_en,sha256_payload,contrato,evidencia)
                VALUES(%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(liga,id_fuente,sha256_payload,contrato) DO NOTHING RETURNING liga''',
                (obs['liga'], obs['id_fuente'], obs['partido_id'], obs['observado_en'],
                 obs['sha256_payload'], obs['contrato'], Jsonb(obs)))
            # fetchone sincroniza también en psycopg pipeline; rowcount puede
            # seguir en -1 mientras el INSERT está pendiente de respuesta.
            evidencias += int(cursor.fetchone() is not None)
            if item['cambia']:
                campos = campos_observacion(obs)
                # Lista fija interna de columnas, jamás interpolada desde el usuario.
                conn.execute('UPDATE partidos_futbol SET '+','.join(c+'=%s' for c in campos)
                             + ',actualizado_en=now() WHERE id=%s',
                             [*(obs[c] for c in campos), obs['partido_id']])
                cambios += 1
    return {'partidos_completados': cambios, 'evidencias_insertadas': evidencias,
            'eventos_verificados': len(plan)}
