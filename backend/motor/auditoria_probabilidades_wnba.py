"""Reproduce métricas de la cohorte guardada. No selecciona, ajusta ni calibra."""
import math
import numpy as np

from motor.contraccion_wnba_experimental import validar_publicacion
from motor.wnba import MERCADOS, exigir, huella, medias, probabilidades


def metricas_guardadas(y, mu, varianza, linea, entera):
    y, mu = np.asarray(y, dtype=float), np.asarray(mu, dtype=float)
    exigir(y.shape == mu.shape and y.ndim == 1 and len(y) > 0 and np.isfinite(y).all() and np.isfinite(mu).all(), 'Cohorte vacía o valores inválidos')
    p = np.asarray([list(probabilidades(float(m), varianza, linea).values()) for m in mu])
    target = np.asarray([[v > linea, v < linea, v == linea] for v in y], dtype=float)
    pi = np.asarray([list(probabilidades(float(m), varianza, entera).values()) for m in mu])
    ti = np.asarray([[v > entera, v < entera, v == entera] for v in y], dtype=float)
    bins = []
    for i in range(10):
        mascara = (p[:, 0] >= i/10) & ((p[:, 0] < (i+1)/10) if i < 9 else (p[:, 0] <= 1))
        bins.append({'desde': i/10, 'hasta': (i+1)/10, 'n': int(mascara.sum()),
                     'probabilidad_media': float(p[mascara, 0].mean()) if mascara.any() else None,
                     'frecuencia_observada': float(target[mascara, 0].mean()) if mascara.any() else None})
    return {'n': len(y), 'mae': float(np.abs(mu-y).mean()), 'linea': linea,
            'brier_multiclase': float(((p-target)**2).sum(axis=1).mean()),
            'log_loss': float(-(target*np.log(np.maximum(p, 1e-12))).sum(axis=1).mean()),
            'linea_entera': entera, 'brier_con_push': float(((pi-ti)**2).sum(axis=1).mean()),
            'push_observados': int((y == entera).sum()), 'calibracion_bins': bins,
            'cobertura_intervalo80': float((np.abs(mu-y) <= 1.2815515655*math.sqrt(varianza)).mean())}


def _diferencia(a, b):
    if isinstance(a, dict):
        return max((_diferencia(v, b[k]) for k,v in a.items()), default=0.)
    if isinstance(a, list):
        exigir(len(a) == len(b), 'Bins originales alterados')
        return max((_diferencia(x,y) for x,y in zip(a,b)), default=0.)
    if a is None or b is None:
        exigir(a is b, 'Ausencia alterada en métrica original')
        return 0.
    exigir(math.isfinite(float(b)), 'Métrica original no finita')
    return abs(a-b)


def auditar(publicacion):
    validar_publicacion(publicacion)
    v = publicacion['validacion']; cohorte = v['cohorte']; modelo = v['candidato']
    mapa = {r['id']: r for r in publicacion['datos']}
    ids = [r['id'] for r in cohorte]
    rechazados = [r['id'] for r in v['rechazados']]
    elegibles = {r['id'] for r in publicacion['datos'] if r['fase'] == 'REG' and r['fecha'] >= '2025-01-01'}
    exigir(len(set(ids)) == len(ids) and len(set(rechazados)) == len(rechazados) and not set(ids).intersection(rechazados)
           and set(ids).union(rechazados) == elegibles, 'Denominador original no conciliado')
    exigir(len(elegibles) == v['evaluacion']['partidos'] and len(ids) == v['evaluacion']['analizados']
           and len(rechazados) == v['evaluacion']['abstenciones'], 'Conteos originales no conciliados')
    exigir(all(r['fecha'] == mapa[r['id']]['fecha'] and r['observado'] == mapa[r['id']]['y'] for r in cohorte), 'Outcomes originales no conciliados')
    guardadas = np.asarray([r['proyeccion'] for r in cohorte])
    delta = float(np.max(np.abs(medias(modelo, [mapa[i] for i in ids])-guardadas)))
    exigir(delta <= 1e-10, 'Proyecciones originales no reproducidas')
    verdad = np.asarray([r['observado'] for r in cohorte]); cov = np.asarray(modelo['covarianza'])
    resultados = {}
    for mercado, ix in MERCADOS.items():
        original = v['evaluacion']['mercados'][mercado]
        calculado = metricas_guardadas(verdad[:,ix].sum(axis=1), guardadas[:,ix].sum(axis=1),
                                       float(cov[np.ix_(ix,ix)].sum()), original['linea'], original['linea_entera'])
        diferencia = _diferencia(calculado, original)
        exigir(diferencia <= 1e-10, f'Métricas originales no reproducidas: {mercado}')
        resultados[mercado] = {'reproducido': calculado, 'max_delta_metricas': diferencia}
    salida = {'formato': 'auditoria-probabilidades-wnba-v1', 'publicacion': publicacion['version'],
              'candidato_version': v['candidato_version'], 'dataset_sha256': publicacion['dataset_sha256'],
              'cohorte_sha256': huella(cohorte), 'denominador': len(elegibles), 'analizados': len(ids),
              'abstenciones': len(rechazados), 'max_delta_proyeccion': delta, 'mercados': resultados,
              'refit_realizado': False, 'calibrador': None, 'activado': False, 'prospectivos': 0,
              'limite': 'Auditoría retrospectiva de métricas del candidato original, no del refit final. EVAL ya observado. No certifica fiabilidad futura ni probabilidades OT. Brier es suma de tres clases, no Brier binario. No se seleccionó ni ajustó calibrador.'}
    salida['auditoria_sha256'] = huella(salida)
    return salida
