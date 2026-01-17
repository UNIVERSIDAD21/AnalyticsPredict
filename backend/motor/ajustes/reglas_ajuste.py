# -*- coding: utf-8 -*-
"""reglas_ajuste.py — Reglas de negocio para ajustes contextuales."""

from __future__ import annotations

from typing import List

from .tipos_ajustes import AjusteIndividual, ResultadoAjustes
from ..contexto.tipos_contexto import ContextoCompleto

CONFIG_AJUSTES = {
    "b2b_impacto_pts": -4.0,
    "b2b_impacto_ambos": -7.0,
    "b2b_impacto_confianza": -0.5,
    "descanso_umbral_dias": 2,
    "descanso_impacto": 1.5,
    "descanso_max_impacto": 2.0,
    "h2h_min_partidos": 3,
    "h2h_umbral_diferencia": 5.0,
    "h2h_factor_aplicacion": 0.30,
    "h2h_max_impacto": 3.0,
    "forma_umbral_diferencia": 3.0,
    "forma_factor_aplicacion": 0.40,
    "forma_max_impacto": 3.0,
    "ajuste_max_individual": 5.0,
    "ajuste_max_total": 8.0,
}


def _crear_ajuste(
    factor: str,
    valor: float,
    confianza: float,
    descripcion: str,
    datos: dict,
) -> AjusteIndividual:
    direccion = "sube" if valor >= 0 else "baja"
    return AjusteIndividual(
        factor=factor,
        valor=valor,
        direccion=direccion,
        confianza_ajuste=confianza,
        descripcion=descripcion,
        datos_soporte=datos,
    )


def calcular_ajustes(contexto: ContextoCompleto, media_base: float) -> ResultadoAjustes:
    ajustes: List[AjusteIndividual] = []
    advertencias: List[str] = []

    descanso_equipo = contexto.descanso_equipo
    descanso_rival = contexto.descanso_rival

    b2b_equipo = descanso_equipo.es_back_to_back
    b2b_rival = descanso_rival.es_back_to_back

    if b2b_equipo and b2b_rival:
        ajustes.append(
            _crear_ajuste(
                "back_to_back",
                CONFIG_AJUSTES["b2b_impacto_ambos"],
                0.75,
                "Ambos equipos en back-to-back: fatiga acumulada reduce ritmo.",
                {
                    "equipo_b2b": True,
                    "rival_b2b": True,
                },
            )
        )
        advertencias.append("⚠️ Ambos equipos en BACK-TO-BACK.")
    elif b2b_equipo or b2b_rival:
        afectado = "equipo" if b2b_equipo else "rival"
        ajustes.append(
            _crear_ajuste(
                "back_to_back",
                CONFIG_AJUSTES["b2b_impacto_pts"],
                0.85,
                f"{afectado.capitalize()} en back-to-back: fatiga esperada reduce anotación.",
                {
                    "equipo_b2b": b2b_equipo,
                    "rival_b2b": b2b_rival,
                },
            )
        )
        advertencias.append("⚠️ Back-to-back confirmado en uno de los equipos.")

    diferencia_descanso = descanso_equipo.dias_descanso - descanso_rival.dias_descanso
    if abs(diferencia_descanso) >= CONFIG_AJUSTES["descanso_umbral_dias"]:
        valor = CONFIG_AJUSTES["descanso_impacto"]
        if diferencia_descanso < 0:
            valor *= -1
        ajustes.append(
            _crear_ajuste(
                "descanso_asimetrico",
                valor,
                0.75,
                "Ventaja de descanso significativa entre equipos.",
                {
                    "dias_equipo": descanso_equipo.dias_descanso,
                    "dias_rival": descanso_rival.dias_descanso,
                    "diferencia": diferencia_descanso,
                },
            )
        )
        advertencias.append("⚠️ Ventaja significativa de descanso.")

    h2h = contexto.h2h
    if h2h and h2h.total_partidos >= CONFIG_AJUSTES["h2h_min_partidos"]:
        diferencia_h2h = h2h.promedio_total - media_base
        if abs(diferencia_h2h) > CONFIG_AJUSTES["h2h_umbral_diferencia"]:
            ajuste = diferencia_h2h * CONFIG_AJUSTES["h2h_factor_aplicacion"]
            ajuste = max(min(ajuste, CONFIG_AJUSTES["h2h_max_impacto"]), -CONFIG_AJUSTES["h2h_max_impacto"])
            ajustes.append(
                _crear_ajuste(
                    "h2h_tendencia",
                    ajuste,
                    0.70,
                    "H2H reciente sugiere ajuste en el total.",
                    {
                        "promedio_h2h": h2h.promedio_total,
                        "muestra": h2h.total_partidos,
                        "diferencia_vs_base": diferencia_h2h,
                        "factor_aplicado": CONFIG_AJUSTES["h2h_factor_aplicacion"],
                    },
                )
            )
            if abs(diferencia_h2h) > 10:
                advertencias.append("⚠️ Diferencia H2H vs base mayor a 10 pts.")

    for etiqueta, forma in (("equipo", contexto.forma_equipo), ("rival", contexto.forma_rival)):
        diferencia = forma.diferencia_vs_temporada
        if abs(diferencia) > CONFIG_AJUSTES["forma_umbral_diferencia"]:
            ajuste = diferencia * CONFIG_AJUSTES["forma_factor_aplicacion"]
            ajuste = max(min(ajuste, CONFIG_AJUSTES["forma_max_impacto"]), -CONFIG_AJUSTES["forma_max_impacto"])
            ajustes.append(
                _crear_ajuste(
                    f"forma_ofensiva_{etiqueta}",
                    ajuste,
                    0.65,
                    "Diferencia reciente en puntos anotados vs temporada.",
                    {
                        "ppg_reciente": forma.ppg,
                        "ppg_temporada": forma.ppg_temporada,
                        "diferencia": diferencia,
                        "factor_aplicado": CONFIG_AJUSTES["forma_factor_aplicacion"],
                    },
                )
            )

    ajuste_total = sum(ajuste.valor for ajuste in ajustes)

    return ResultadoAjustes(
        ajustes=ajustes,
        ajuste_total=ajuste_total,
        ajuste_total_capped=ajuste_total,
        fue_capped=False,
        advertencias=advertencias,
        confianza_delta=0.0,
    )
