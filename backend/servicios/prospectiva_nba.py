"""Seguimiento Q1 NBA Ridge raw. Sin selección de lado, cuotas, stake ni picks.

La captura es prospectiva por reloj de BD; no certifica disponibilidad temporal
del histórico de entrenamiento ni independencia de ESPN. No usa calibrador.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from math import erf, isfinite, sqrt
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from motor.nba_predictor_cuartos import construir_matriz_diseno
from motor.utilidades import resolver_nombre_en_modelo
from motor_autoentrenamiento.artefacto_nba import cargar_artefacto


def digest(datos):
    return sha256(json.dumps(datos, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def utc(valor):
    instante = datetime.fromisoformat(str(valor).replace('Z', '+00:00'))
    if instante.tzinfo is None:
        raise ValueError('Se requiere hora con zona explícita')
    return instante.astimezone(timezone.utc)


def identidad_evento(evento):
    if not str(evento.get('id', '')).isdigit():
        raise ValueError('Evento ESPN sin identidad')
    competiciones = evento.get('competitions', [])
    if len(competiciones) != 1:
        raise ValueError('Competición ambigua')
    competencia = competiciones[0]
    lados = {x['homeAway']: x for x in competencia['competitors']}
    if set(lados) != {'home', 'away'} or len(competencia['competitors']) != 2:
        raise ValueError('Local/visitante ambiguos')
    inicio = utc(evento['date'])
    if utc(competencia['date']) != inicio:
        raise ValueError('Inicio de evento y competición incompatibles')
    ids = [str(lados[l]['team']['id']) for l in ('home', 'away')]
    if ids[0] == ids[1] or not all(x.isdigit() for x in ids):
        raise ValueError('Identidad de equipos inválida')
    return inicio, lados, ids


def construir_snapshot(evento, ruta: Path, linea: float, ahora: datetime):
    if not isfinite(linea) or linea <= 0 or linea * 2 % 2 != 1:
        raise ValueError('Q1 requiere umbral positivo de medio punto, sin push')
    inicio, lados, ids = identidad_evento(evento)
    estado = evento.get('status', {}).get('type', {})
    if estado.get('state') != 'pre' or estado.get('completed') or not ahora < inicio:
        raise ValueError('Solo eventos futuros sin iniciar')
    hash_antes = sha256(ruta.read_bytes()).hexdigest()
    modelo = cargar_artefacto(ruta)
    if modelo is None:
        raise ValueError('No existe artefacto')
    if sha256(ruta.read_bytes()).hexdigest() != hash_antes:
        raise ValueError('El artefacto cambió durante la captura')
    metricas = modelo['metricas']
    fit = utc(metricas['fit_completed_at'])
    if not fit < ahora < inicio or utc(metricas['training_data_latest_game_date']+'T23:59:59+00:00') >= ahora:
        raise ValueError('Modelo/dataset no anteriores al congelamiento')
    nombres = [resolver_nombre_en_modelo(lados[l]['team']['displayName'], modelo['entidad_a_indice']) for l in ('home', 'away')]
    if not all(nombres):
        raise ValueError('Equipo fuera del dominio del modelo NBA')
    x = construir_matriz_diseno([nombres[0]], [nombres[1]], [1], modelo['entidad_a_indice'])
    media = float((x @ (modelo['pesos_equipo'] + modelo['pesos_rival']))[0, 0])
    sigma = sqrt(float(modelo['desviacion_equipo'][0]**2 + modelo['desviacion_rival'][0]**2))
    if not isfinite(sigma) or sigma <= 0:
        raise ValueError('Desviación Q1 inválida')
    p_raw = (1 - erf((linea - media) / sigma / sqrt(2))) / 2
    return {
        'version': 1, 'deporte': 'nba', 'source': 'ESPN', 'event_id': str(evento['id']),
        'inicio_utc': inicio.isoformat(), 'team_ids': ids, 'equipos_modelo': nombres,
        'mercado': 'Q1_TOTAL', 'linea': linea, 'linea_source_type': 'TECHNICAL_ESTIMATE',
        'linea_nota': 'Umbral analítico predeclarado; no es línea de mercado real.',
        'p_raw': p_raw, 'p_calibrada': None, 'calibrador_id': None,
        'media': media, 'desviacion': sigma, 'features': x[0].tolist(),
        'modelo_version_id': modelo['modelo_version_id'], 'artefacto_sha256': hash_antes,
        'dataset_hash': metricas['hash_datos'], 'fit_completed_at': fit.isoformat(),
        'modelo_metricas': metricas,
        'pesos_q1_local': modelo['pesos_equipo'][:, 0].tolist(),
        'pesos_q1_visitante': modelo['pesos_rival'][:, 0].tolist(),
        'evento_observado_en': ahora.isoformat(), 'evento_sha256': digest(evento), 'evento': evento,
        'certificacion': 'NO_CERTIFICADO', 'independencia_outcome_requerida': True,
        'limitaciones': ['Distribución normal y varianza aditiva sin validación prospectiva.',
                         'Disponibilidad histórica del dataset de entrenamiento no acreditada.'],
        'policy': {'no_picks': True, 'no_stake': True, 'no_betting_recommendations': True},
    }


def congelar(conn, evento, ruta, linea):
    """La clave impide reanalizar el mismo evento/mercado/umbral como muestra nueva."""
    with conn.transaction(), conn.cursor(row_factory=dict_row) as c:
        ahora = c.execute('SELECT clock_timestamp() ahora').fetchone()['ahora']
        snapshot = construir_snapshot(evento, ruta, linea, ahora)
        clave = f"nba:ESPN:{snapshot['event_id']}:Q1_TOTAL:{linea:g}"
        uid = uuid5(NAMESPACE_URL, clave)
        anterior = c.execute('SELECT id,sha256 FROM predicciones_prospectivas WHERE clave=%s', (clave,)).fetchone()
        if anterior:
            return {'id': str(anterior['id']), 'insertada': False}
        # Revalidar el reloj al escribir; una solicitud lenta no puede entrar tarde.
        c.execute('''INSERT INTO predicciones_prospectivas(id,clave,inicio_utc,fit_completed_at,sha256,snapshot)
                     VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(clave) DO NOTHING RETURNING id''',
                  (uid, clave, snapshot['inicio_utc'], snapshot['fit_completed_at'], digest(snapshot), Jsonb(snapshot)))
        return {'id': str(uid), 'insertada': c.fetchone() is not None}


def resolver(conn, prediccion_id, evento):
    with conn.transaction(), conn.cursor(row_factory=dict_row) as c:
        fila = c.execute('SELECT snapshot,congelado_en FROM predicciones_prospectivas WHERE id=%s', (prediccion_id,)).fetchone()
        if not fila:
            raise ValueError('Predicción inexistente')
        s = fila['snapshot']
        inicio, lados, ids = identidad_evento(evento)
        ahora = c.execute('SELECT clock_timestamp() ahora').fetchone()['ahora']
        estado = evento.get('status', {}).get('type', {})
        if (str(evento['id']) != s['event_id'] or ids != s['team_ids'] or inicio != utc(s['inicio_utc'])
                or not estado.get('completed') or estado.get('state') != 'post' or not inicio < ahora):
            raise ValueError('Resultado final/identidad/horario no acreditados; requiere revisión')
        puntos = []
        for l in ('home', 'away'):
            cuartos = lados[l].get('linescores', [])
            if len(cuartos) < 4:
                raise ValueError('Final sin cuatro cuartos')
            valores = [float(q['value']) for q in cuartos]
            total = float(lados[l]['score'])
            if any(not isfinite(v) or v < 0 or not v.is_integer() for v in valores) or sum(valores) != total or total <= 0:
                raise ValueError('Marcador/cuarto inválidos')
            puntos.append(valores[0])
        real = sum(puntos)
        evidencia = {'source': 'ESPN', 'independiente': False, 'evento': evento,
                     'observado_en': ahora.isoformat(), 'valor_real': real,
                     'outcome': real > s['linea'], 'certificacion': 'NO_CERTIFICADO'}
        previo = c.execute('SELECT evidencia FROM outcomes_prospectivos WHERE prediccion_id=%s', (prediccion_id,)).fetchone()
        if previo:
            if digest(previo['evidencia']['evento']) != digest(evento):
                raise ValueError('Resultado revisado: no sobrescribir outcome inmutable')
            return {'insertado': False}
        c.execute('INSERT INTO outcomes_prospectivos(prediccion_id,sha256,evidencia) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING RETURNING prediccion_id',
                  (prediccion_id, digest(evidencia), Jsonb(evidencia)))
        insertado = c.fetchone() is not None
        if not insertado:
            concurrente = c.execute('SELECT evidencia FROM outcomes_prospectivos WHERE prediccion_id=%s', (prediccion_id,)).fetchone()
            if digest(concurrente['evidencia']['evento']) != digest(evento):
                raise ValueError('Outcome concurrente incompatible: requiere revisión')
        return {'insertado': insertado}
