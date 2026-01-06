# -*- coding: utf-8 -*-
"""rutas_ingestion.py — Endpoints de sincronización de partidos."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from starlette.concurrency import run_in_threadpool

from configuracion import CONFIGURACION
from ingestion import SyncConfig, sync_partidos_recientes
from motor_autoentrenamiento import GestorModelo

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])


def _validar_acceso(api_key: str | None) -> None:
    if not CONFIGURACION.ingestion_api_enabled:
        raise HTTPException(status_code=403, detail="Ingestión deshabilitada")
    if CONFIGURACION.ingestion_api_key:
        if not api_key or api_key != CONFIGURACION.ingestion_api_key:
            raise HTTPException(status_code=401, detail="API key inválida")


@router.post("/sync", summary="Sincronizar partidos recientes")
async def sync_partidos(
    days: int = Query(7, ge=1, le=60),
    force: bool = Query(False),
    dry_run: bool = Query(False),
    source: str = Query("espn"),
    x_api_key: str | None = Header(default=None, alias="X-API-KEY"),
):
    _validar_acceso(x_api_key)

    cfg = SyncConfig(days=days, force=force, dry_run=dry_run, source=source)
    resultado = await run_in_threadpool(sync_partidos_recientes, cfg)

    respuesta = {
        "exito": resultado.errores == 0,
        "ventana": {
            "inicio": resultado.start_date.isoformat(),
            "fin": resultado.end_date.isoformat(),
        },
        "resumen": {
            "events_detected": resultado.events_detected,
            "events_processed": resultado.events_processed,
            "insertados": resultado.insertados,
            "actualizados": resultado.actualizados,
            "omitidos": resultado.omitidos,
            "errores": resultado.errores,
            "dry_run": resultado.dry_run,
        },
        "detalles": resultado.detalles[:10],
    }

    if not dry_run and (resultado.insertados + resultado.actualizados) > 0:
        gestor = GestorModelo.obtener_instancia()
        await gestor.reentrenar_async()
        respuesta["modelo"] = "reentrenado"
    else:
        respuesta["modelo"] = "sin cambios"

    return respuesta
