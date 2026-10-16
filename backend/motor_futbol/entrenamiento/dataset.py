"""Selección efectiva por familia; NULL nunca se convierte en un resultado cero."""
from collections import Counter
import hashlib
import json
import math
from numbers import Real

from ..tipos import TipoModelo, normalizar_nombre_equipo


CAMPOS = {
    TipoModelo.CORNERS: [f'{lado}_corners_{tiempo}' for lado in ('local', 'visitante') for tiempo in ('1t', '2t')],
    TipoModelo.GOLES: [f'{lado}_goles_{tiempo}' for lado in ('local', 'visitante') for tiempo in ('1t', '2t')],
    TipoModelo.DISPAROS: [f'{lado}_disparos_{target}' for lado in ('local', 'visitante') for target in ('total', 'arco')],
}


def motivo_exclusion(partido, tipo):
    if partido.get('valido') is False or partido.get('estado', 'FINALIZADO') != 'FINALIZADO':
        return 'no_final_o_invalido'
    if not all(partido.get(k) for k in ('id', 'fecha_partido', 'equipo_local', 'equipo_visitante')):
        return 'identidad_incompleta'
    if normalizar_nombre_equipo(partido['equipo_local']) == normalizar_nombre_equipo(partido['equipo_visitante']):
        return 'mismo_equipo'
    valores = [partido.get(k) for k in CAMPOS[tipo]]
    if any(v is None for v in valores):
        return 'target_ausente'
    if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) or v < 0 or int(v) != v for v in valores):
        return 'target_invalido'
    for lado in ('local', 'visitante'):
        if tipo == TipoModelo.DISPAROS:
            if partido[f'{lado}_disparos_arco'] > partido[f'{lado}_disparos_total']:
                return 'arco_mayor_que_total'
        else:
            total = partido.get(f'{lado}_{tipo.value}_total')
            if total is not None and total != sum(partido[f'{lado}_{tipo.value}_{t}'] for t in ('1t', '2t')):
                return 'tiempos_incompatibles_con_total'
    return None


def seleccionar(partidos, tipo, min_partidos_equipo=1):
    tipo = TipoModelo(tipo)
    validos, excluidos = [], Counter()
    ids = [str(p.get('id')) for p in partidos]
    duplicados = {ident for ident, n in Counter(ids).items() if n > 1}
    for p in partidos:
        motivo = 'id_duplicado' if str(p.get('id')) in duplicados else motivo_exclusion(p, tipo)
        if motivo:
            excluidos[motivo] += 1
        else:
            validos.append(p)
    # La poda es iterativa: retirar un rival puede dejar otro equipo sin soporte.
    while validos:
        conteos = Counter(normalizar_nombre_equipo(p[k]) for p in validos for k in ('equipo_local', 'equipo_visitante'))
        conservados = [p for p in validos if all(conteos[normalizar_nombre_equipo(p[k])] >= min_partidos_equipo for k in ('equipo_local', 'equipo_visitante'))]
        if len(conservados) == len(validos):
            break
        excluidos['equipo_sin_minimo'] += len(validos)-len(conservados)
        validos = conservados
    validos.sort(key=lambda p: (p['fecha_partido'], str(p['id'])))
    return validos, dict(excluidos)


def describir(partidos, tipo, excluidos=None):
    """Hash de identidades, valores y fechas EFECTIVAMENTE usados, no solo IDs."""
    columnas = ['id', 'fecha_partido', 'equipo_local', 'equipo_visitante', 'competicion_id', 'temporada_id', *CAMPOS[TipoModelo(tipo)]]
    filas = [{k: p.get(k) for k in columnas} for p in sorted(partidos, key=lambda p: (p['fecha_partido'], str(p['id'])))]
    contenido = json.dumps(filas, default=str, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return {
        'politica': 'final_valido_targets_completos_coherentes_v1',
        'hash_sha256': hashlib.sha256(contenido.encode()).hexdigest(),
        'n_partidos': len(partidos), 'n_filas_diseno': 2*len(partidos),
        'fecha_min': min((p['fecha_partido'] for p in partidos), default=None).isoformat() if partidos else None,
        'fecha_max': max((p['fecha_partido'] for p in partidos), default=None).isoformat() if partidos else None,
        'equipos': sorted({normalizar_nombre_equipo(p[k]) for p in partidos for k in ('equipo_local', 'equipo_visitante')}),
        'competiciones': sorted({str(p.get('competicion_id')) for p in partidos}),
        'temporadas': sorted({str(p.get('temporada_id')) for p in partidos}),
        'excluidos': excluidos or {},
        'disponibilidad_historica_acreditada': False,
    }
