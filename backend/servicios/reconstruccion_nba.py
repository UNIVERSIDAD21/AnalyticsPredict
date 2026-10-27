"""Refit NBA efímero al corte. Sin publicar pesos/versiones ni registrar consultas."""
from collections import Counter
from hashlib import sha256
import json

import numpy as np

from db import obtener_pool
from lecturas_http import solo_lectura_http
from motor import analizar_partido, resultado_a_dict
from motor.tipos import Ubicacion
from motor_autoentrenamiento import EntrenadorBD, ModeloEnMemoria
from motor_autoentrenamiento.entrenador_bd import ajustar_ridge, construir_matriz_diseno, normalizar_nombre, ALPHA_RIDGE


def reconstruir(peticion, fixture, marcadores=(None, None, None)):
    token = solo_lectura_http.set(True)
    try:
        return _reconstruir(peticion, fixture, marcadores)
    finally:
        solo_lectura_http.reset(token)


def _reconstruir(peticion, fixture, marcadores):
    corte = fixture['fecha_partido']
    filas = EntrenadorBD(obtener_pool())._obtener_partidos(
        temporadas=peticion.temporadas, cutoff_fecha=corte)
    # Defensa adicional: ni un dato del mismo día o posterior cruza el corte.
    filas = [r for r in filas if r['fecha_partido'] < corte]
    muestras = Counter(normalizar_nombre(r[l]) for r in filas for l in ('equipo_local','equipo_visitante'))
    local, visitante = fixture['local'], fixture['visitante']
    if len(filas) < 100 or any(muestras[normalizar_nombre(n)] < 6 for n in (local, visitante)):
        raise ValueError('Muestra NBA anterior al corte insuficiente: se requieren 100 finales y 6 por equipo')
    indices = {n: i for i,n in enumerate(sorted(muestras))}
    equipos, rivales, localias, ye, yr = [], [], [], [], []
    for r in filas:
        h = [r[f'local_q{i}'] for i in range(1,5)]
        a = [r[f'visitante_q{i}'] for i in range(1,5)]
        equipos.extend((r['equipo_local'], r['equipo_visitante']))
        rivales.extend((r['equipo_visitante'], r['equipo_local']))
        localias.extend((1,0)); ye.extend((h,a)); yr.extend((a,h))
    x = construir_matriz_diseno(equipos, rivales, localias, indices)
    we, se = ajustar_ridge(x, np.array(ye), ALPHA_RIDGE)
    wr, sr = ajustar_ridge(x, np.array(yr), ALPHA_RIDGE)
    modelo = ModeloEnMemoria({'alpha': ALPHA_RIDGE, 'entidad_a_indice': indices,
        'pesos_equipo': we, 'pesos_rival': wr, 'desviacion_equipo': se, 'desviacion_rival': sr}, version=0)
    resultado = analizar_partido(modelo=modelo, equipo=local, rival=visitante,
        ubicacion=Ubicacion.LOCAL, mercado=peticion.mercado, linea=peticion.linea,
        lado=peticion.lado, fecha_partido=corte, incluir_contexto=False, solo_historico=True,
        marcador_q1=marcadores[0], marcador_q2=marcadores[1], marcador_q3=marcadores[2])
    resultado.candidatos = []; resultado.mejor_apuesta = None
    datos = resultado_a_dict(resultado)
    huella = sha256(json.dumps(filas, default=str, sort_keys=True).encode()).hexdigest()
    datos.setdefault('metadata', {}).update({
        'modo_analisis': 'HISTORICO_RECONSTRUIDO', 'solo_consulta': True,
        'partido_id': str(fixture['id']), 'fecha_partido': corte.isoformat(),
        'corte_exclusivo': corte.isoformat(), 'partidos_entrenamiento': len(filas),
        'ultimo_dato_utilizado': max(r['fecha_partido'] for r in filas).isoformat(),
        'dataset_sha256': huella, 'modelo_version': None,
        'calibracion': 'SIN_CALIBRAR', 'incluye_ot': False,
        'muestras': {'local': muestras[normalizar_nombre(local)], 'visitante': muestras[normalizar_nombre(visitante)]},
    })
    return datos
