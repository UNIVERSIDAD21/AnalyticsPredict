# -*- coding: utf-8 -*-
"""
generador_razones.py — Genera explicaciones para las predicciones.
"""

from __future__ import annotations

from typing import List

from .tipos import RazonPrediccion


def generar_razones_basicas(
    nombre_equipo: str,
    nombre_rival: str,
    media_equipo: float,
    media_rival: float,
    media_total: float,
    mercado: str,
) -> List[RazonPrediccion]:
    """Genera razones básicas basadas en las medias predichas."""
    razones: List[RazonPrediccion] = []
    unidad = "partido" if mercado == "COMPLETO" else "cuarto"

    impacto_total = round(media_total - (media_equipo + media_rival), 2)
    direccion_total = "sube" if impacto_total >= 0 else "baja"
    razones.append(
        RazonPrediccion(
            factor="total_estimado",
            direccion=direccion_total,
            impacto=impacto_total,
            descripcion=(
                f"Total estimado {media_total:.1f} pts entre {nombre_equipo} y {nombre_rival}."
            ),
        )
    )

    impacto_equipo = round(media_equipo, 2)
    razones.append(
        RazonPrediccion(
            factor="ataque_equipo",
            direccion="sube",
            impacto=impacto_equipo,
            descripcion=f"{nombre_equipo} proyecta {media_equipo:.1f} pts en el {unidad}.",
        )
    )

    impacto_rival = round(media_rival, 2)
    razones.append(
        RazonPrediccion(
            factor="ataque_rival",
            direccion="sube",
            impacto=impacto_rival,
            descripcion=f"{nombre_rival} proyecta {media_rival:.1f} pts en el {unidad}.",
        )
    )

    return razones


def generar_razones_ajustes(
    nombre_equipo: str,
    nombre_rival: str,
    mercado: str,
    media_base: float,
    media_ajustada: float,
    linea: float | None,
    ajustes,
) -> List[RazonPrediccion]:
    """Genera razones enriquecidas basadas en ajustes contextuales."""
    unidad = "partido" if mercado == "COMPLETO" else "cuarto"
    razones: List[RazonPrediccion] = []
    direccion_base = "sube" if media_ajustada >= media_base else "baja"
    linea_texto = f" (línea: {linea:.1f})" if linea is not None else ""

    razones.append(
        RazonPrediccion(
            factor="prediccion_sistema",
            direccion=direccion_base,
            impacto=round(media_ajustada, 2),
            descripcion=(
                f"Sistema proyecta {media_ajustada:.1f} pts en el {unidad} entre "
                f"{nombre_equipo} y {nombre_rival}{linea_texto}."
            ),
        )
    )

    ajustes_filtrados = [
        ajuste for ajuste in ajustes.ajustes if abs(ajuste.valor) > 0.5
    ]
    ajustes_ordenados = sorted(ajustes_filtrados, key=lambda a: abs(a.valor), reverse=True)
    for ajuste in ajustes_ordenados:
        razones.append(
            RazonPrediccion(
                factor=ajuste.factor,
                direccion=ajuste.direccion,
                impacto=round(ajuste.valor, 2),
                descripcion=ajuste.descripcion,
            )
        )

    razones.append(
        RazonPrediccion(
            factor="resumen_neto",
            direccion="sube" if ajustes.ajuste_total_capped >= 0 else "baja",
            impacto=round(ajustes.ajuste_total_capped, 2),
            descripcion=(
                f"Ajuste neto: {ajustes.ajuste_total_capped:+.1f} pts. "
                f"Contexto reciente para {nombre_equipo} vs {nombre_rival}."
            ),
        )
    )

    return razones
