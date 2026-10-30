"""Superficie local acotada y ajena a las escrituras del análisis estándar."""
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from motor_autoentrenamiento import obtener_modelo
from servicios.consulta_local import consultar, identidad_modelo

router = APIRouter(prefix="/api/local", tags=["Consulta base local"])


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
