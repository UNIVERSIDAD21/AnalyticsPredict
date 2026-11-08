"""Control de agenda colombiana, puro y sin red. Nunca inventa la fecha correcta.

Un timeValid de ESPN no acredita un horario cuando el mismo club disputa dos
encuentros incompatibles. Las filas dudosas se conservan, pero no son utilizables.
Una confirmación oficial exacta tiene precedencia sobre un calendario genérico.
"""
from datetime import datetime, timedelta

CONTRATO = 'COL_AGENDA_CONFLICTO_V1'
UMBRAL = timedelta(hours=24)


def instante(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Agenda sin zona horaria')
    return result


def confirmacion_oficial(meta):
    proof = (meta or {}).get('evidencia', {}).get('confirmacion_agenda', {})
    return proof if (proof.get('proveedor') == 'DIMAYOR_OFFICIAL'
                     and proof.get('url', '').startswith('https://dimayor.com.co/')
                     and proof.get('inicio_utc') and proof.get('sha256')) else None


def en_cuarentena(meta):
    return (meta or {}).get('evidencia', {}).get('cuarentena_agenda', {}).get('contrato') == CONTRATO


def conflictos(registros, partidos, horarios, enlaces):
    """Evalúa el lote completo y las filas vigentes; nunca depende del orden.

    Solo bloquea no-finales de COL_PRIMERAA. Finales y confirmaciones oficiales
    sobreviven a un choque con un fixture genérico, sin elegir por mayoría.
    El ID de origen y los clubes se vinculan exclusivamente mediante crosswalks.
    """
    by_id = {p['id']: p for p in partidos}
    source = {(x['liga'], x['id_fuente']): x['partido_id'] for x in enlaces}
    incoming = {}
    for row in registros:
        if row['deporte'] != 'futbol' or row['codigo'] != 'COL_PRIMERAA':
            continue
        pid = source.get((row['feed'], row['id_fuente']))
        old = by_id.get(pid)
        if not row.get('inicio_utc') or not row.get('local_id') or not row.get('visitante_id'):
            continue
        meta = horarios.get(pid)
        proof = confirmacion_oficial(meta)
        # Una captura incompatible no desplaza una confirmación oficial previa.
        official = bool(proof and instante(proof['inicio_utc']) == instante(row['inicio_utc']))
        incoming[pid or ('fuente:' + row['id_fuente'])] = {
            'id': pid, 'evento': row['id_fuente'], 'inicio': instante(row['inicio_utc']),
            'equipos': {row['local_id'], row['visitante_id']},
            'protegido': row['estado'] in ('FINALIZADO', 'EN_VIVO') or official,
            'evaluable': row['estado'] == 'PROGRAMADO' and not (old and old['estado'] == 'FINALIZADO')}
    candidates = dict(incoming)
    for pid, p in by_id.items():
        meta = horarios.get(pid)
        if not p.get('valido') or not meta or meta['competicion_codigo'] != 'COL_PRIMERAA':
            continue
        proof = confirmacion_oficial(meta)
        # Si la fuente intenta desplazar un final/confirmado, conserva también
        # la reserva acreditada para detectar colisiones con otros eventos.
        protected = p['estado'] == 'FINALIZADO' or bool(proof)
        if pid in candidates and not protected:
            continue
        if p['estado'] not in ('PROGRAMADO', 'EN_VIVO', 'FINALIZADO'):
            continue
        start = proof['inicio_utc'] if proof else meta.get('inicio_utc') or p['fecha_partido']
        candidates[('canonico:' + pid) if pid in candidates else pid] = {
            'id': pid, 'evento': None, 'inicio': instante(start),
            'equipos': {p['equipo_local_id'], p['equipo_visitante_id']},
            'protegido': protected, 'evaluable': False}
    blocked = {}
    for key, item in incoming.items():
        if not item['evaluable'] or item['protegido']:
            continue
        clashes = [other for k, other in candidates.items() if k != key
                   and (item['id'] is None or other['id'] != item['id'])
                   and item['equipos'] & other['equipos']
                   and abs(item['inicio'] - other['inicio']) < UMBRAL]
        if clashes:
            blocked[item['evento']] = {
                'contrato': CONTRATO, 'motivo': 'EQUIPO_CON_PARTIDOS_INCOMPATIBLES',
                'inicio_rechazado': item['inicio'].isoformat(),
                'conflictos': sorted({str(x['id'] or x['evento']) for x in clashes}),
                'limite': 'No acredita cancelación ni nueva fecha; requiere programación conciliada'}
    return blocked


def puede_reactivar(old, meta, row):
    """Solo nuestra cuarentena sin resultado, con otra hora y captura posterior.

    El llamador ya debió descartar choques en el lote y en el calendario vigente.
    Una invalidez histórica/manual nunca se rehabilita por este mecanismo.
    """
    if not old or old.get('valido') or not en_cuarentena(meta):
        return False
    quarantine = meta['evidencia']['cuarentena_agenda']
    return (old['estado'] == 'PROGRAMADO' and row['estado'] == 'PROGRAMADO'
            and all(old.get(k) is None for k in ('local_goles_total', 'visitante_goles_total'))
            and bool(row.get('inicio_utc'))
            and instante(row['inicio_utc']) != instante(quarantine['inicio_rechazado'])
            and instante(row['evidencia']['observado_en']) > instante(quarantine.get('rechazado_en') or meta['observado_en']))
