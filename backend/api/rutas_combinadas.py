# -*- coding: utf-8 -*-
"""
rutas_combinadas.py — Endpoints CRUD para combinadas (parlays).
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from esquemas.combinadas import (
    PeticionActualizarResultadoCombinada,
    PeticionCrearCombinada,
    RespuestaCombinada,
    RespuestaListaCombinadas,
)
from servicios.servicio_combinadas import (
    actualizar_resultado_combinada_db,
    crear_combinada_db,
    eliminar_combinada_db,
    listar_combinadas_db,
    obtener_combinada_db,
)
from .dependencias import obtener_usuario_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/combinadas", tags=["Combinadas"])


@router.post("", summary="Crear combinada", response_model=RespuestaCombinada)
async def crear_combinada(
    peticion: PeticionCrearCombinada,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaCombinada:
    if len(peticion.selecciones) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una combinada requiere mínimo 2 selecciones.",
        )

    combinada = crear_combinada_db(peticion, usuario_id)
    return RespuestaCombinada(exito=True, combinada=combinada)


@router.get("", summary="Listar combinadas", response_model=RespuestaListaCombinadas)
async def listar_combinadas(
    usuario_id: UUID = Depends(obtener_usuario_id),
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=100),
    resultado: Optional[str] = None,
) -> RespuestaListaCombinadas:
    total, total_paginas, combinadas = listar_combinadas_db(
        usuario_id=usuario_id,
        pagina=pagina,
        tamano=tamano,
        resultado=resultado,
    )
    return RespuestaListaCombinadas(
        exito=True,
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        combinadas=combinadas,
    )


@router.get("/{combinada_id}", summary="Detalle combinada", response_model=RespuestaCombinada)
async def obtener_combinada(
    combinada_id: UUID,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaCombinada:
    try:
        combinada = obtener_combinada_db(combinada_id, usuario_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RespuestaCombinada(exito=True, combinada=combinada)


@router.patch("/{combinada_id}/resultado", summary="Actualizar resultado combinada", response_model=RespuestaCombinada)
async def actualizar_resultado_combinada(
    combinada_id: UUID,
    peticion: PeticionActualizarResultadoCombinada,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaCombinada:
    """Actualiza el resultado de una combinada pendiente."""
    try:
        combinada = actualizar_resultado_combinada_db(
            combinada_id=combinada_id,
            usuario_id=usuario_id,
            resultado=peticion.resultado,
        )
    except ValueError as exc:
        mensaje = str(exc)
        if "no encontrada" in mensaje.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=mensaje) from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensaje) from exc

    return RespuestaCombinada(exito=True, combinada=combinada)


@router.delete("/{combinada_id}", summary="Eliminar combinada")
async def eliminar_combinada(
    combinada_id: UUID,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> dict:
    try:
        eliminar_combinada_db(combinada_id, usuario_id)
    except ValueError as exc:
        mensaje = str(exc)
        if "pendientes" in mensaje.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mensaje) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=mensaje) from exc

    return {"exito": True}
