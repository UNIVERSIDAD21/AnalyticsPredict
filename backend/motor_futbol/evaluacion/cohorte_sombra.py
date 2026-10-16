"""Evaluación posterior de una cohorte de laboratorio, sin promover modelos."""
from collections import Counter
from datetime import datetime

from ..entrenamiento.dataset import motivo_exclusion
from ..modelos.artefacto import sha256
from ..tipos import TipoModelo, normalizar_nombre_equipo
from .estacional import exigir_utc
from .temporal_ridge import metricas


def evaluar_cohorte(cohorte, partidos, observado_en):
    observado = exigir_utc(observado_en)
    cuerpo = {k: v for k, v in cohorte.items() if k != 'sha256'}
    if cohorte.get('sha256') != sha256(cuerpo):
        raise ValueError('La cohorte congelada no conserva su hash')
    if observado <= exigir_utc(datetime.fromisoformat(cohorte['congelado_en'])):
        raise ValueError('Se requieren observaciones posteriores al congelamiento')
    ids = [str(p['id']) for p in partidos]
    if len(ids) != len(set(ids)): raise ValueError('Outcomes ambiguos por ID duplicado')
    por_id = {str(p['id']): p for p in partidos}
    resultados = {}
    for tipo, familia in cohorte['familias'].items():
        pred = familia['cohorte']['predicciones']; abst = familia['cohorte']['abstenciones']
        pares = []; exclusiones = Counter(); pendientes = 0
        for registro in pred:
            p = por_id.get(registro['partido_id'])
            if p is None or p.get('estado') != 'FINALIZADO' or p['fecha_partido'] >= observado:
                pendientes += 1; continue
            if (exigir_utc(p['fecha_partido']).isoformat() != exigir_utc(datetime.fromisoformat(registro['inicio_utc'])).isoformat()
                    or any(normalizar_nombre_equipo(p[k]) != normalizar_nombre_equipo(registro[k])
                           for k in ('equipo_local', 'equipo_visitante'))):
                exclusiones['IDENTIDAD_O_INICIO_CAMBIADO'] += 1; continue
            motivo = motivo_exclusion(p, TipoModelo(tipo))
            if motivo:
                exclusiones[motivo] += 1; continue
            targets = familia['candidato']['targets']
            pares.append({'partido_id': registro['partido_id'], 'fecha': registro['inicio_utc'],
                'real': [p[k] for k in targets],
                'prediccion': [registro['prediccion_sin_recorte'][k] for k in targets],
                'baseline': [registro['baseline'][k] for k in targets]})
        m = metricas(pares, 1000, 42, familia['candidato']['targets'])
        candidatos = len(pred)+len(abst)
        meses = Counter(p['fecha'][:7] for p in pares)
        politica = familia['candidato']['politica']
        motivos = []
        if len(pares) < politica['min_eval']: motivos.append('MASA_EVAL_INSUFICIENTE')
        if sum(n >= politica['min_por_ventana'] for n in meses.values()) < politica['min_ventanas_eval']:
            motivos.append('POCAS_VENTANAS')
        cobertura = len(pares)/candidatos if candidatos else None
        if cobertura is None or cobertura < politica['cobertura_minima']: motivos.append('COBERTURA_INSUFICIENTE')
        if m['ic95_delta_mae'] is None or m['ic95_delta_mae'][1] >= 0: motivos.append('MEJORA_NO_ACREDITADA')
        if any(v['mae'] > v['mae_baseline'] for v in m['por_target'].values()): motivos.append('TARGET_PEOR_QUE_BASELINE')
        ultimo = max((exigir_utc(datetime.fromisoformat(p['fecha'])) for p in pares), default=None)
        if ultimo is None or (observado-ultimo).total_seconds() > politica['max_antiguedad_target_dias']*86400:
            motivos.append('TARGET_SIN_FRESCURA')
        if pendientes: motivos.append('OUTCOMES_PENDIENTES')
        if observado < exigir_utc(datetime.fromisoformat(cohorte['declaracion']['fin_eval'])):
            motivos.append('PERIODO_NO_CERRADO')
        resultados[tipo] = {'metricas': m, 'candidatos': candidatos, 'predicciones': len(pred),
            'abstenciones': len(abst), 'pendientes': pendientes, 'exclusiones': dict(exclusiones),
            'cobertura_resuelta_total': cobertura, 'meses_utc': dict(meses), 'motivos': motivos,
            'activable': False, 'certificacion': 'NO_CERTIFICADO',
            'nota': 'Esta evaluación no acredita disponibilidad histórica ni independencia de la fuente.'}
    return {'cohorte_sha256': cohorte['sha256'], 'observado_en': observado.isoformat(), 'familias': resultados,
            'certificacion': 'NO_CERTIFICADO', 'p_calibrada': None}
