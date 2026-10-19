"""ML V4 aislado: forma causal, selección temporal y nueva cohorte futura.

El refit final crea OTRO artefacto después del desarrollo: su única prueba fuera
de muestra es la cohorte futura. No publica versiones ni probabilidades en serving.
"""
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from itertools import groupby

import numpy as np

from ..entrenamiento.dataset import CAMPOS, describir, motivo_exclusion, seleccionar
from ..modelos.artefacto import sha256
from ..tipos import TipoModelo, normalizar_nombre_equipo as normalizar
from .estacional import exigir_utc
from .temporal_ridge import LIGAS, metricas


NOMBRES_FORMA = ([f'liga_{liga}' for liga in LIGAS] +
                 [f'{lado}_{dato}' for lado in ('local', 'visitante')
                  for dato in ([f'media_{h}_{t}' for h in (5, 20)
                                for t in ('favor_1', 'favor_2', 'contra_1', 'contra_2')] +
                               ['descanso_limitado_60d', 'historial_limitado_60'])])


@dataclass(frozen=True)
class PoliticaForma:
    version: str = 'forma_temporal_v4'
    desde: str = '2023-07-01T00:00:00+00:00'
    meses_desarrollo: tuple = ('2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-09', '2026-10')
    disenos: tuple = ('identidad', 'forma', 'hibrido')
    alphas: tuple = (1.0, 5.0, 10.0)
    horizontes_forma: tuple = (5, 20)
    min_train: int = 500
    objetivo_cal: int = 200
    min_cal: int = 100
    min_partidos_equipo: int = 5
    max_dias_cal: int = 180
    min_eval: int = 100
    min_meses: int = 2
    min_por_mes: int = 30
    cobertura_minima: float = .90
    max_antiguedad_dias: int = 60
    bootstrap_repeticiones: int = 1000
    semilla: int = 42

    def to_dict(self):
        return {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(self).items()}

    def validar(self):
        # Otro protocolo, no interruptores para rebajar gates después de medir.
        if self.to_dict() != PoliticaForma().to_dict():
            raise ValueError('V4 exige la política completa predeclarada, sin rebajar controles')


def validar_filas(partidos):
    ids = [str(p.get('id', '')) for p in partidos]
    if any(not ident or ident == 'None' for ident in ids) or len(ids) != len(set(ids)):
        raise ValueError('Identidades ausentes o duplicadas')
    for p in partidos:
        exigir_utc(p['fecha_partido'])
        if not all(p.get(k) for k in ('equipo_local', 'equipo_visitante', 'competicion_codigo')):
            raise ValueError('Identidad de equipos/competición incompleta')


def sellar(cuerpo):
    return {**cuerpo, 'sha256': sha256(cuerpo)}


def verificar(objeto):
    if objeto.get('sha256') != sha256({k: v for k, v in objeto.items() if k != 'sha256'}):
        raise ValueError('Artefacto o cohorte no conserva su hash')


def estado_vacio():
    return {'equipos': {}, 'ligas': {}}


def actualizar(estado, partido, tipo):
    valores = [float(partido[k]) for k in CAMPOS[tipo]]
    for lado, indices in (('local', [0, 1, 2, 3]), ('visitante', [2, 3, 0, 1])):
        nombre = normalizar(partido['equipo_' + lado])
        equipo = estado['equipos'].setdefault(nombre, {'n': 0, 'ultimos': [], 'ultimo': None})
        equipo['n'] += 1
        equipo['ultimos'] = (equipo['ultimos'] + [[valores[i] for i in indices]])[-20:]
        equipo['ultimo'] = exigir_utc(partido['fecha_partido']).isoformat()
    liga = estado['ligas'].setdefault(partido['competicion_codigo'], {'n': 0, 'suma': [0.] * 4})
    liga['n'] += 1
    liga['suma'] = [x + y for x, y in zip(liga['suma'], valores)]


def features_forma(estado, partido):
    """Solo observaciones anteriores; ausencias de target NO se imputan a cero."""
    fecha = exigir_utc(partido['fecha_partido'])
    locales = [normalizar(partido['equipo_' + lado]) for lado in ('local', 'visitante')]
    if any(estado['equipos'].get(n, {}).get('n', 0) < 5 for n in locales):
        return None
    vector = [float(partido['competicion_codigo'] == liga) for liga in LIGAS]
    for nombre in locales:
        equipo = estado['equipos'][nombre]
        ultimo = exigir_utc(datetime.fromisoformat(equipo['ultimo']))
        if ultimo >= fecha:
            raise ValueError('La forma contiene un resultado contemporáneo o futuro')
        for horizonte in (5, 20):
            vector.extend(np.mean(equipo['ultimos'][-horizonte:], axis=0).tolist())
        vector.extend([min((fecha - ultimo).total_seconds() / 86400, 60) / 60,
                       min(equipo['n'], 60) / 60])
    return vector


def historial_causal(validos, tipo):
    """Predice el grupo de instantes empatados ANTES de incorporar sus outcomes."""
    estado = estado_vacio()
    filas = []
    for _, grupo in groupby(validos, key=lambda p: p['fecha_partido']):
        grupo = list(grupo)
        for p in grupo:
            forma = features_forma(estado, p)
            if forma is not None:
                filas.append({'partido': p, 'forma': forma})
        for p in grupo:
            actualizar(estado, p, tipo)
    return filas, estado


def matriz(filas, diseno, entidades):
    resultado = []
    for fila in filas:
        p = fila['partido']
        identidad = [0.] * (2 * len(entidades))
        for lado, offset in (('local', 0), ('visitante', len(entidades))):
            nombre = normalizar(p['equipo_' + lado])
            if nombre in entidades:
                identidad[offset + entidades[nombre]] = 1.
        liga = fila['forma'][:len(LIGAS)]
        resultado.append(liga + identidad if diseno == 'identidad' else (
            fila['forma'] if diseno == 'forma' else fila['forma'] + identidad))
    return np.asarray(resultado, dtype=float)


def ajustar(x, y, alpha):
    media, escala = x.mean(axis=0), x.std(axis=0)
    escala[escala < 1e-12] = 1.
    z = np.column_stack((np.ones(len(x)), (x - media) / escala))
    regularizacion = np.eye(z.shape[1]) * alpha
    regularizacion[0, 0] = 0  # Intercepto no penalizado.
    pesos = np.linalg.solve(z.T @ z + regularizacion, z.T @ y)
    return {'media': media.tolist(), 'escala': escala.tolist(), 'pesos': pesos.tolist()}


def aplicar(ajuste, x, tipo):
    z = np.column_stack((np.ones(len(x)), (x - ajuste['media']) / ajuste['escala']))
    pred = np.maximum(z @ np.asarray(ajuste['pesos']), 0.)
    if tipo == TipoModelo.DISPAROS:
        pred[:, 1] = np.minimum(pred[:, 1], pred[:, 0])
        pred[:, 3] = np.minimum(pred[:, 3], pred[:, 2])
    return pred


def entidades_de(estado):
    return {n: i for i, n in enumerate(sorted(n for n, e in estado['equipos'].items() if e['n'] >= 5))}


def describir_forma(partidos, tipo, exclusiones=None):
    descripcion = describir(partidos, tipo, exclusiones)
    # El descriptor legacy asume dos perspectivas; V4 usa UNA fila por evento.
    return {**descripcion, 'n_filas_diseno': len(partidos),
            'politica_features': 'forma_causal_una_fila_por_partido_v4'}


def construir_candidato(partidos, tipo, corte, politica=None):
    """CAL selecciona diseño/alpha; refit explícito crea un candidato NUEVO.

    El modelo reajustado no hereda métricas de CAL como eficacia del artefacto final.
    Los 500 TRAIN y 100 CAL siguen siendo mínimos separados antes de seleccionar.
    """
    politica = politica or PoliticaForma()
    politica.validar()
    validar_filas(partidos)
    corte, tipo = exigir_utc(corte), TipoModelo(tipo)
    acotados = [p for p in partidos if p['competicion_codigo'] in LIGAS
                and exigir_utc(datetime.fromisoformat(politica.desde)) <= p['fecha_partido'] < corte]
    validos, exclusiones = seleccionar(acotados, tipo)
    filas, estado_final = historial_causal(validos, tipo)
    recientes = [p for p in validos if p['fecha_partido'] >= corte - timedelta(days=politica.max_dias_cal)]
    limite = (recientes[-politica.objetivo_cal] if len(recientes) >= politica.objetivo_cal else (
        recientes[0] if recientes else {'fecha_partido': corte}))['fecha_partido']
    train_raw = [p for p in validos if p['fecha_partido'] < limite]
    _, estado_train = historial_causal(train_raw, tipo)
    entidades = entidades_de(estado_train)
    train = [f for f in filas if f['partido']['fecha_partido'] < limite]
    cal = [f for f in filas if limite <= f['partido']['fecha_partido'] < corte
           and all(normalizar(f['partido']['equipo_' + l]) in entidades for l in ('local', 'visitante'))]
    salida = {'version': politica.version, 'tipo': tipo.value, 'corte': corte.isoformat(),
              'politica': politica.to_dict(), 'estado': 'SIN_CANDIDATO', 'motivos': [],
              'targets': CAMPOS[tipo], 'train_seleccion': describir_forma([f['partido'] for f in train], tipo),
              'cal_seleccion': describir_forma([f['partido'] for f in cal], tipo),
              'n_cal_candidatos': len(recientes) if len(recientes) < 200 else sum(p['fecha_partido'] >= limite for p in recientes),
              'exclusiones_datos': exclusiones, 'busqueda': [], 'activable': False,
              'calibrador_probabilidades': None, 'certificacion': 'NO_CERTIFICADO',
              'disponibilidad_historica_acreditada': False}
    if len(train) < politica.min_train:
        salida['motivos'].append('TRAIN_INSUFICIENTE')
    if len(cal) < politica.min_cal:
        salida['motivos'].append('CAL_INSUFICIENTE')
    if not validos or (corte - validos[-1]['fecha_partido']).total_seconds() > politica.max_antiguedad_dias * 86400:
        salida['motivos'].append('TARGET_SIN_FRESCURA')
    if salida['motivos']:
        return sellar(salida)
    y = np.asarray([[f['partido'][k] for k in CAMPOS[tipo]] for f in train], dtype=float)
    yc = np.asarray([[f['partido'][k] for k in CAMPOS[tipo]] for f in cal], dtype=float)
    mejor = None
    for diseno in politica.disenos:
        x, xc = matriz(train, diseno, entidades), matriz(cal, diseno, entidades)
        for alpha in politica.alphas:
            ajuste = ajustar(x, y, alpha)
            mae = float(np.abs(aplicar(ajuste, xc, tipo) - yc).mean())
            salida['busqueda'].append({'diseno': diseno, 'alpha': alpha, 'mae_cal': mae})
            if mejor is None or mae < mejor[0]:
                mejor = (mae, diseno, alpha)
    # Ningún outcome posterior al corte. No usar el MAE CAL como métrica de este refit.
    entidades_finales = entidades_de(estado_final)
    yf = np.asarray([[f['partido'][k] for k in CAMPOS[tipo]] for f in filas], dtype=float)
    ajuste_final = ajustar(matriz(filas, mejor[1], entidades_finales), yf, mejor[2])
    estaticos = [b for b in salida['busqueda'] if b['diseno'] == 'identidad']
    alpha_control = min(estaticos, key=lambda b: b['mae_cal'])['alpha']
    ajuste_control = ajustar(matriz(filas, 'identidad', entidades_finales), yf, alpha_control)
    salida.update(estado='CANDIDATO_SOMBRA', diseno=mejor[1], alpha=mejor[2], ajuste=ajuste_final,
                  control_identidad={'alpha': alpha_control, 'ajuste': ajuste_control},
                  entidades=entidades_finales, estado_forma=estado_final,
                  dataset_refit=describir_forma([f['partido'] for f in filas], tipo),
                  dataset_fuente=describir_forma(validos, tipo, exclusiones),
                  refit='TRAIN+CAL anteriores al corte; prueba del artefacto final SOLO en nueva cohorte futura',
                  metricas_artefacto_final=None)
    nombres_identidad = [f'{lado}_{n}' for lado in ('local', 'visitante') for n in entidades_finales]
    salida['feature_names'] = (NOMBRES_FORMA[:len(LIGAS)] + nombres_identidad if mejor[1] == 'identidad'
                               else NOMBRES_FORMA if mejor[1] == 'forma' else NOMBRES_FORMA + nombres_identidad)
    return sellar(salida)


def predecir(candidato, partido):
    verificar(candidato)
    if candidato['estado'] != 'CANDIDATO_SOMBRA':
        return {'motivo': 'SIN_CANDIDATO'}
    if partido['competicion_codigo'] not in LIGAS:
        return {'motivo': 'FUERA_DE_LIGAS'}
    if normalizar(partido['equipo_local']) == normalizar(partido['equipo_visitante']):
        return {'motivo': 'MISMO_EQUIPO'}
    if exigir_utc(partido['fecha_partido']) < exigir_utc(datetime.fromisoformat(candidato['corte'])):
        return {'motivo': 'NO_POSTERIOR_AL_CORTE'}
    if partido['competicion_codigo'] not in candidato['estado_forma']['ligas']:
        return {'motivo': 'LIGA_SIN_TRAIN'}
    forma = features_forma(candidato['estado_forma'], partido)
    if forma is None:
        return {'motivo': 'EQUIPO_SIN_CINCO_ANTECEDENTES_TRAIN'}
    fila = {'partido': partido, 'forma': forma}
    tipo = TipoModelo(candidato['tipo'])
    x = matriz([fila], candidato['diseno'], candidato['entidades'])
    control = candidato['control_identidad']
    base = candidato['estado_forma']['ligas'][partido['competicion_codigo']]
    return {'motivo': None, 'prediccion': aplicar(candidato['ajuste'], x, tipo)[0].tolist(),
            'control_identidad': aplicar(control['ajuste'], matriz([fila], 'identidad', candidato['entidades']), tipo)[0].tolist(),
            'baseline': [x / base['n'] for x in base['suma']], 'features': x[0].tolist()}


def resumir(pares, candidatos, politica, observado, fin, meses_requeridos=True, targets=None):
    m = metricas(pares, politica.bootstrap_repeticiones, politica.semilla, targets)
    meses = Counter(f['fecha'][:7] for f in pares)
    dias = sorted({f['fecha'][:10] for f in pares})
    # IC por bloque día UTC; los encuentros de una jornada se remuestrean juntos.
    if dias:
        errores = {d: [float(np.mean(np.abs(np.asarray(f['prediccion']) - f['real']) -
                        np.abs(np.asarray(f['baseline']) - f['real'])))
                       for f in pares if f['fecha'][:10] == d] for d in dias}
        sumas = np.asarray([sum(errores[d]) for d in dias])
        conteos = np.asarray([len(errores[d]) for d in dias])
        rng = np.random.default_rng(politica.semilla)
        indices = rng.integers(0, len(dias), (politica.bootstrap_repeticiones, len(dias)))
        valores = sumas[indices].sum(axis=1) / conteos[indices].sum(axis=1)
        m['ic95_delta_mae_bloques_dia_utc'] = np.quantile(valores, [.025, .975]).tolist()
    else:
        m['ic95_delta_mae_bloques_dia_utc'] = None
    cobertura = len(pares) / candidatos if candidatos else None
    motivos = []
    if len(pares) < politica.min_eval:
        motivos.append('MASA_EVAL_INSUFICIENTE')
    if meses_requeridos and sum(n >= politica.min_por_mes for n in meses.values()) < politica.min_meses:
        motivos.append('POCOS_MESES')
    if cobertura is None or cobertura < politica.cobertura_minima:
        motivos.append('COBERTURA_INSUFICIENTE')
    for campo in ('ic95_delta_mae', 'ic95_delta_mae_bloques_dia_utc'):
        if m[campo] is None or m[campo][1] >= 0:
            motivos.append('MEJORA_NO_ACREDITADA_' + campo.upper())
    if any(t['mae'] > t['mae_baseline'] for t in m['por_target'].values()):
        motivos.append('TARGET_PEOR_QUE_BASELINE')
    ultimo = max((datetime.fromisoformat(f['fecha']) for f in pares), default=None)
    if ultimo is None or (observado - ultimo).total_seconds() > politica.max_antiguedad_dias * 86400:
        motivos.append('TARGET_SIN_FRESCURA')
    if observado < fin:
        motivos.append('PERIODO_NO_CERRADO')
    return {'metricas': m, 'candidatos': candidatos, 'cobertura_resuelta_total': cobertura,
            'meses_utc': dict(meses), 'motivos_estadisticos': motivos,
            'gate_estadistico_superado': not motivos, 'activable': False,
            'calibrador_probabilidades': None, 'certificacion': 'NO_CERTIFICADO'}


def desarrollar(partidos, corte, politica=None):
    politica = politica or PoliticaForma()
    politica.validar()
    validar_filas(partidos)
    corte = exigir_utc(corte)
    familias = {}
    for tipo in TipoModelo:
        ventanas, pares, controles = [], [], []
        total = 0
        for mes in politica.meses_desarrollo:
            inicio = datetime.fromisoformat(mes + '-01T00:00:00+00:00')
            siguiente = datetime(inicio.year + (inicio.month == 12), inicio.month % 12 + 1, 1, tzinfo=timezone.utc)
            fin = min(siguiente, corte)
            if inicio >= fin:
                continue
            candidato = construir_candidato(partidos, tipo, inicio, politica)
            eventos = [p for p in partidos if p['competicion_codigo'] in LIGAS and inicio <= p['fecha_partido'] < fin]
            total += len(eventos)
            filas, exclusiones = [], Counter()
            for p in eventos:
                resultado = predecir(candidato, p)
                motivo = resultado['motivo'] or motivo_exclusion(p, tipo)
                if motivo:
                    exclusiones[motivo] += 1
                    continue
                fila = {'partido_id': str(p['id']), 'fecha': exigir_utc(p['fecha_partido']).isoformat(),
                        'real': [p[k] for k in CAMPOS[tipo]], 'prediccion': resultado['prediccion'],
                        'baseline': resultado['baseline']}
                filas.append(fila)
                controles.append({**fila, 'prediccion': resultado['control_identidad']})
            pares.extend(filas)
            ventanas.append({'mes': mes, 'candidatos': len(eventos), 'pares': len(filas),
                             'exclusiones': dict(exclusiones), 'candidato': candidato})
        resumen = resumir(pares, total, politica, corte, corte, targets=CAMPOS[tipo])
        familias[tipo.value] = {'ventanas': ventanas, 'pares': pares, 'resumen': resumen,
                               'control_identidad': metricas(controles, targets=CAMPOS[tipo]),
                               'candidato_final': construir_candidato(partidos, tipo, corte, politica)}
    return sellar({'politica': politica.to_dict(), 'corte': corte.isoformat(), 'familias': familias,
                   'fit_completed_at': datetime.now(timezone.utc).isoformat(),
                   'ambito': 'DESARROLLO_RETROSPECTIVO_NO_CERTIFICADO',
                   'limite': 'Datos históricos ya observados; no son prueba independiente del refit final',
                   'modelo_activo': False, 'p_calibrada': None})


def congelar(desarrollo, fixtures, congelado, inicio, fin, declarado):
    verificar(desarrollo)
    validar_filas(fixtures)
    declarado, corte, congelado, inicio, fin = map(exigir_utc, (
        declarado, datetime.fromisoformat(desarrollo['corte']), congelado, inicio, fin))
    if not declarado <= corte < congelado < inicio < fin:
        raise ValueError('Orden obligatorio declaración <= snapshot < congelamiento < inicio < fin')
    if not corte < exigir_utc(datetime.fromisoformat(desarrollo['fit_completed_at'])) <= congelado:
        raise ValueError('El ajuste debe terminar después del snapshot y antes del congelamiento')
    familias = {}
    for tipo, familia in desarrollo['familias'].items():
        modelo = familia['candidato_final']
        predicciones, abstenciones = [], []
        for p in sorted(fixtures, key=lambda p: (p['fecha_partido'], str(p['id']))):
            if p['competicion_codigo'] not in LIGAS or not inicio <= p['fecha_partido'] < fin:
                continue
            identidad = {k: p[k] for k in ('equipo_local', 'equipo_visitante', 'competicion_codigo')}
            identidad.update(partido_id=str(p['id']), inicio_utc=exigir_utc(p['fecha_partido']).isoformat())
            resultado = predecir(modelo, p)
            motivo = ('NO_PROGRAMADO_O_INVALIDO' if p.get('estado') != 'PROGRAMADO' or p.get('valido') is False
                      else resultado['motivo'])
            if motivo:
                abstenciones.append({**identidad, 'motivo': motivo})
            else:
                predicciones.append({**identidad, **resultado, 'modelo_sha256': modelo['sha256'],
                                     'p_raw': None, 'p_calibrada': None})
        n = len(predicciones) + len(abstenciones)
        cobertura_maxima = len(predicciones) / n if n else None
        familias[tipo] = {'modelo': modelo, 'predicciones': predicciones, 'abstenciones': abstenciones,
                         'candidatos': n, 'cobertura_maxima': cobertura_maxima,
                         'cobertura_maxima_suficiente': cobertura_maxima is not None and cobertura_maxima >= .90}
    return sellar({'version': PoliticaForma().version, 'declarado_en': declarado.isoformat(),
                   'congelado_en': congelado.isoformat(), 'inicio_eval': inicio.isoformat(), 'fin_eval': fin.isoformat(),
                   'desarrollo_sha256': desarrollo['sha256'], 'familias': familias, 'modelo_activo': False,
                   'policy': {'no_picks': True, 'no_stake': True, 'no_betting_recommendations': True}})


def evaluar_congelada(cohorte, partidos, observado):
    verificar(cohorte)
    validar_filas(partidos)
    observado = exigir_utc(observado)
    if observado <= exigir_utc(datetime.fromisoformat(cohorte['congelado_en'])):
        raise ValueError('Se requiere observación posterior al congelamiento')
    por_id = {str(p['id']): p for p in partidos}
    resultados = {}
    for nombre, familia in cohorte['familias'].items():
        verificar(familia['modelo'])
        tipo = TipoModelo(nombre)
        pares, exclusiones, pendientes = [], Counter(), 0
        for registro in familia['predicciones']:
            p = por_id.get(registro['partido_id'])
            if p is None or p.get('estado') != 'FINALIZADO' or p['fecha_partido'] >= observado:
                pendientes += 1
                continue
            if (exigir_utc(p['fecha_partido']).isoformat() != registro['inicio_utc'] or
                    any(p[k] != registro[k] for k in ('equipo_local', 'equipo_visitante', 'competicion_codigo'))):
                exclusiones['IDENTIDAD_O_HORA_CAMBIADA'] += 1
                continue
            motivo = motivo_exclusion(p, tipo)
            if motivo:
                exclusiones[motivo] += 1
                continue
            pares.append({'partido_id': registro['partido_id'], 'fecha': registro['inicio_utc'],
                          'real': [p[k] for k in CAMPOS[tipo]], 'prediccion': registro['prediccion'],
                          'baseline': registro['baseline']})
        resumen = resumir(pares, len(familia['predicciones']) + len(familia['abstenciones']),
                          PoliticaForma(), observado, datetime.fromisoformat(cohorte['fin_eval']), targets=CAMPOS[tipo])
        if pendientes:
            resumen['motivos_estadisticos'].append('OUTCOMES_PENDIENTES')
            resumen['gate_estadistico_superado'] = False
        resumen.update(pendientes=pendientes, exclusiones=dict(exclusiones),
                       abstenciones=len(familia['abstenciones']), pares=pares,
                       motivos_no_activacion=['CALIBRACION_PROBABILISTICA_NO_ACREDITADA',
                                              'EVALUACION_NO_ES_PROMOCION_AUTOMATICA'])
        resultados[nombre] = resumen
    return sellar({'cohorte_sha256': cohorte['sha256'], 'observado_en': observado.isoformat(),
                   'familias': resultados, 'certificacion': 'NO_CERTIFICADO', 'modelo_activo': False})
