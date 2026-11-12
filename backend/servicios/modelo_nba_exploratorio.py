"""Selección personal independiente del singleton y de la campaña congelada."""
from hashlib import sha256
import json

from motor_autoentrenamiento.artefacto_nba import cargar_artefacto, ruta_artefacto
from motor_autoentrenamiento.gestor_modelo import ModeloEnMemoria


def directorio():
    return ruta_artefacto().parent / 'nba_exploratorio'


def cargar_seleccion():
    raiz = directorio().resolve()
    path = raiz / 'seleccion.json'
    if not path.is_file():
        raise ValueError('No hay candidato personal seleccionado; no se sustituye por 2123')
    seleccion = json.loads(path.read_text(encoding='utf-8'))
    artefacto = (raiz / seleccion['archivo']).resolve()
    if artefacto.parent != raiz or artefacto.suffix != '.npz':
        raise ValueError('Ruta del candidato fuera del directorio permitido')
    antes = sha256(artefacto.read_bytes()).hexdigest()
    if antes != seleccion['sha256']:
        raise ValueError('El candidato no coincide con la selección sellada')
    datos = cargar_artefacto(artefacto)
    if datos is None or datos['modelo_version_id'] != seleccion['modelo_version_id']:
        raise ValueError('Identidad del candidato incorrecta')
    if sha256(artefacto.read_bytes()).hexdigest() != antes:
        raise ValueError('El candidato cambió durante la lectura')
    modelo = ModeloEnMemoria(datos)
    modelo.metricas = {**modelo.metricas, 'alcance': 'PERSONAL_EXPLORATORIO', 'artefacto_sha256': antes}
    return modelo


def leer_revision():
    path = directorio() / 'ultima_revision.json'
    if not path.is_file():
        return {'estado': 'NO_VERIFICABLE', 'motivo': 'No hay recibo de revisión NBA acreditado'}
    return json.loads(path.read_text(encoding='utf-8'))


def estado_refresco(conn, modelo):
    from motor_autoentrenamiento.dominio_nba import FILTRO_NBA_ENTRENABLE
    from servicios.consulta_local import identidad_modelo
    identidad = identidad_modelo(modelo)
    corte = identidad['corte_modelo']
    row = conn.execute(f'''SELECT max(p.fecha_partido),count(*),
        count(*) FILTER(WHERE p.fecha_partido>%s) FROM partidos_baloncesto p
        WHERE {FILTRO_NBA_ENTRENABLE} AND COALESCE(p.tipo_partido,'REG')!='PRE' ''', (corte,)).fetchone()
    revision = leer_revision()
    return {'modelo': identidad, 'ultimo_final_valido_bd': row[0], 'finales_validos_bd': row[1],
            'finales_posteriores_al_modelo': row[2] if corte else None,
            'necesita_actualizacion': row[2] > 0 if corte else None,
            'revision_datos': revision, 'cobertura': 'Solo ventana del recibo; histórico no recertificado',
            'limite': 'Fecha máxima y agenda futura no acreditan cobertura ni calibración.'}
