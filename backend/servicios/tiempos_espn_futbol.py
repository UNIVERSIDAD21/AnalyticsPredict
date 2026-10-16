"""Goles por mitades explícitos de ESPN: identidad exacta y ausencia sin imputar."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from scripts.auditar_fuente_espn_soccer import (
    FuenteNoDisponible, _entero_no_negativo, _instante_utc,
)


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
              'contrato': 'ESPN_REGULATION_TWO_HALVES_EXPLICIT_LINESCORES_V1'}
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


def validar_observacion(fila: dict) -> None:
    """Valida antes de planificar DML; una observación no puede ser prepartido."""
    instante = datetime.fromisoformat(_instante_utc(fila['observado_en']))
    inicio = datetime.fromisoformat(_instante_utc(fila['inicio_utc']))
    if instante <= inicio or instante > datetime.now(timezone.utc):
        raise ValueError('Instante de observación incompatible')
    if len(fila.get('sha256_payload', '')) != 64:
        raise ValueError('Hash de evidencia ausente')
    for lado in ('local', 'visitante'):
        valores = [fila.get(f'{lado}_goles_{p}') for p in ('1t', '2t', 'total')]
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in valores):
            raise ValueError('Marcadores inválidos')
        if valores[0] + valores[1] != valores[2]:
            raise ValueError('Mitades incompatibles')


CAMPOS = ('local_goles_1t', 'local_goles_2t', 'visitante_goles_1t', 'visitante_goles_2t')


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
                if (ev[f'{lado}_id_fuente'] != obs[f'{lado}_id_fuente']
                        or fila[f'{lado}_goles_total'] != obs[f'{lado}_goles_total']):
                    raise ValueError('Cambio de equipos o marcador canónico')
            if any(fila[c] is not None and fila[c] != obs[c] for c in CAMPOS):
                raise ValueError('No sobrescribir una mitad contradictoria')
            plan.append({'observacion': obs, 'cambia': any(fila[c] is None for c in CAMPOS)})
    return plan


def aplicar_observaciones(conn, observaciones: list[dict]) -> dict:
    """Transacción atómica/idempotente. La tabla de evidencia debe estar instalada.

    No cambia FT, corners, tiros, equipos, datos_completos ni las capturas previas.
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
                ON CONFLICT(liga,id_fuente,sha256_payload) DO NOTHING''',
                (obs['liga'], obs['id_fuente'], obs['partido_id'], obs['observado_en'],
                 obs['sha256_payload'], obs['contrato'], Jsonb(obs)))
            evidencias += cursor.rowcount
            if item['cambia']:
                conn.execute('''UPDATE partidos_futbol SET
                    local_goles_1t=%s,local_goles_2t=%s,
                    visitante_goles_1t=%s,visitante_goles_2t=%s,actualizado_en=now()
                    WHERE id=%s''', [*(obs[c] for c in CAMPOS), obs['partido_id']])
                cambios += 1
    return {'partidos_completados': cambios, 'evidencias_insertadas': evidencias,
            'eventos_verificados': len(plan)}
