"""Contratos exclusivos Euroliga: análisis neutral y trazabilidad sin DML."""
from datetime import datetime, timedelta, timezone
import logging
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from motor.euroliga import cargar, final_valido, normalizar_nombre, predecir
from servicios.predictor_euroliga import contexto, historial, leer_datos, registrar, resumir_fixture
from servicios.analisis_integral import integral_euroliga, aplicar_escenario_euroliga

router = APIRouter(prefix="/api/euroliga", tags=["Predictor Euroliga"])
logger = logging.getLogger(__name__)


class PeticionEuroliga(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    equipo_local: str = Field(min_length=2, max_length=120)
    equipo_visitante: str = Field(min_length=2, max_length=120)
    mercado: Literal["Q1", "Q2", "Q3", "Q4", "COMPLETO"] = "COMPLETO"
    linea: float = Field(gt=0, le=600)
    partido_id: UUID | None = None
    lado: Literal["OVER", "UNDER"] = "OVER"
    cuota_over: float | None = Field(default=None, gt=1, le=1000)
    cuota_under: float | None = Field(default=None, gt=1, le=1000)
    parciales: list[tuple[Annotated[int, Field(strict=True, ge=0, le=100)], Annotated[int, Field(strict=True, ge=0, le=100)]]] = Field(default_factory=list, max_length=3)


def modelo_actual():
    try:
        return cargar()
    except (RuntimeError, ValueError, KeyError, OSError) as exc:
        logger.warning("Modelo Euroliga no disponible: %s", type(exc).__name__)
        raise HTTPException(503, "Modelo Euroliga no disponible; revisar publicación offline") from exc


@router.get("/estado")
def estado():
    m = modelo_actual()
    return {"exito": True, "dominio": m["dominio"], "version": m["version"], "corte_datos": m["fecha_max"],
            "fit_completed_at": m["fit_completed_at"], "partidos": m["partidos_entrenamiento"],
            "equipos": len(m["entidades"]), "dataset_sha256": m["dataset_sha256"],
            "certificacion": m["certificacion"], "calibrador": None, "incluye_ot": False,
            "min_partidos_equipo": m["min_partidos_equipo"], "validacion": m["validacion"]}


@router.get("/equipos")
def equipos():
    m = modelo_actual()
    return {"exito": True, "equipos": [{**v, "muestras": m["muestras_equipo"][k],
             "elegible": m["muestras_equipo"][k] >= m["min_partidos_equipo"]} for k, v in sorted(m["catalogo"].items())]}


@router.get("/partidos")
def partidos(dias: int = Query(30, ge=1, le=60)):
    hoy = datetime.now(timezone.utc).date()
    fin = hoy + timedelta(days=dias)
    filas = leer_datos()
    historico = False
    resultados = [resumir_fixture(r) for r in filas if r["valido"] is True and hoy.isoformat() <= str(r["fecha_partido"])[:10] <= fin.isoformat() and not final_valido(r)]
    finales = [str(r["fecha_partido"])[:10] for r in filas if final_valido(r)]
    return {"exito": True, "partidos": resultados, "total": len(resultados), "ultimo_final_bd": max(finales) if finales else None,
            "observado_en": datetime.now(timezone.utc).isoformat(), "zona_fechas": "fecha canónica de competición; sin hora de kickoff"}


@router.post("/analizar")
def analizar(p: PeticionEuroliga):
    m = modelo_actual()
    fixture = None
    historico = False
    filas = leer_datos()
    if p.partido_id:
        fixture = next((r for r in filas if str(r["id"]) == str(p.partido_id)), None)
        if not fixture or fixture["valido"] is not True:
            raise HTTPException(422, "Fixture no pertenece a Euroliga válida")
        if any(normalizar_nombre(fixture[k]) != normalizar_nombre(nombre) for k, nombre in (("local", p.equipo_local), ("visitante", p.equipo_visitante))):
            raise HTTPException(422, "Equipos/localía no coinciden con el fixture Euroliga")
        from servicios.agenda_baloncesto import ahora
        from servicios.horarios_agenda import horario_partido, requiere_reconstruccion
        fixture['horario'] = horario_partido(fixture['id'])
        historico = requiere_reconstruccion(fixture['fecha_partido'],fixture['horario'],ahora())
        if not historico and str(fixture["fecha_partido"])[:10] <= m["fecha_max"]:
            raise HTTPException(422, "Fixture no es posterior al corte del modelo")
    try:
        if historico:
            from motor.euroliga import preparar_filas, entrenar
            corte_historico = min(str(fixture['fecha_partido'])[:10],ahora().date().isoformat())
            previos = preparar_filas(filas, corte_historico)
            if len(previos) < 600:
                raise ValueError('Muestra Euroliga anterior al corte insuficiente para TRAIN/CAL/EVAL temporales')
            m = entrenar(filas, corte_historico,
                         inicio_cal=previos[len(previos)*6//10]['fecha_partido'],
                         inicio_eval=previos[len(previos)*8//10]['fecha_partido'])
        resultado = predecir(m, p.equipo_local, p.equipo_visitante, p.mercado, p.linea, [list(q) for q in p.parciales])
        if historico:
            resultado['modo'] = 'HISTORICO_RECONSTRUIDO'
            resultado['advertencias'].append('Reconstrucción con datos anteriores al día del encuentro. No es un pronóstico emitido entonces; solo consulta, sin publicar el refit ni conservar journal.')
        corte = corte_historico if historico else str(fixture["fecha_partido"])[:10] if fixture else (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
        resultado["contexto"] = contexto(
            filas, p.equipo_local, p.equipo_visitante, corte, m.get("temporada_reciente")
        )
        validacion = m.get("validacion", {})
        resultado["diagnostico_modelo"] = {
            "partidos_entrenamiento": m.get("partidos_entrenamiento"),
            "fecha_min": m.get("fecha_min"),
            "fecha_max": m.get("fecha_max"),
            "alpha_ridge": m.get("alpha"),
            "ajuste_finalizado_en": m.get("fit_completed_at"),
        }
        resultado["validacion_historica"] = {
            "tipo": validacion.get("tipo"),
            "train_n": validacion.get("train_n"),
            "cal_n": validacion.get("cal_n"),
            "cal_util_n": validacion.get("cal_util_n"),
            "evaluacion": validacion.get("evaluacion"),
            "calibrador_probabilistico": validacion.get("calibrador_probabilistico"),
            "prospectiva_n": validacion.get("prospectiva_n", 0),
            "limitacion": validacion.get("limitacion"),
        }
        resultado["ultimo_final_bd"] = max((str(r["fecha_partido"])[:10] for r in filas if final_valido(r)), default=None)
        if resultado["ultimo_final_bd"] and resultado["ultimo_final_bd"] > m["fecha_max"]:
            resultado["advertencias"].append("La base tiene finales posteriores al modelo; publicar un refit explícito para incorporarlos.")
        if (datetime.now(timezone.utc).date() - datetime.fromisoformat(m["fecha_max"]).date()).days > 3:
            resultado["advertencias"].append("Histórico del modelo con más de tres días de antigüedad; frescura de ronda no acreditada.")
        resultado["fecha_partido"] = str(fixture["fecha_partido"])[:10] if fixture else None
        integral = integral_euroliga(
            resultado, lado=p.lado, cuota_over=p.cuota_over, cuota_under=p.cuota_under
        )
        aplicar_escenario_euroliga(resultado, integral)
        if historico:
            resultado.update({'analisis_id': str(uuid4()), 'partido_id': str(fixture['id']),
                              'prospectiva_acreditada_por_fecha': False,
                              'corte_exclusivo': corte_historico, 'solo_consulta': True})
            return {'exito': True, 'resultado': resultado}
        return {"exito": True, "resultado": registrar(resultado, fixture)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except OSError as exc:
        logger.error("No se pudo conservar análisis Euroliga: %s", type(exc).__name__)
        raise HTTPException(503, "No se pudo conservar la trazabilidad del análisis") from exc


@router.get("/historial")
def consultar_historial(limite: int = Query(20, ge=1, le=100)):
    resultados = historial(limite)
    for r in resultados:
        if "analisis_integral" not in r:
            r["analisis_integral"] = integral_euroliga(r, aplicar_contexto=False)
    return {"exito": True, "analisis": resultados}
