"""Walk-forward retrospectivo Ridge por evento, sin apuestas ni escritura de BD.

Los resultados no acreditan cuándo estuvo disponible el histórico en su proveedor.
CAL selecciona alpha; NO es un calibrador de probabilidades. EVAL nunca selecciona.
"""
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
import json
import math

import numpy as np

from ..entrenamiento.dataset import CAMPOS, describir, seleccionar
from ..modelos.artefacto import sha256
from ..modelos.base import ajustar_ridge, construir_matriz_diseno
from ..tipos import TipoModelo, normalizar_nombre_equipo

LIGAS = ('ENG_PREMIER', 'ESP_LALIGA', 'ITA_SERIEA', 'GER_BUNDESLIGA', 'FRA_LIGUE1')


@dataclass(frozen=True)
class Ventana:
    nombre: str
    inicio_cal: date
    inicio_eval: date
    fin_eval: date


VENTANAS = (
    Ventana('2026-01', date(2025, 10, 1), date(2026, 1, 1), date(2026, 2, 1)),
    Ventana('2026-02', date(2025, 11, 1), date(2026, 2, 1), date(2026, 3, 1)),
    Ventana('2026-03', date(2025, 12, 1), date(2026, 3, 1), date(2026, 4, 1)),
    Ventana('2026-09', date(2026, 6, 1), date(2026, 9, 1), date(2026, 10, 1)),
    Ventana('2026-10', date(2026, 7, 1), date(2026, 10, 1), date(2026, 10, 16)),
)


@dataclass(frozen=True)
class PoliticaTemporal:
    desde: date = date(2023, 7, 1)
    ventanas: tuple[Ventana, ...] = VENTANAS
    ligas: tuple[str, ...] = LIGAS
    alphas: tuple[float, ...] = (1.0, 5.0, 10.0)
    min_train: int = 500
    min_cal: int = 100
    min_eval: int = 30
    min_partidos_equipo: int = 5
    bootstrap_repeticiones: int = 1000
    semilla: int = 42
    min_eval_activacion: int = 100
    min_ventanas_activacion: int = 2
    cobertura_activacion: float = 0.90
    max_antiguedad_dias: int = 60

    def validar(self):
        if not self.ventanas or not self.alphas or any(not math.isfinite(a) or a <= 0 for a in self.alphas):
            raise ValueError('Ventanas y alphas positivos finitos son obligatorios')
        if any(n < 1 for n in (self.min_train, self.min_cal, self.min_eval, self.min_partidos_equipo,
                               self.bootstrap_repeticiones, self.min_eval_activacion, self.min_ventanas_activacion)):
            raise ValueError('Los mínimos deben ser positivos')
        if not 0 < self.cobertura_activacion <= 1 or self.max_antiguedad_dias < 0:
            raise ValueError('Gate de cobertura/antigüedad inválido')
        anterior = None
        for v in self.ventanas:
            if not self.desde < v.inicio_cal < v.inicio_eval < v.fin_eval:
                raise ValueError('Orden train < CAL < EVAL inválido')
            if anterior and v.inicio_eval < anterior:
                raise ValueError('Las ventanas EVAL no pueden solaparse ni desordenarse')
            anterior = v.fin_eval

    def to_dict(self):
        return json.loads(json.dumps(asdict(self), default=str))


def medianoche(dia):
    return datetime.combine(dia, time.min, tzinfo=timezone.utc)


def particionar(partidos, ventana, desde):
    """Cada ID aparece una sola vez; las dos perspectivas se construyen después."""
    a, b, c, d = map(medianoche, (desde, ventana.inicio_cal, ventana.inicio_eval, ventana.fin_eval))
    return ([p for p in partidos if a <= p['fecha_partido'] < b],
            [p for p in partidos if b <= p['fecha_partido'] < c],
            [p for p in partidos if c <= p['fecha_partido'] < d])


def conocidos(partidos, mapa):
    return [p for p in partidos if all(normalizar_nombre_equipo(p[k]) in mapa for k in ('equipo_local', 'equipo_visitante'))]


def matrices(partidos, tipo, mapa, doble=False):
    if len(conocidos(partidos, mapa)) != len(partidos):
        raise ValueError('Equipo fuera del train: no usar vector vacío')
    locales = [p['equipo_local'] for p in partidos]
    visitantes = [p['equipo_visitante'] for p in partidos]
    X = construir_matriz_diseno(locales, visitantes, [1]*len(partidos), mapa)
    Y = np.asarray([[p[k] for k in CAMPOS[tipo]] for p in partidos], dtype=float).reshape(-1, 4)
    if doble:
        X = np.vstack((X, construir_matriz_diseno(visitantes, locales, [0]*len(partidos), mapa)))
        Y = np.vstack((Y, Y[:, [2, 3, 0, 1]]))
    return X, Y


def metricas(filas, repeticiones=1000, semilla=42, targets=None):
    """Intervalo pareado con unidad partido; los cuatro targets no inflan n."""
    if not filas:
        return {'n_partidos': 0, 'mae': None, 'rmse': None, 'mae_baseline': None,
                'rmse_baseline': None, 'delta_mae': None, 'ic95_delta_mae': None, 'por_target': {}}
    real, pred, base = (np.asarray([f[k] for f in filas], dtype=float) for k in ('real', 'prediccion', 'baseline'))
    errores, eb = pred-real, base-real
    diferencia = np.mean(np.abs(errores)-np.abs(eb), axis=1)
    rng = np.random.default_rng(semilla)
    medias = [float(np.mean(rng.choice(diferencia, size=len(filas), replace=True))) for _ in range(repeticiones)]
    return {
        'n_partidos': len(filas), 'mae': float(np.mean(np.abs(errores))),
        'rmse': float(np.sqrt(np.mean(errores**2))),
        'mae_baseline': float(np.mean(np.abs(eb))), 'rmse_baseline': float(np.sqrt(np.mean(eb**2))),
        'delta_mae': float(np.mean(diferencia)),
        'ic95_delta_mae': [float(x) for x in np.quantile(medias, [0.025, 0.975])],
        'bootstrap': {'unidad': 'PARTIDO', 'repeticiones': repeticiones, 'semilla': semilla,
                      'limite': 'No modela toda la dependencia temporal/equipo entre partidos'},
        'por_target': {(targets[i] if targets else str(i)): {'mae': float(np.mean(np.abs(errores[:, i]))),
                               'mae_baseline': float(np.mean(np.abs(eb[:, i]))),
                               'rmse': float(np.sqrt(np.mean(errores[:, i]**2)))} for i in range(4)},
    }


def evaluar_ventana(partidos, tipo, ventana, politica):
    train, cal_total, eval_total = particionar(partidos, ventana, politica.desde)
    train, exclusiones = seleccionar(train, tipo, politica.min_partidos_equipo)
    mapa = {n: i for i, n in enumerate(sorted({normalizar_nombre_equipo(p[k]) for p in train for k in ('equipo_local', 'equipo_visitante')}))}
    cal, evaluacion = conocidos(cal_total, mapa), conocidos(eval_total, mapa)
    reporte = {
        'ventana': ventana.nombre, 'limites': json.loads(json.dumps(asdict(ventana), default=str)),
        'train': describir(train, tipo, exclusiones), 'cal': describir(cal, tipo),
        'eval': describir(evaluacion, tipo), 'n_cal_candidatos': len(cal_total),
        'n_eval_candidatos': len(eval_total), 'cal_equipo_desconocido': len(cal_total)-len(cal),
        'eval_equipo_desconocido': len(eval_total)-len(evaluacion),
        'cobertura_eval': len(evaluacion)/len(eval_total) if eval_total else None,
        'estado': 'SIN_EVALUACION', 'motivo': None, 'seleccion_alpha': [],
        'alpha': None, 'filas_eval': [], 'metricas': metricas([]),
    }
    for nombre, filas, minimo in [('TRAIN', train, politica.min_train), ('CAL', cal, politica.min_cal), ('EVAL', evaluacion, politica.min_eval)]:
        if len(filas) < minimo:
            reporte['motivo'] = 'MUESTRA_' + nombre + '_INSUFICIENTE'
            return reporte
    X, Y = matrices(train, tipo, mapa, doble=True)
    Xcal, Ycal = matrices(cal, tipo, mapa)
    Xeval, Yeval = matrices(evaluacion, tipo, mapa)
    baseline = np.mean(matrices(train, tipo, mapa)[1], axis=0)
    mejor, mejor_mae, pesos_elegidos = None, float('inf'), None
    for alpha in sorted(set(politica.alphas)):
        pesos, _ = ajustar_ridge(X, Y, alpha)
        error = float(np.mean(np.abs(Xcal @ pesos-Ycal)))
        reporte['seleccion_alpha'].append({'alpha': alpha, 'mae_cal': error})
        if error < mejor_mae:
            mejor, mejor_mae, pesos_elegidos = alpha, error, pesos
    pred = Xeval @ pesos_elegidos
    reporte['alpha'] = mejor
    reporte['coeficientes_sha256'] = sha256({'entidades': mapa, 'pesos': pesos_elegidos.tolist()})
    reporte['filas_eval'] = [
        {'partido_id': str(p['id']), 'fecha': p['fecha_partido'].isoformat(),
         'real': Yeval[i].tolist(), 'prediccion': pred[i].tolist(), 'baseline': baseline.tolist()}
        for i, p in enumerate(evaluacion)]
    reporte['metricas'] = metricas(reporte['filas_eval'], politica.bootstrap_repeticiones, politica.semilla, CAMPOS[tipo])
    reporte['estado'], reporte['motivo'] = 'EVALUADO_RETROSPECTIVO', None
    return reporte


def evaluar(partidos, politica=None):
    politica = politica or PoliticaTemporal()
    politica.validar()
    for p in partidos:
        if not isinstance(p.get('fecha_partido'), datetime) or p['fecha_partido'].tzinfo is None:
            raise ValueError('La evaluación requiere fechas completas con zona horaria')
    acotados = [p for p in partidos if p.get('competicion_codigo') in politica.ligas]
    informe = {
        'ambito': 'WALK_FORWARD_RETROSPECTIVO_NO_PROSPECTIVO', 'certificacion': 'NO_CERTIFICADO',
        'politica': politica.to_dict(), 'politica_sha256': sha256(politica.to_dict()),
        'baseline': 'Media por target en TRAIN original, perspectiva local, misma cohorte EVAL',
        'seleccion_alpha': 'Solo CAL; sin refit CAL y sin optimización con EVAL',
        'calibrador_probabilidades': None, 'disponibilidad_historica_acreditada': False,
        'policy': {'no_picks': True, 'no_stake': True, 'no_betting_recommendations': True},
        'familias': {},
    }
    for tipo in TipoModelo:
        validos, exclusiones = seleccionar(acotados, tipo)
        ventanas = [evaluar_ventana(validos, tipo, v, politica) for v in politica.ventanas]
        filas = [f for v in ventanas for f in v['filas_eval']]
        if len({f['partido_id'] for f in filas}) != len(filas):
            raise ValueError('Un partido fue contado más de una vez en EVAL')
        m = metricas(filas, politica.bootstrap_repeticiones, politica.semilla, CAMPOS[tipo])
        candidatos = sum(v['n_eval_candidatos'] for v in ventanas)
        cobertura = len(filas)/candidatos if candidatos else None
        ultima = max((f['fecha'] for f in filas), default=None)
        motivos = []
        if m['n_partidos'] < politica.min_eval_activacion: motivos.append('MASA_EVAL_INSUFICIENTE')
        if sum(v['estado'] == 'EVALUADO_RETROSPECTIVO' for v in ventanas) < politica.min_ventanas_activacion: motivos.append('POCAS_VENTANAS')
        if cobertura is None or cobertura < politica.cobertura_activacion: motivos.append('COBERTURA_INSUFICIENTE')
        if ultima is None or (politica.ventanas[-1].fin_eval-datetime.fromisoformat(ultima).date()).days > politica.max_antiguedad_dias: motivos.append('TARGET_SIN_FRESCURA')
        if m['ic95_delta_mae'] is None or m['ic95_delta_mae'][1] >= 0: motivos.append('MEJORA_BASELINE_NO_ACREDITADA')
        if any(x['mae'] > x['mae_baseline'] for x in m['por_target'].values()): motivos.append('TARGET_PEOR_QUE_BASELINE')
        informe['familias'][tipo.value] = {
            'dataset': describir(validos, tipo, exclusiones), 'ventanas': ventanas, 'resumen': m,
            'cobertura_eval_total': cobertura, 'ultimo_eval': ultima,
            'gate_activacion_exploratoria': {'apto': not motivos, 'motivos': motivos,
                'no_es_promocion_beta_ni_certificacion': True},
        }
    return informe
