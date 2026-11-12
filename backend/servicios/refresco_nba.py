"""Refresco manual NBA: planes por identidad, sin fit ni efectos en lecturas."""
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from psycopg.rows import dict_row

from scripts.actualizar_partidos_nba import event_to_record, is_completed, load_context


CAMPOS_RESULTADO = tuple(
    f'{lado}_{periodo}' for lado in ('local', 'visitante')
    for periodo in ('q1', 'q2', 'q3', 'q4', 'ot', 'total')
)


def huella(valor):
    return sha256(json.dumps(valor, sort_keys=True, default=str, separators=(',', ':')).encode()).hexdigest()


def guardar_nuevo(path, valor):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as archivo:
        json.dump(valor, archivo, ensure_ascii=False, indent=2, default=str, allow_nan=False)


def validar_final(evento, contexto, anio_fin):
    """ESPN explícito, valores observados enteros; nunca imputa cuartos NULL."""
    if not is_completed(evento) or evento.get('status', {}).get('type', {}).get('state') != 'post':
        raise ValueError('NO_FINAL')
    if evento.get('season', {}).get('year') != anio_fin:
        raise ValueError('TEMPORADA_NO_COINCIDE')
    inicio = datetime.fromisoformat(evento['date'].replace('Z', '+00:00'))
    if inicio.utcoffset() is None or inicio >= datetime.now(timezone.utc):
        raise ValueError('INICIO_NO_ACREDITADO')
    lados = evento['competitions'][0]['competitors']
    if len(lados) != 2:
        raise ValueError('COMPETIDORES_INVALIDOS')
    largos = []
    for lado in lados:
        lineas = lado.get('linescores', [])
        largos.append(len(lineas))
        if len(lineas) < 4:
            raise ValueError('CUARTOS_INCOMPLETOS')
        valores = [x.get('value', x.get('displayValue')) for x in lineas]
        valores.append(lado.get('score'))
        for valor in valores:
            if valor is None or isinstance(valor, bool) or not str(valor).strip():
                raise ValueError('PUNTOS_AUSENTES')
            numero = float(valor)
            if not numero.is_integer() or numero < 0:
                raise ValueError('PUNTOS_INVALIDOS')
    if largos[0] != largos[1]:
        raise ValueError('OT_INCOMPLETO')
    registro = event_to_record(evento, contexto)
    if registro['ganador_id'] is None:
        raise ValueError('FINAL_EMPATE_NO_VALIDO')
    # Una prórroga exige empate al concluir la regulación.
    if largos[0] > 4 and sum(registro[f'local_q{i}'] for i in range(1, 5)) != sum(registro[f'visitante_q{i}'] for i in range(1, 5)):
        raise ValueError('OT_SIN_EMPATE_REGULACION')
    return registro


def planificar(conn, eventos, anio_fin):
    contexto = load_context(conn, anio_fin)
    salida = []
    vistos = set()
    with conn.cursor(row_factory=dict_row) as cursor:
        for evento in eventos:
            ident = str(evento.get('id', ''))
            if not ident or ident in vistos:
                raise ValueError('IDs ESPN ausentes o duplicados')
            vistos.add(ident)
            item = {'evento_id': ident, 'inicio_utc': evento.get('date'), 'fuente_sha256': huella(evento)}
            try:
                registro = validar_final(evento, contexto, anio_fin)
                cursor.execute('''SELECT * FROM partidos_baloncesto WHERE competicion_id=%s
                    AND (source_game_id=%s OR espn_game_id=%s)''', (contexto.competicion_id, ident, ident))
                filas = cursor.fetchall()
                if not filas:
                    cursor.execute('''SELECT * FROM partidos_baloncesto WHERE competicion_id=%s
                        AND equipo_local_id=%s AND equipo_visitante_id=%s
                        AND fecha_partido BETWEEN %s::date-2 AND %s::date+2''',
                        (contexto.competicion_id, registro['equipo_local_id'], registro['equipo_visitante_id'],
                         registro['fecha_partido'], registro['fecha_partido']))
                    filas = cursor.fetchall()
                if len(filas) > 1:
                    raise ValueError('IDENTIDAD_AMBIGUA')
                anterior = filas[0] if filas else None
                if anterior:
                    if anterior['valido'] is not True:
                        raise ValueError('FILA_INVALIDADA_CONSERVADA')
                    for clave in ('competicion_id', 'temporada_id', 'equipo_local_id', 'equipo_visitante_id', 'tipo_partido'):
                        if str(anterior[clave]) != str(registro[clave]):
                            raise ValueError('IDENTIDAD_EN_CONFLICTO: ' + clave)
                    for clave in ('source_game_id', 'espn_game_id'):
                        if anterior[clave] and str(anterior[clave]) != ident:
                            raise ValueError('ID_FUENTE_EN_CONFLICTO')
                    diferencias = {k: registro[k] for k in CAMPOS_RESULTADO if anterior[k] != registro[k]}
                    if diferencias and anterior['valido'] and anterior['local_total'] and anterior['visitante_total']:
                        raise ValueError('FINAL_EXISTENTE_EN_CONFLICTO')
                    accion = 'ACTUALIZAR' if diferencias else 'COINCIDENTE'
                else:
                    accion = 'INSERTAR'
                item.update(accion=accion, antes=anterior, registro=registro,
                            antes_sha256=huella(anterior) if anterior else None,
                            evento=evento, anio_fin=anio_fin)
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                item.update(accion='EXCLUIDO', motivo=str(exc))
            salida.append(item)
    return salida


def aplicar(conn, plan):
    """Una transacción externa controla commit/rollback. Repetición no toca timestamps."""
    from psycopg import sql
    from scripts.actualizar_partidos_nba import upsert_records
    conteos = {'insertados': 0, 'actualizados': 0, 'coincidentes': 0, 'excluidos': 0}
    conn.execute("SELECT pg_advisory_xact_lock(hashtext('ap_refresco_nba_manual'))")
    for item in plan:
        accion = item['accion']
        if accion == 'EXCLUIDO':
            conteos['excluidos'] += 1
            continue
        registro = item['registro']
        if accion == 'INSERTAR':
            # La unicidad se coteja de nuevo dentro de la transacción, sin upsert ciego.
            nuevo = planificar(conn, [item['evento']], item['anio_fin'])[0]
            if nuevo['accion'] != 'INSERTAR':
                raise ValueError('El destino cambió desde la vista previa')
            conteos['insertados'] += upsert_records(conn, [registro], False)['inserted']
            continue
        with conn.cursor(row_factory=dict_row) as cursor:
            actual = cursor.execute('SELECT * FROM partidos_baloncesto WHERE id=%s FOR UPDATE', (item['antes']['id'],)).fetchone()
            if huella(actual) != item['antes_sha256']:
                raise ValueError('La fila cambió desde la vista previa; regenerar plan')
        if accion == 'COINCIDENTE':
            conteos['coincidentes'] += 1
            continue
        campos = CAMPOS_RESULTADO + ('ganador_id', 'diferencia_puntos', 'hubo_overtime')
        sentencia = sql.SQL('UPDATE partidos_baloncesto SET {},actualizado_en=now() WHERE id=%s').format(
            sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in campos))
        conn.execute(sentencia, [registro[k] for k in campos] + [item['antes']['id']])
        conteos['actualizados'] += 1
    return conteos
