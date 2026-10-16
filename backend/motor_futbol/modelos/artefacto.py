"""Contrato JSON verificable de Ridge fútbol. No usa pickle ni rutas de BD."""
from datetime import datetime
import hashlib
import json
import math

import numpy as np

from ..tipos import TipoModelo, normalizar_nombre_equipo


def sha256(payload):
    contenido = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(contenido.encode()).hexdigest()


def exportar(modelo):
    if not modelo.entrenado:
        raise ValueError('No se puede persistir un modelo sin entrenar')
    payload = {
        'formato': 1, 'dominio': 'FUTBOL',
        'features': 'intercepto_equipo_rival_local_v1',
        'tipo': modelo.tipo.value, 'targets': list(modelo.targets),
        'alfa': modelo.alfa, 'entidad_a_indice': modelo.entidad_a_indice,
        'pesos': {k: v.tolist() for k, v in modelo.pesos.items()},
        'std_residuales': modelo.std_residuales,
        'fecha_entrenamiento': modelo.fecha_entrenamiento.isoformat() if modelo.fecha_entrenamiento else None,
        'metricas': modelo.metricas, 'dataset': getattr(modelo, 'dataset', {}),
        'calibrador': None, 'certificacion': 'NO_CERTIFICADO',
    }
    cargar(payload)  # Misma validación al publicar y servir.
    return payload


def cargar(payload):
    from .corners import ModeloCorners
    from .goles import ModeloGoles
    from .disparos import ModeloDisparos

    if not isinstance(payload, dict):
        raise ValueError('El artefacto debe ser un objeto JSON')
    if payload.get('formato') != 1 or payload.get('dominio') != 'FUTBOL' or payload.get('features') != 'intercepto_equipo_rival_local_v1':
        raise ValueError('Contrato de artefacto fútbol no soportado')
    if payload.get('calibrador') is not None or payload.get('certificacion') != 'NO_CERTIFICADO':
        raise ValueError('Este artefacto raw no acredita calibración ni certificación')
    modelo = {TipoModelo.CORNERS: ModeloCorners, TipoModelo.GOLES: ModeloGoles, TipoModelo.DISPAROS: ModeloDisparos}[TipoModelo(payload['tipo'])]()
    if payload['targets'] != modelo.targets:
        raise ValueError('Targets incompletos o incompatibles')
    entidades = payload['entidad_a_indice']
    if not isinstance(entidades, dict) or not entidades or any(not isinstance(k, str) or not k or normalizar_nombre_equipo(k) != k or type(v) is not int for k, v in entidades.items()) or sorted(entidades.values()) != list(range(len(entidades))):
        raise ValueError('Índices de equipos incompatibles')
    if any(not isinstance(payload[k], dict) for k in ('pesos', 'std_residuales', 'dataset', 'metricas')):
        raise ValueError('Coeficientes y metadatos deben ser objetos JSON')
    if set(payload['pesos']) != set(modelo.targets) or set(payload['std_residuales']) != set(modelo.targets):
        raise ValueError('Faltan coeficientes o residuales por target')
    modelo.alfa = float(payload['alfa'])
    if not math.isfinite(modelo.alfa) or modelo.alfa <= 0:
        raise ValueError('Alpha inválido')
    modelo.entidad_a_indice = dict(entidades)
    for target in modelo.targets:
        pesos = np.asarray(payload['pesos'][target], dtype=float)
        std = float(payload['std_residuales'][target])
        if pesos.shape != (2+2*len(entidades),) or not np.isfinite(pesos).all() or not math.isfinite(std) or std < 0:
            raise ValueError('Dimensión o valores de coeficientes/residuales inválidos')
        modelo.pesos[target] = pesos
        modelo.std_residuales[target] = std
    modelo.fecha_entrenamiento = datetime.fromisoformat(payload['fecha_entrenamiento'])
    modelo.metricas = dict(payload['metricas'])
    modelo.dataset = dict(payload['dataset'])
    d = modelo.dataset
    if d.get('politica') != 'final_valido_targets_completos_coherentes_v1' or type(d.get('n_partidos')) is not int or d['n_partidos'] <= 0:
        raise ValueError('Dataset efectivo no acreditado')
    if d.get('n_filas_diseno') != 2*d['n_partidos'] or d.get('equipos') != modelo.obtener_equipos():
        raise ValueError('Dataset y diseño incompatibles')
    huella = d.get('hash_sha256', '')
    if len(huella) != 64 or any(c not in '0123456789abcdef' for c in huella):
        raise ValueError('Hash de dataset inválido')
    minimo, maximo = (datetime.fromisoformat(d[k]) for k in ('fecha_min', 'fecha_max'))
    if any(f.tzinfo is None for f in (minimo, maximo, modelo.fecha_entrenamiento)) or not minimo <= maximo < modelo.fecha_entrenamiento:
        raise ValueError('Fechas de dataset/ajuste no acreditadas')
    # También rechaza NaN/Infinity en metadatos anidados.
    sha256(payload)
    modelo._entrenado = True
    return modelo


def cargar_registro(registro):
    metadata = registro.get('metadata') or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    if not isinstance(metadata, dict):
        raise ValueError('Metadata de modelo inválida')
    payload = metadata.get('artefacto')
    if not payload or metadata.get('artefacto_sha256') != sha256(payload):
        raise ValueError('Versión sin artefacto íntegro; el registro de métricas no es un modelo')
    modelo = cargar(payload)
    mercado = {'corners': 'CORNERS_FT', 'goles': 'GOLES_FT', 'disparos': 'DISPAROS_FT'}[modelo.tipo.value]
    if registro['mercado_principal'] != mercado or registro['hash_datos'] != modelo.dataset.get('hash_sha256', '')[:32]:
        raise ValueError('Registro y artefacto no corresponden al mismo dataset/familia')
    if registro['partidos_entrenamiento'] != modelo.dataset.get('n_partidos') or registro['equipos'] != modelo.cantidad_equipos:
        raise ValueError('Registro y artefacto tienen conteos diferentes')
    if registro['fecha_entrenamiento'] != modelo.fecha_entrenamiento:
        raise ValueError('Registro y artefacto tienen fechas de ajuste diferentes')
    modelo.version_id = registro['id']
    return modelo
