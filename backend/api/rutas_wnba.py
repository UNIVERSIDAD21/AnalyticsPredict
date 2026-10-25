"""API WNBA aislada; SQL READ ONLY, journal propio, sin fallback ni efectos financieros."""

from datetime import date, datetime
from collections import Counter
from typing import Literal, Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from psycopg import Error as DatabaseError
from motor.wnba import BOGOTA, MIN_EQUIPO, normalizar, huella
from servicios import predictor_wnba as svc

router = APIRouter(prefix="/api/wnba", tags=["Predictor WNBA"])


class PeticionWNBA(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    equipo_local_id: UUID
    equipo_visitante_id: UUID
    temporadas: list[UUID] = Field(min_length=1, max_length=20)
    corte: date | None = None
    fases: list[Literal["REG", "POST"]] = Field(
        default_factory=lambda: ["REG"], min_length=1, max_length=2
    )
    mercado: Literal["Q1", "Q2", "Q3", "Q4", "COMPLETO"] = "COMPLETO"
    linea: float = Field(ge=0, le=600)
    partido_id: str | None = Field(default=None, max_length=100)
    modo: Literal["PREPARTIDO", "CIERRE_Q1", "CIERRE_Q2", "CIERRE_Q3"] = "PREPARTIDO"
    parciales: list[tuple[Annotated[StrictInt, Field(ge=0, le=100)], Annotated[StrictInt, Field(ge=0, le=100)]]] = Field(default_factory=list, max_length=3)
    contrato: Literal["REGULACION_V1", "NBA_EQUIVALENTE_V2"] = "REGULACION_V1"
    es_prueba: bool = False
    lado: Literal["OVER", "UNDER"] = "OVER"
    cuota_over: float | None = Field(default=None, gt=1, le=1000)
    cuota_under: float | None = Field(default=None, gt=1, le=1000)


def modelo():
    try:
        return svc.cargar()
    except (RuntimeError, ValueError, OSError, KeyError) as e:
        raise HTTPException(
            503,
            "Modelo WNBA ausente o incompatible. Publicar con gestionar_predictor_wnba.py; otras ligas no se ven afectadas.",
        ) from e


def datos_bd():
    try:
        filas = svc.leer_datos()
        normalizar(filas)
        return filas
    except (DatabaseError, RuntimeError, ValueError, KeyError) as e:
        raise HTTPException(
            503,
            "Datos WNBA no disponibles o inconsistentes; revisar ingesta/conexión y reintentar. No se utiliza otra liga.",
        ) from e


@router.get("/catalogo")
def catalogo():
    filas = datos_bd()
    datos = normalizar(filas)
    teams = {}
    years = {}
    for r in datos:
        for idkey, name in (("local_id", "local"), ("visitante_id", "visitante")):
            t = teams.setdefault(
                r[idkey], {"id": r[idkey], "nombre": r[name], "muestras": 0}
            )
            t["muestras"] += 1
        y = years.setdefault(
            r["temporada_id"],
            {"id": r["temporada_id"], "nombre": r["temporada"], "fases": Counter(), "equipos": []},
        )
        y["fases"][r["fase"]] += 1
        y["equipos"] = sorted(set(y["equipos"]) | {r["local_id"], r["visitante_id"]})
    for t in teams.values():
        t["elegible"] = t["muestras"] >= MIN_EQUIPO
    status = {"disponible": False, "motivo": "Modelo WNBA no publicado"}
    try:
        m = svc.cargar()
        status = {
            "disponible": True,
            "version": m["version"],
            "publicado_utc": m["publicado_utc"],
            "ultimo_snapshot": max(r["fecha"] for r in m["datos"]),
            "dataset_sha256": m["dataset_sha256"],
            "politica": m["politica"],
            "desactualizado": huella(datos) != m["dataset_sha256"],
            "validacion": {
                k: v
                for k, v in m["validacion"].items()
                if k not in ("candidato", "cohorte", "rechazados")
            },
        }
    except (RuntimeError, ValueError, OSError, KeyError):
        pass
    return {
        "exito": True,
        "modelo": status,
        "equipos": sorted(teams.values(), key=lambda t: t["nombre"]),
        "temporadas": sorted(years.values(), key=lambda t: t["nombre"]),
        "ultimo_final_bd": max((r["fecha"] for r in datos), default=None),
        "fuente_n": len(filas),
        "elegibles_n": len(datos),
        "finales_n": sum(r["estado"] == "FINALIZADO" for r in filas),
        "cobertura": "Cobertura del lote en BD; no certificada contra calendario independiente.",
    }


@router.get("/partidos")
def partidos(historicos: bool = False, limite: int = Query(50, ge=1, le=100)):
    if not historicos:
        from servicios.calendario_wnba import listar
        from servicios.predictor_euroliga import conexion_lectura
        with conexion_lectura() as conn:
            rows, comprobacion = listar(conn)
        return {"exito": True, "partidos": [
            {"id":str(r["id"]), "fecha_partido":r["inicio_utc"].isoformat() if r["inicio_utc"] else str(r["fecha_local"] or ''),
             "equipo_local_id":str(r["equipo_local_id"]),"equipo_visitante_id":str(r["equipo_visitante_id"]),
             "equipo_local_nombre":r["local"],"equipo_visitante_nombre":r["visitante"],
             "tipo_partido":r["fase"],"temporada_id":str(r["temporada_id"]),
             "temporada_nombre":"WNBA "+r["temporada_nombre"],"competicion_codigo":"wnba",
             "estado":r["estado"],"precision_fecha":r["precision_fecha"],
             "condicional":r["registro"].get("condicional",False),"local_total":None,"visitante_total":None,"finalizado":False}
            for r in rows if r["estado"] != "FINALIZADO"], "comprobacion":comprobacion}
    filas = datos_bd()
    now = datetime.now(BOGOTA)
    selected = [
        r
        for r in filas
        if r["fase"] in ("REG", "POST")
        and (
            (historicos and r["estado"] == "FINALIZADO" and r["valido"] is True)
            or (
                not historicos
                and r["estado"] == "PROGRAMADO"
                and datetime.fromisoformat(r["inicio_utc"]) >= now
            )
        )
    ]
    selected = sorted(selected, key=lambda r: r["inicio_utc"], reverse=historicos)[
        :limite
    ]
    return {
        "exito": True,
        "partidos": [
            {
                "id": (
                    str(r["partido_id"])
                    if r["partido_id"]
                    else "espn-" + r["source_game_id"]
                ),
                "fecha_partido": r["inicio_utc"],
                "equipo_local_id": str(r["equipo_local_id"]),
                "equipo_visitante_id": str(r["equipo_visitante_id"]),
                "equipo_local_nombre": r["local"],
                "equipo_visitante_nombre": r["visitante"],
                "tipo_partido": r["fase"],
                "temporada_id": str(r["temporada_id"]),
                "temporada_nombre": r["temporada_nombre"],
                "competicion_codigo": "wnba",
            }
            for r in selected
        ],
    }


@router.post("/analizar")
def analizar(p: PeticionWNBA):
    m = modelo()
    try:
        if p.modo != (f"CIERRE_Q{len(p.parciales)}" if p.parciales else "PREPARTIDO"):
            raise ValueError("Modo y cuartos terminados contradictorios")
        if p.parciales and (p.contrato != "NBA_EQUIVALENTE_V2" or p.cuota_over or p.cuota_under):
            raise ValueError("Los cortes WNBA requieren contrato v2 y no admiten cuotas prepartido")
        result = svc.analizar(
            m,
            datos_para_analisis() if p.partido_id and p.contrato == "NBA_EQUIVALENTE_V2" else datos_bd(),
            str(p.equipo_local_id),
            str(p.equipo_visitante_id),
            [str(x) for x in p.temporadas],
            p.corte.isoformat() if p.corte else None,
            p.fases,
            p.mercado,
            p.linea,
            p.partido_id,
            p.es_prueba,
            p.cuota_over,
            p.cuota_under,
            [list(q) for q in p.parciales],
            p.contrato == "NBA_EQUIVALENTE_V2",
        )
        result["lado_solicitado"] = p.lado
        return {"exito": True, "resultado": svc.registrar(result)}
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except OSError as e:
        raise HTTPException(
            503,
            "No se pudo conservar el historial WNBA; revisar permisos del directorio propio",
        ) from e


def datos_para_analisis():
    from servicios.calendario_wnba import listar
    from servicios.predictor_euroliga import conexion_lectura
    filas = datos_bd()
    with conexion_lectura() as conn:
        fixtures, _ = listar(conn)
    for r in fixtures:
        if r["inicio_utc"] is None:
            continue  # No acreditar una predicción oficial con una hora inventada.
        filas.append({**r,"fixture_id":str(r["id"]),"partido_id":str(r["resultado_id"]) if r["resultado_id"] else None,
                      "inicio_utc":r["inicio_utc"].isoformat(),"valido":False})
    return filas


@router.post("/calendario/sincronizar")
def sincronizar_calendario():
    import os
    from pathlib import Path
    from uuid import uuid4
    from servicios.calendario_wnba import consultar
    from scripts.sincronizar_calendario_wnba import ejecutar
    from db import obtener_pool
    reporte = consultar()
    destino = Path.home()/".local/share/analyticspredict/wnba/calendario"/str(uuid4())
    # El pool usa la configuración protegida existente; no pasar credenciales al cliente.
    url = os.environ.get("DATABASE_URL")
    if not url:
        url = obtener_pool().conninfo
    try:
        ejecutar(reporte,destino,url,aplicar_cambios=True)
    except (ValueError, OSError, DatabaseError) as e:
        raise HTTPException(503,"Sincronización WNBA detenida; no hay actualización de resultados/modelos. Revisar evidencia local.") from e
    return {"exito":True,"comprobacion":{k:v for k,v in reporte.items() if k!='partidos'}}


from esquemas.combinadas import SeleccionCombinadaCrear


class EvaluarCombinadaWNBA(BaseModel):
    selecciones: list[SeleccionCombinadaCrear] = Field(min_length=1,max_length=20)


@router.post("/combinadas/evaluar")
def evaluar_combinada(p: EvaluarCombinadaWNBA):
    from servicios.combinadas_wnba import evaluar
    try:
        ss=[s.model_dump(mode="json") for s in p.selecciones]
        return {"exito":True, **evaluar(ss)}
    except (ValueError, OSError, KeyError) as e:
        raise HTTPException(422,str(e)) from e


@router.get("/historial")
def historial(limite: int = Query(20, ge=1, le=100)):
    try:
        return {"exito": True, "analisis": svc.historial_para_vista(limite)}
    except (ValueError, OSError) as e:
        raise HTTPException(
            503, "Historial WNBA no legible; revisar archivos locales"
        ) from e


@router.get("/estadisticas")
def estadisticas(temporada_id: UUID | None = None):
    from servicios.presentacion_wnba import estadisticas as presentar
    rows = [r for r in normalizar(datos_bd()) if r["fecha"] < datetime.now(BOGOTA).date().isoformat()]
    try:
        return presentar(rows, str(temporada_id) if temporada_id else None)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.get("/equipos/{equipo_id}/historial")
def historial_equipo(equipo_id: UUID, limite: int = Query(5000, ge=1, le=5000),
                     temporada_id: UUID | None = None, como_local: bool | None = None,
                     analisis_id: UUID | None = None):
    from servicios.presentacion_wnba import historial_equipo as presentar
    from motor.wnba import alcance
    import json
    rows = normalizar(datos_bd())
    regulacion = False
    if analisis_id:
        try:
            r = json.loads((svc.journal() / (str(analisis_id) + ".json")).read_text())
            if str(equipo_id) not in (r["equipo_local_id"], r["equipo_visitante_id"]):
                raise ValueError("Equipo distinto del análisis WNBA")
            # Usa el snapshot que produjo el resultado, no finales llegados después.
            m = svc.cargar_publicacion(r["publicacion_version"])
            rows = alcance(m["datos"], [s["id"] for s in r["temporadas_solicitadas"]], r["corte_exclusivo"], r["fases_solicitadas"])
            regulacion = not r["incluye_ot"]
        except (ValueError, OSError, KeyError) as e:
            raise HTTPException(422, "No se pudo recuperar el alcance original WNBA") from e
    else:
        rows = [r for r in rows if r["fecha"] < datetime.now(BOGOTA).date().isoformat()]
    try:
        return presentar(rows, str(equipo_id), limite=limite,
                         temporada=str(temporada_id) if temporada_id else None,
                         como_local=como_local, regulacion=regulacion)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
