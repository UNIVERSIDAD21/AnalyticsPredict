"""API WNBA aislada; SQL READ ONLY, journal propio, sin fallback ni efectos financieros."""

from datetime import date, datetime
from collections import Counter
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
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
    modo: Literal["PREPARTIDO"] = "PREPARTIDO"
    es_prueba: bool = False
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
            {"id": r["temporada_id"], "nombre": r["temporada"], "fases": Counter()},
        )
        y["fases"][r["fase"]] += 1
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
        result = svc.analizar(
            m,
            datos_bd(),
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
        )
        return {"exito": True, "resultado": svc.registrar(result)}
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except OSError as e:
        raise HTTPException(
            503,
            "No se pudo conservar el historial WNBA; revisar permisos del directorio propio",
        ) from e


@router.get("/historial")
def historial(limite: int = Query(20, ge=1, le=100)):
    try:
        return {"exito": True, "analisis": svc.historial(limite)}
    except (ValueError, OSError) as e:
        raise HTTPException(
            503, "Historial WNBA no legible; revisar archivos locales"
        ) from e
