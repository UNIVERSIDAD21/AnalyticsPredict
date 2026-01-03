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
) -> List[RazonPrediccion]:
    """Genera razones básicas basadas en las medias predichas."""
    razones: List[RazonPrediccion] = []

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
            descripcion=f"{nombre_equipo} proyecta {media_equipo:.1f} pts en el cuarto.",
        )
    )

    impacto_rival = round(media_rival, 2)
    razones.append(
        RazonPrediccion(
            factor="ataque_rival",
            direccion="sube",
            impacto=impacto_rival,
            descripcion=f"{nombre_rival} proyecta {media_rival:.1f} pts en el cuarto.",
        )
    )

    return razones
