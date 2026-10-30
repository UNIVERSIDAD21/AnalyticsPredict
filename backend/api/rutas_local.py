"""Superficie local acotada y ajena a las escrituras del análisis estándar."""
from typing import Literal
from datetime import datetime, timezone
import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from motor_autoentrenamiento import obtener_modelo
from servicios.consulta_local import consultar, identidad_modelo

router = APIRouter(prefix="/api/local", tags=["Consulta base local"])


@router.get('/estado')
def estado_local():
    """Diagnóstico del proceso y artefactos; nunca comprueba la conexión SQL."""
    from servicios.consulta_local_ligas import catalogo as catalogo_congelado
    modelos = {}
    try:
        m = modelo_local()
        modelos['nba'] = {'disponible': True, 'equipos_disponibles': len(m.obtener_equipos()),
                          **identidad_modelo(m)}
    except HTTPException:
        modelos['nba'] = {'disponible': False, 'motivo': 'Artefacto ausente o no cargado'}
    for liga in ('euroliga', 'wnba'):
        try:
            c = catalogo_congelado(cargar_liga(liga), liga)
            modelos[liga] = {'disponible': True,
                'equipos_disponibles': sum(e['disponible'] for e in c['equipos']), **c['metadata']}
        except (HTTPException, KeyError, TypeError, ValueError):
            modelos[liga] = {'disponible': False, 'motivo': 'Artefacto ausente o no íntegro'}
    deshabilitada = os.getenv('ANALYTICSPREDICT_SOLO_BASE_LOCAL') == '1'
    return {'formato': 'diagnostico-local-v1', 'observado_en': datetime.now(timezone.utc).isoformat(),
        'modo': 'BASE_LOCAL' if deshabilitada else 'CON_BD_CONFIGURADA',
        'bd': {'deshabilitada': deshabilitada, 'conexion_comprobada': False,
               'estado': 'DESHABILITADA_POR_MODO' if deshabilitada else 'NO_COMPROBADA'},
        'modelos': modelos, 'fuente': 'proceso_y_artefactos_locales',
        'capacidades': {'consulta_base': True, 'cuaderno': 'almacen_del_navegador',
                        'agendas_y_contexto': 'requiere_BD', 'futbol_sin_BD': False},
        'limites': ['No verifica datos deportivos actuales ni conectividad SQL.',
                    'No acredita migración, calibración ni rendimiento predictivo.',
                    'No incluye credenciales, rutas privadas ni contenido del cuaderno.']}


@router.get('/cobertura')
def cobertura_registrada(dias: int = Query(default=365, ge=1, le=1095)):
    """Lectura explícita de BD; no la ejecuta el inventario de artefactos."""
    from db import obtener_pool
    from servicios.cobertura_uso import leer_cobertura
    try:
        with obtener_pool().connection() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            return leer_cobertura(conn, dias)
    except Exception as exc:
        raise HTTPException(503, detail={'estado': 'COBERTURA_NO_DISPONIBLE',
            'mensaje': 'Cobertura de BD N/D. No se descargaron fuentes ni se actualizaron datos.'}) from exc


class PeticionLocal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equipo_local: str = Field(min_length=1, max_length=100)
    equipo_visitante: str = Field(min_length=1, max_length=100)
    periodo: Literal["Q1", "Q2", "Q3", "Q4", "TOTAL"] = "TOTAL"
    linea: float = Field(gt=0, lt=1000, allow_inf_nan=False)


def modelo_local():
    try:
        return obtener_modelo()
    except RuntimeError as exc:
        raise HTTPException(503, "Artefacto NBA local no disponible; no se intenta entrenar ni conectar a la BD") from exc


@router.get("/nba/catalogo")
def catalogo():
    modelo = modelo_local()
    return {"equipos": sorted(modelo.obtener_equipos()), "metadata": identidad_modelo(modelo)}


@router.post("/nba/consultar")
def consulta(peticion: PeticionLocal):
    try:
        return consultar(modelo_local(), peticion.equipo_local, peticion.equipo_visitante,
                         peticion.periodo, peticion.linea)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def cargar_liga(liga):
    try:
        if liga == "euroliga":
            from motor.euroliga import cargar
        else:
            from servicios.predictor_wnba import cargar
        return cargar()
    except (RuntimeError, ValueError, OSError, KeyError) as exc:
        raise HTTPException(503, f"Artefacto {liga} no disponible o no íntegro; no se entrena ni se usa otra liga") from exc


@router.get("/{liga}/catalogo")
def catalogo_liga(liga: Literal["euroliga", "wnba"]):
    from servicios.consulta_local_ligas import catalogo
    return catalogo(cargar_liga(liga), liga)


@router.post("/{liga}/consultar")
def consulta_liga(liga: Literal["euroliga", "wnba"], peticion: PeticionLocal):
    from servicios.consulta_local_ligas import consultar
    try:
        return consultar(cargar_liga(liga), liga, peticion.equipo_local, peticion.equipo_visitante,
                         peticion.periodo, peticion.linea)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/modelos")
def modelos_publicados():
    """Inventario del disco, no acreditación de BD ni evaluación nueva."""
    resultados = {}
    try:
        resultados['nba'] = {'disponible': True, **identidad_modelo(modelo_local()),
                             'validacion': None, 'limite': 'El artefacto no contiene evaluación temporal independiente.'}
    except HTTPException:
        resultados['nba'] = {'disponible': False, 'limite': 'Artefacto no disponible.'}
    from motor.euroliga import cargar as cargar_euro
    from servicios.predictor_wnba import cargar as cargar_wnba
    for liga, loader in (('euroliga', cargar_euro), ('wnba', cargar_wnba)):
        try:
            m = loader()
            validacion = {k: v for k, v in m.get('validacion', {}).items() if k not in ('candidato', 'cohorte', 'rechazados')}
            resultados[liga] = {'disponible': True, 'modelo_version': m['version'],
                'corte_modelo': m.get('fecha_max') or max((r['fecha'] for r in m.get('datos', [])), default=None),
                'dataset_hash': m['dataset_sha256'], 'validacion': validacion,
                'limite': 'Evaluación del candidato de desarrollo, no eficacia acreditada del refit publicado.'}
        except (RuntimeError, ValueError, OSError, KeyError):
            resultados[liga] = {'disponible': False, 'limite': 'Artefacto no disponible o no íntegro; no se utiliza otra liga.'}
    resultados['futbol'] = {'disponible': None, 'limite': 'V4 de laboratorio: necesita cohorte original y outcomes posteriores. Este inventario sin BD no acredita modelos activos.'}
    return {'fuente': 'artefactos_locales', 'certificacion': 'NO_CERTIFICADO', 'modelos': resultados}
