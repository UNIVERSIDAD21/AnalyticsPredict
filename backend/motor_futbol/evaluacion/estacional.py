"""Candidatos Ridge de laboratorio: CAL por partidos anteriores, sin activar serving.

No reemplaza el protocolo V1 ni certifica datos retrospectivos. El receso no se
rellena con partidos: CAL retrocede como máximo 180 días y no divide instantes.
"""
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

from ..entrenamiento.dataset import CAMPOS, describir, seleccionar
from ..modelos.artefacto import sha256
from ..modelos.base import ajustar_ridge
from ..tipos import TipoModelo, normalizar_nombre_equipo
from .temporal_ridge import LIGAS, conocidos, matrices


@dataclass(frozen=True)
class PoliticaEstacional:
    version: str = 'estacional_sombra_v2'
    objetivo_cal: int = 200
    min_cal: int = 100
    min_train: int = 500
    min_partidos_equipo: int = 5
    max_dias_cal: int = 180
    alphas: tuple = (1.0, 5.0, 10.0)
    min_eval: int = 100
    min_ventanas_eval: int = 2
    cobertura_minima: float = 0.90
    max_antiguedad_target_dias: int = 60
    ventanas_eval: str = 'MESES_UTC'
    min_por_ventana: int = 30
    bootstrap_repeticiones: int = 1000
    semilla: int = 42

    def to_dict(self):
        return {**asdict(self), 'alphas': list(self.alphas)}

    def validar(self):
        # Los mínimos V1 se conservan; no son interruptores para aprobar un corte.
        if (self.min_cal < 100 or self.min_train < 500 or self.min_eval < 100
                or self.min_partidos_equipo < 5 or self.min_ventanas_eval < 2
                or self.objetivo_cal < self.min_cal or not 0.90 <= self.cobertura_minima <= 1
                or not 1 <= self.max_dias_cal <= 180
                or not 0 <= self.max_antiguedad_target_dias <= 60
                or self.ventanas_eval != 'MESES_UTC' or self.min_por_ventana < 30
                or self.bootstrap_repeticiones != 1000 or self.semilla != 42
                or self.alphas != (1.0, 5.0, 10.0)):
            raise ValueError('Política estacional fuera de los controles declarados')


def exigir_utc(valor):
    if not isinstance(valor, datetime) or valor.tzinfo is None:
        raise ValueError('Se requiere instante con zona horaria')
    return valor.astimezone(timezone.utc)


def preparar_candidato(partidos, tipo, corte, politica=None):
    """Ajusta solo con datos anteriores al corte; CAL elige alpha, nunca refit.

    Devuelve todos los coeficientes para reproducir la prueba aislada. Que pueda
    ajustarse NO significa que haya pasado gates de evaluación o de activación.
    """
    politica = politica or PoliticaEstacional()
    politica.validar()
    corte = exigir_utc(corte)
    tipo = TipoModelo(tipo)
    for p in partidos:
        exigir_utc(p['fecha_partido'])
    anteriores = [p for p in partidos if p.get('competicion_codigo') in LIGAS
                  and p['fecha_partido'] < corte]
    validos, excluidos = seleccionar(anteriores, tipo)
    recientes = [p for p in validos if p['fecha_partido'] >= corte-timedelta(days=politica.max_dias_cal)]
    # El corte se calcula por tiempo, nunca por resultado ni por equipo de EVAL.
    limite = recientes[-politica.objetivo_cal]['fecha_partido'] if len(recientes) >= politica.objetivo_cal else (
        recientes[0]['fecha_partido'] if recientes else corte)
    train, poda = seleccionar([p for p in validos if p['fecha_partido'] < limite],
                              tipo, politica.min_partidos_equipo)
    mapa = {n: i for i, n in enumerate(sorted({normalizar_nombre_equipo(p[k])
            for p in train for k in ('equipo_local', 'equipo_visitante')}))}
    cal_total = [p for p in recientes if p['fecha_partido'] >= limite]
    cal = conocidos(cal_total, mapa)
    conteos = Counter(normalizar_nombre_equipo(p[k]) for p in validos
                      if p['fecha_partido'] < limite for k in ('equipo_local', 'equipo_visitante'))
    desconocidos = sorted({normalizar_nombre_equipo(p[k]) for p in cal_total
                           for k in ('equipo_local', 'equipo_visitante') if normalizar_nombre_equipo(p[k]) not in mapa})
    resultado = {
        'version': politica.version, 'tipo': tipo.value, 'corte': corte.isoformat(),
        'politica': politica.to_dict(), 'politica_sha256': sha256(politica.to_dict()),
        'estado': 'SIN_CANDIDATO', 'motivos': [], 'certificacion': 'NO_CERTIFICADO',
        'activable': False, 'calibrador': None, 'disponibilidad_historica_acreditada': False,
        'train': describir(train, tipo, poda), 'cal': describir(cal, tipo),
        'n_cal_candidatos': len(cal_total), 'n_cal_equipo_desconocido': len(cal_total)-len(cal),
        'equipos_excluidos': [{'equipo': n, 'partidos_previos': conteos[n],
                               'motivo': 'SIN_MINIMO_O_PODA_TRAIN'} for n in desconocidos],
        'excluidos_datos': excluidos, 'targets': CAMPOS[tipo],
        'seleccion_alpha': [],
        'limites': ['Candidato para pruebas, no modelo activo.',
                    'CAL selecciona alpha; no calibra probabilidades.',
                    'La disponibilidad histórica no se deduce de la fecha del partido.'],
    }
    if len(train) < politica.min_train: resultado['motivos'].append('MUESTRA_TRAIN_INSUFICIENTE')
    if len(cal) < politica.min_cal: resultado['motivos'].append('MUESTRA_CAL_INSUFICIENTE')
    if not validos or (corte-validos[-1]['fecha_partido']).total_seconds() > politica.max_antiguedad_target_dias*86400:
        resultado['motivos'].append('TARGET_SIN_FRESCURA')
    if resultado['motivos']:
        return resultado
    x, y = matrices(train, tipo, mapa, doble=True)
    xc, yc = matrices(cal, tipo, mapa)
    mejor = None
    for alpha in politica.alphas:
        pesos, _ = ajustar_ridge(x, y, alpha)
        mae = float(np.mean(np.abs(xc @ pesos-yc)))
        resultado['seleccion_alpha'].append({'alpha': alpha, 'mae_cal': mae})
        if mejor is None or mae < mejor[0]: mejor = (mae, alpha, pesos)
    resultado.update(estado='CANDIDATO_SOMBRA', alpha=mejor[1], pesos=mejor[2].tolist(),
                     entidades=mapa, baseline=np.mean(matrices(train, tipo, mapa)[1], axis=0).tolist())
    resultado['artefacto_sha256'] = sha256({k: resultado[k] for k in ('tipo','pesos','entidades','alpha','train','cal','politica_sha256')})
    return resultado


def pronosticar_sombra(candidato, partidos, congelado_en, inicio_eval, fin_eval):
    """Predicciones puntuales futuras sin cuotas/picks; las abstenciones se cuentan.

    El llamador conserva candidato completo, datos y política antes de resultados.
    No se genera una probabilidad ficticia a partir del error de ajuste.
    """
    ahora, inicio, fin = map(exigir_utc, (congelado_en, inicio_eval, fin_eval))
    if not exigir_utc(datetime.fromisoformat(candidato['corte'])) < ahora < inicio < fin:
        raise ValueError('Orden obligatorio corte < congelamiento < inicio_eval < fin_eval')
    if candidato.get('fit_completed_at') and exigir_utc(datetime.fromisoformat(candidato['fit_completed_at'])) >= ahora:
        raise ValueError('El ajuste debe terminar antes del congelamiento')
    ids = [str(p['id']) for p in partidos]
    if len(ids) != len(set(ids)):
        raise ValueError('Partidos futuros duplicados')
    predicciones, abstenciones = [], []
    for p in sorted(partidos, key=lambda p: (p['fecha_partido'], str(p['id']))):
        fecha = exigir_utc(p['fecha_partido'])
        if not inicio <= fecha < fin:
            continue
        motivo = None
        if candidato['estado'] != 'CANDIDATO_SOMBRA': motivo = 'SIN_CANDIDATO'
        elif p.get('competicion_codigo') not in LIGAS: motivo = 'FUERA_DE_LIGAS'
        elif p.get('estado') != 'PROGRAMADO': motivo = 'NO_PROGRAMADO'
        elif not conocidos([p], candidato['entidades']): motivo = 'EQUIPO_FUERA_TRAIN'
        elif normalizar_nombre_equipo(p['equipo_local']) == normalizar_nombre_equipo(p['equipo_visitante']): motivo = 'MISMO_EQUIPO'
        if motivo:
            abstenciones.append({'partido_id': str(p['id']), 'motivo': motivo})
            continue
        # Construcción solo de features: nunca leer outcomes de los fixtures.
        from ..modelos.base import construir_matriz_diseno
        x = construir_matriz_diseno([p['equipo_local']], [p['equipo_visitante']], [1], candidato['entidades'])
        valores = (x @ np.asarray(candidato['pesos']))[0].tolist()
        predicciones.append({'partido_id': str(p['id']), 'inicio_utc': fecha.isoformat(),
            'equipo_local': p['equipo_local'], 'equipo_visitante': p['equipo_visitante'],
            'features': x[0].tolist(), 'prediccion_sin_recorte': dict(zip(candidato['targets'], valores)),
            'baseline': dict(zip(candidato['targets'], candidato['baseline'])),
            'artefacto_sha256': candidato['artefacto_sha256'], 'congelado_en': ahora.isoformat(),
            'p_raw': None, 'p_calibrada': None, 'activable': False})
    return {'predicciones': predicciones, 'abstenciones': abstenciones, 'estado': 'SOMBRA_NO_ACTIVA'}
