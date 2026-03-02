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
    ganador_probable: str | None = None,
    probabilidad_ganador: float | None = None,
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


    diferencial = round(media_equipo - media_rival, 2)
    ganador = nombre_equipo if diferencial >= 0 else nombre_rival
    if ganador_probable:
        ganador = nombre_equipo if ganador_probable == "equipo" else nombre_rival

    razones.append(
        RazonPrediccion(
            factor="diferencial_estimado",
            direccion="sube" if diferencial >= 0 else "baja",
            impacto=abs(diferencial),
            descripcion=(
                f"Se proyecta {diferencial:+.1f} pts para {nombre_equipo} vs {nombre_rival} en el {unidad}."
            ),
        )
    )

    if probabilidad_ganador is not None:
        razones.append(
            RazonPrediccion(
                factor="probabilidad_victoria",
                direccion="sube",
                impacto=round(probabilidad_ganador * 100, 2),
                descripcion=(
                    f"{ganador} tiene {probabilidad_ganador * 100:.1f}% de probabilidad de ganar este {unidad}."
                ),
            )
        )

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
    ganador_probable: str | None = None,
    probabilidad_ganador: float | None = None,
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



    diferencial = round(media_ajustada - media_base, 2)
    if abs(diferencial) > 0.1:
        razones.append(
            RazonPrediccion(
                factor="impacto_contexto_ganador",
                direccion="sube" if diferencial >= 0 else "baja",
                impacto=abs(diferencial),
                descripcion=(
                    f"El contexto mueve la proyección en {diferencial:+.1f} pts respecto al modelo base."
                ),
            )
        )

    if probabilidad_ganador is not None:
        ganador = nombre_equipo if (ganador_probable or "equipo") == "equipo" else nombre_rival
        razones.append(
            RazonPrediccion(
                factor="probabilidad_victoria_ajustada",
                direccion="sube",
                impacto=round(probabilidad_ganador * 100, 2),
                descripcion=f"Probabilidad estimada de victoria para {ganador}: {probabilidad_ganador * 100:.1f}%.",
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
