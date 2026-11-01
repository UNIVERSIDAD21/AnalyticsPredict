"""Matriz de contratos WNBA sin red, BD, journals ni publicación de modelos.

Ajusta alcances solo en memoria. Comprueba funcionamiento, no eficacia predictiva.
Los parciales de los cortes son entradas de prueba, nunca resultados oficiales.
"""
from collections import Counter
from datetime import date
from itertools import permutations
import math
import time

import numpy as np

from motor.wnba import ajustar_alcance, conocido, huella
from motor.wnba_ampliado import POLITICA_MUESTRAS, POTENCIA, ajustar_ot, predecir_ampliado

PARCIALES = [[19, 21], [20, 18], [17, 22]]


def _comprobar(resultado, parciales):
    def exigir(condicion, mensaje):
        if not condicion:
            raise AssertionError(mensaje)

    def distribucion(valores, campo):
        exigir(all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in valores.values()), f"{campo}: probabilidad fuera de rango")
        exigir(abs(sum(valores.values()) - 1) < 1e-12, f"{campo}: probabilidades no suman 1")

    distribucion(resultado['probabilidades'], 'objetivo Q4')
    predicciones = resultado['predicciones']
    for q in range(1, 5):
        p = predicciones[f'Q{q}']
        exigir(all(math.isfinite(p[k]) and p[k] >= 0 for k in ('media_local', 'media_visitante', 'media_total', 'varianza_total')), 'Proyección no finita/negativa')
        exigir(abs(p['media_local'] + p['media_visitante'] - p['media_total']) < 1e-10, 'Total de cuarto no concilia')
        distribucion(p['ganador'], f'ganador Q{q}')
        if q <= len(parciales):
            exigir(p['observado'] and p['media_local'] == parciales[q-1][0] and p['media_visitante'] == parciales[q-1][1] and p['varianza_total'] == 0, 'Cuarto observado se volvió a pronosticar')
        else:
            exigir(not p['observado'], 'Cuarto futuro marcado observado')
    regulacion = resultado['regulacion']
    exigir(abs(sum(predicciones[f'Q{q}']['media_total'] for q in range(1, 5)) - regulacion['media_total']) < 1e-10, 'Regulación no coincide con suma de cuartos')
    if parciales:
        exigir(not resultado['incluye_ot'] and predicciones['COMPLETO'] == regulacion, 'Corte incorpora OT o altera regulación')
    elif 'COMPLETO' in predicciones:
        exigir(predicciones['COMPLETO']['media_total'] >= regulacion['media_total'], 'OT reduce marcador')
        exigir(predicciones['COMPLETO']['ganador']['empate'] == 0, 'Empate después de OT')
    else:
        exigir(set(resultado['mercados_no_disponibles']) == {'COMPLETO'}, 'Muestra OT bloqueó cuartos')
    total_lineas = 0
    for mercado, lineas in resultado['evaluacion_lineas'].items():
        for linea, probs in lineas.items():
            distribucion(probs, f'{mercado}/{linea}')
            if not float(linea).is_integer():
                exigir(probs['push'] == 0, 'Push en media línea')
            if float(linea) == 0:
                exigir(probs['under'] == 0, 'Puntos negativos con probabilidad positiva')
            total_lineas += 1
    return total_lineas


def auditar(datos, *, corte, potencia=POTENCIA, progreso=None):
    date.fromisoformat(corte)
    if not isinstance(potencia, int) or not 5 <= potencia <= POTENCIA:
        raise ValueError('Integración entre 2^5 y 2^15; usar 2^15 para verificar serving')
    if len({r['id'] for r in datos}) != len(datos):
        raise ValueError('Dataset con IDs duplicados')
    datos = sorted((r for r in datos if r['fecha'] < corte), key=lambda r: (r['inicio_utc'], r['id']))
    if not datos:
        raise ValueError('Sin datos anteriores al corte')
    catalogo = {r[k]: r[n] for r in datos for k, n in (('local_id', 'local'), ('visitante_id', 'visitante'))}
    original = huella(datos)
    alcances = []
    incidencias = []
    inicio = time.monotonic()
    for temporada in sorted({r['temporada'] for r in datos}):
        rows = [r for r in datos if r['temporada'] == temporada and r['fase'] == 'REG']
        entrada = {'temporada': temporada, 'partidos': len(rows), 'parejas_catalogo': len(catalogo)*(len(catalogo)-1), 'parejas_con_soporte': 0, 'parejas_abstencion': 0, 'modos_verificados': 0, 'distribuciones_verificadas': 0, 'total_pre_con_ot_disponible': None, 'motivos_abstencion': {}, 'fallos': 0}
        try:
            modelo = ajustar_alcance(rows)
        except ValueError as exc:
            entrada.update(estado='ALCANCE_SIN_SOPORTE', motivo=str(exc))
            alcances.append(entrada)
            continue
        ot = ajustar_ot(rows)
        entrada.update(ot_n=ot['n'], total_pre_con_ot_disponible=ot['n'] >= ot['minimo'])
        motivos = Counter()
        modelo_hash = huella(modelo)
        for local, visita in permutations(sorted(catalogo), 2):
            if not conocido(modelo, {'local_id': local, 'visitante_id': visita}):
                entrada['parejas_abstencion'] += 1
                try:
                    predecir_ampliado(modelo, local, visita, 'Q4', 40.5, [], ot, potencia=potencia)
                except ValueError:
                    motivos['Equipo ausente o muestra insuficiente en esta temporada'] += 1
                else:
                    incidencias.append({'temporada': temporada, 'local': catalogo[local], 'visitante': catalogo[visita], 'modo': 'PREPARTIDO', 'error': 'No se abstuvo ante equipo sin soporte'})
                    entrada['fallos'] += 1
                continue
            entrada['parejas_con_soporte'] += 1
            for n in range(4):
                parciales = [list(q) for q in PARCIALES[:n]]
                modo = 'PREPARTIDO' if n == 0 else f'CIERRE_Q{n}'
                lineas = {**{f'Q{q}': [0, 40, 40.5] for q in range(n+1, 5)}, 'COMPLETO': [0, 160, 160.5]}
                try:
                    result = predecir_ampliado(modelo, local, visita, 'Q4', 40.5, parciales, ot, potencia=potencia, lineas=lineas)
                    entrada['distribuciones_verificadas'] += _comprobar(result, parciales)
                    entrada['modos_verificados'] += 1
                except (ValueError, AssertionError, KeyError, TypeError, FloatingPointError, np.linalg.LinAlgError) as exc:
                    entrada['fallos'] += 1
                    incidencias.append({'temporada': temporada, 'local': catalogo[local], 'visitante': catalogo[visita], 'modo': modo, 'error': f'{type(exc).__name__}: {exc}'})
        if huella(modelo) != modelo_hash:
            entrada['fallos'] += 1
            incidencias.append({'temporada': temporada, 'error': 'Modelo mutado al predecir'})
        entrada.update(estado='VERIFICADO' if not entrada['fallos'] else 'CON_FALLOS', motivos_abstencion=dict(motivos))
        alcances.append(entrada)
        if progreso:
            progreso(entrada)
    if huella(datos) != original:
        incidencias.append({'error': 'Dataset mutado durante la auditoría'})
    casos = sum(x['modos_verificados'] for x in alcances)
    estado = 'CON_FALLOS' if incidencias else 'VERIFICADO' if casos else 'SIN_CASOS_VERIFICABLES'
    return {'estado': estado, 'corte_exclusivo': corte, 'politica_muestras': POLITICA_MUESTRAS, 'dataset_sha256': original, 'registros_previos': len(datos), 'equipos_catalogo': len(catalogo), 'simulaciones_por_modo': 2**potencia, 'serving_exacto': potencia == POTENCIA, 'alcances': alcances, 'fallos': incidencias, 'casos_con_soporte': casos, 'distribuciones_verificadas': sum(x['distribuciones_verificadas'] for x in alcances), 'duracion_segundos': round(time.monotonic()-inicio, 3), 'limites': ['Solo REG y temporadas individuales; no todas sus combinaciones.', 'Parciales sintéticos controlados: no son marcadores oficiales ni prueba de eficacia.', 'No escribe BD, journals ni publica modelos. Ajustes de temporada solo en memoria.', 'No valida calibración ni disponibilidad histórica original de la información.']}
