# -*- coding: utf-8 -*-
"""
nba_predictor_cuartos.py — Motor de predicción por cuartos.

Este módulo expone funciones para cargar el modelo y generar predicciones
por cuarto o juego completo, incluyendo probabilidades y recomendaciones.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

import json
import numpy as np

from .calculadora_probabilidad import (
    calcular_intervalo_confianza,
    calcular_kelly,
    calcular_devig,
    calcular_probabilidad_over,
    calcular_probabilidad_victoria,
)
from .generador_razones import generar_razones_basicas, generar_razones_ajustes
from .calibradores import obtener_calibrador_activo
from .ajustes import aplicar_ajustes_contextuales
from .contexto import recolectar_contexto
from .tipos import (
    AnalisisMercado,
    CandidatoApuesta,
    ConfiguracionSizing,
    FactoresConfianza,
    LadoApuesta,
    ModeloRidge,
    NivelConfianza,
    PerfilRiesgo,
    PrediccionCuarto,
    RazonPrediccion,
    ResultadoAnalisis,
    ResultadoSizing,
    TipoMercado,
    Ubicacion,
    ScoreApuesta,
)
from .utilidades import (
    limitar_entre_0_y_1,
    normalizar_nombre,
    parsear_marcador,
    resolver_nombre_en_modelo,
)

CLAVES_CUARTOS = ("Q1", "Q2", "Q3", "Q4")
INDICE_CUARTOS = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3}
RIESGO_DESVIACION_UMBRAL = 7.5
SIGMA_GANADOR_NBA_COMPLETO = 12.5
PESO_MODELO_GANADOR = 0.25
PESO_MERCADO_GANADOR = 0.75

logger = logging.getLogger(__name__)


def cargar_modelo(ruta: str) -> ModeloRidge:
    """Carga un modelo Ridge desde un archivo .npz."""
    with np.load(ruta, allow_pickle=True) as datos:
        alfa = float(datos["alpha"][0])
        entidad_a_indice = json.loads(str(datos["entity_json"][0]))
        pesos_equipo = datos["w_team"]
        pesos_rival = datos["w_opp"]
        desviacion_equipo = datos["std_team"]
        desviacion_rival = datos["std_opp"]

    return ModeloRidge(
        alfa=alfa,
        entidad_a_indice=entidad_a_indice,
        pesos_equipo=pesos_equipo,
        pesos_rival=pesos_rival,
        desviacion_equipo=desviacion_equipo,
        desviacion_rival=desviacion_rival,
    )


def construir_matriz_diseno(
    nombres_equipo: Sequence[str],
    nombres_rival: Sequence[str],
    es_local: Sequence[int],
    entidad_a_indice: Dict[str, int],
) -> np.ndarray:
    """Construye la matriz de diseño para predicción Ridge."""
    cantidad = len(nombres_equipo)
    cantidad_entidades = len(entidad_a_indice)
    matriz = np.zeros((cantidad, 1 + cantidad_entidades + cantidad_entidades + 1), dtype=float)
    matriz[:, 0] = 1.0

    for indice, (equipo, rival, local) in enumerate(zip(nombres_equipo, nombres_rival, es_local)):
        indice_equipo = entidad_a_indice[normalizar_nombre(equipo)]
        indice_rival = entidad_a_indice[normalizar_nombre(rival)]
        matriz[indice, 1 + indice_equipo] = 1.0
        matriz[indice, 1 + cantidad_entidades + indice_rival] = 1.0
        matriz[indice, -1] = float(local)

    return matriz


def predecir_cuartos(
    modelo: ModeloRidge,
    equipo: str,
    rival: str,
    ubicacion: Ubicacion,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Predice medias y desviaciones para equipo y rival en Q1-Q4."""
    equipo_norm = resolver_nombre_en_modelo(equipo, modelo.entidad_a_indice)
    rival_norm = resolver_nombre_en_modelo(rival, modelo.entidad_a_indice)

    if equipo_norm is None:
        raise ValueError(f'Equipo "{equipo}" no está en el modelo.')
    if rival_norm is None:
        raise ValueError(f'Rival "{rival}" no está en el modelo.')

    es_local = 1 if ubicacion == Ubicacion.LOCAL else 0
    matriz = construir_matriz_diseno([equipo_norm], [rival_norm], [es_local], modelo.entidad_a_indice)

    media_equipo = (matriz @ modelo.pesos_equipo).reshape(-1)
    media_rival = (matriz @ modelo.pesos_rival).reshape(-1)
    desviacion_equipo = np.array(modelo.desviacion_equipo).reshape(-1)
    desviacion_rival = np.array(modelo.desviacion_rival).reshape(-1)

    return media_equipo, desviacion_equipo, media_rival, desviacion_rival


def aplicar_ajuste_en_vivo(
    media_equipo: np.ndarray,
    media_rival: np.ndarray,
    q1: Optional[Tuple[float, float]],
    q2: Optional[Tuple[float, float]],
    q3: Optional[Tuple[float, float]],
    peso_en_vivo: float,
    peso_q1: float = 0.15,
    peso_q2: float = 0.35,
    peso_q3: float = 0.50,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Tuple[float, float]], Dict[str, object]]:
    """Ajusta las predicciones con los marcadores reales de cuartos previos."""
    peso_en_vivo = limitar_entre_0_y_1(peso_en_vivo)

    media_equipo_ajustada = media_equipo.copy()
    media_rival_ajustada = media_rival.copy()

    reales: Dict[str, Tuple[float, float]] = {}
    metadata: Dict[str, object] = {
        "peso_en_vivo": peso_en_vivo,
        "peso_q1": float(peso_q1),
        "peso_q2": float(peso_q2),
        "peso_q3": float(peso_q3),
    }

    proporcionados: List[Tuple[str, Tuple[float, float], float]] = []
    if q1 is not None:
        proporcionados.append(("Q1", q1, peso_q1))
    if q2 is not None:
        proporcionados.append(("Q2", q2, peso_q2))
    if q3 is not None:
        proporcionados.append(("Q3", q3, peso_q3))

    if not proporcionados:
        raise ValueError("Debes proporcionar al menos un marcador de Q1, Q2 o Q3.")

    residuos_equipo: Dict[str, float] = {}
    residuos_rival: Dict[str, float] = {}

    for cuarto, (puntos_equipo, puntos_rival), _peso in proporcionados:
        indice = INDICE_CUARTOS[cuarto]
        reales[cuarto] = (float(puntos_equipo), float(puntos_rival))
        residuos_equipo[cuarto] = puntos_equipo - float(media_equipo[indice])
        residuos_rival[cuarto] = puntos_rival - float(media_rival[indice])
        media_equipo_ajustada[indice] = puntos_equipo
        media_rival_ajustada[indice] = puntos_rival

    peso_total = sum(max(0.0, peso) for _, _, peso in proporcionados) or 1.0
    residuo_equipo_comb = 0.0
    residuo_rival_comb = 0.0

    for cuarto, _puntos, peso in proporcionados:
        peso_normalizado = max(0.0, peso) / peso_total
        residuo_equipo_comb += peso_normalizado * residuos_equipo[cuarto]
        residuo_rival_comb += peso_normalizado * residuos_rival[cuarto]

    metadata["residuo_equipo_comb"] = residuo_equipo_comb
    metadata["residuo_rival_comb"] = residuo_rival_comb

    for cuarto in ("Q4", "Q3", "Q2"):
        if cuarto in reales:
            continue
        indice = INDICE_CUARTOS[cuarto]
        media_equipo_ajustada[indice] = float(media_equipo[indice]) + residuo_equipo_comb * peso_en_vivo
        media_rival_ajustada[indice] = float(media_rival[indice]) + residuo_rival_comb * peso_en_vivo

    return media_equipo_ajustada, media_rival_ajustada, reales, metadata


def calcular_prediccion_cuarto(
    cuarto: str,
    media_equipo: float,
    desviacion_equipo: float,
    media_rival: float,
    desviacion_rival: float,
    linea: Optional[float] = None,
) -> PrediccionCuarto:
    """Construye la predicción completa para un cuarto."""
    media_total = float(media_equipo) + float(media_rival)
    desviacion_total = float(np.sqrt(desviacion_equipo ** 2 + desviacion_rival ** 2))

    rango_equipo = calcular_intervalo_confianza(media_equipo, desviacion_equipo, z=1.0)
    rango_rival = calcular_intervalo_confianza(media_rival, desviacion_rival, z=1.0)
    rango_total = calcular_intervalo_confianza(media_total, desviacion_total, z=1.0)

    probabilidad_over = None
    probabilidad_under = None
    if linea is not None:
        probabilidad_over = calcular_probabilidad_over(media_total, desviacion_total, linea)
        probabilidad_under = 1.0 - probabilidad_over

    desviacion_equipo_victoria = desviacion_equipo
    desviacion_rival_victoria = desviacion_rival

    if cuarto == "COMPLETO":
        # Para probabilidad de ganador en juego completo usamos sigma empírico NBA
        # para evitar sobreestimar incertidumbre al propagar residuos por cuarto.
        sigma_por_lado = SIGMA_GANADOR_NBA_COMPLETO / np.sqrt(2.0)
        desviacion_equipo_victoria = float(sigma_por_lado)
        desviacion_rival_victoria = float(sigma_por_lado)

    probabilidad_ganador = calcular_probabilidad_victoria(
        media_equipo,
        desviacion_equipo_victoria,
        media_rival,
        desviacion_rival_victoria,
    )

    return PrediccionCuarto(
        cuarto=cuarto,
        media_equipo=media_equipo,
        desviacion_equipo=desviacion_equipo,
        rango_equipo=rango_equipo,
        media_rival=media_rival,
        desviacion_rival=desviacion_rival,
        rango_rival=rango_rival,
        media_total=media_total,
        desviacion_total=desviacion_total,
        rango_total=rango_total,
        linea_analizada=linea,
        probabilidad_over=probabilidad_over,
        probabilidad_under=probabilidad_under,
        ganador_probable="equipo" if probabilidad_ganador >= 0.5 else "rival",
        probabilidad_ganador=probabilidad_ganador,
    )


def candidatos_para_cuarto(
    cuarto: str,
    linea: float,
    media_equipo: float,
    desviacion_equipo: float,
    media_rival: float,
    desviacion_rival: float,
    cuota_over: Optional[float] = None,
    cuota_under: Optional[float] = None,
    modo_devig: str = "estricto",
    config_sizing: Optional[ConfiguracionSizing] = None,
    calibrador_activo: Optional[object] = None,
) -> List[CandidatoApuesta]:
    """Genera candidatos de apuesta para un cuarto específico."""
    if calibrador_activo is not None:
        mercado_calibrador = getattr(calibrador_activo, "mercado", None)
        if mercado_calibrador is not None and mercado_calibrador != cuarto:
            logger.warning(
                "Calibrador de mercado incorrecto ignorado (cuarto=%s calibrador.mercado=%s).",
                cuarto,
                mercado_calibrador,
            )
            calibrador_activo = None
    candidatos: List[CandidatoApuesta] = []
    media_total = media_equipo + media_rival
    desviacion_total = float(np.sqrt(desviacion_equipo ** 2 + desviacion_rival ** 2))

    prob_over_total = calcular_probabilidad_over(media_total, desviacion_total, linea)
    distancia_z_total = abs(media_total - linea) / max(desviacion_total, 1e-9)

    if modo_devig not in ("estimado", "estricto"):
        raise ValueError("modo_devig debe ser 'estimado' o 'estricto'.")
    modo_estimado = modo_devig == "estimado"
    riesgo_alto = desviacion_total > RIESGO_DESVIACION_UMBRAL

    def calcular_kelly_base(probabilidad: float, cuota: float) -> Optional[float]:
        if cuota <= 1.0 or not (0.0 <= probabilidad <= 1.0):
            return None
        b = cuota - 1.0
        q = 1.0 - probabilidad
        return (b * probabilidad - q) / b

    def construir_candidato(
        lado: LadoApuesta,
        probabilidad: float,
        cuota_lado: float,
        cuota_opuesta: Optional[float],
    ) -> CandidatoApuesta:
        p_raw = float(probabilidad)
        p_calibrada = (
            calibrador_activo.calibrar(p_raw) if calibrador_activo is not None else None
        )
        p_efectiva = p_calibrada if p_calibrada is not None else p_raw
        datos_devig = calcular_devig(
            cuota_lado,
            cuota_opuesta,
            modo_estimado=modo_estimado,
        )
        edge_real = p_efectiva - datos_devig.p_mkt_fair
        ev = (p_efectiva * cuota_lado) - 1.0

        sizing = None
        kelly_full: Optional[float] = None
        if config_sizing is not None:
            sizing = calcular_kelly(
                probabilidad=p_efectiva,
                cuota=cuota_lado,
                config=config_sizing,
                datos_devig=datos_devig,
                riesgo_alto=riesgo_alto,
            )
            kelly_full = sizing.kelly_full
        else:
            kelly_full = calcular_kelly_base(p_efectiva, cuota_lado)

        score = ScoreApuesta.calcular(
            ev=ev,
            edge_real=edge_real,
            riesgo=desviacion_total,
            datos_devig=datos_devig,
            kelly_full=kelly_full,
            riesgo_referencia=RIESGO_DESVIACION_UMBRAL,
        )

        return CandidatoApuesta(
            cuarto=cuarto,
            mercado=TipoMercado.TOTAL,
            lado=lado,
            linea=linea,
            probabilidad=p_efectiva,
            media=media_total,
            desviacion=desviacion_total,
            distancia_z=distancia_z_total,
            datos_devig=datos_devig,
            edge_real=edge_real,
            ev=ev,
            score=score,
            sizing=sizing,
            cuota=cuota_lado,
            cuota_over=cuota_over,
            cuota_under=cuota_under,
            p_raw=p_raw,
            p_calibrada=p_calibrada,
            calibrador_usado=calibrador_activo.metodo if p_calibrada is not None else None,
            calibrador_id=getattr(calibrador_activo, "id", None)
            if p_calibrada is not None
            else None,
        )

    if cuota_over is not None:
        candidatos.append(
            construir_candidato(
                LadoApuesta.OVER,
                prob_over_total,
                float(cuota_over),
                cuota_under,
            )
        )
    if cuota_under is not None:
        candidatos.append(
            construir_candidato(
                LadoApuesta.UNDER,
                1.0 - prob_over_total,
                float(cuota_under),
                cuota_over,
            )
        )

    return candidatos


def seleccionar_mejor_apuesta(candidatos: List[CandidatoApuesta]) -> Optional[CandidatoApuesta]:
    """Selecciona el candidato con mejor score profesional."""
    if not candidatos:
        logger.info("No hay candidatos.")
        return None

    aptos = [candidato for candidato in candidatos if candidato.score and candidato.score.gates_pasados]
    if not aptos:
        logger.info("Ningún candidato pasó gates.")
        for candidato in candidatos:
            if candidato.score:
                logger.debug(
                    "Candidato descartado: lado=%s cuota=%s explicacion=%s",
                    candidato.lado.value,
                    candidato.cuota,
                    candidato.score.explicacion,
                )
            else:
                logger.debug(
                    "Candidato descartado: lado=%s cuota=%s explicacion=sin_score",
                    candidato.lado.value,
                    candidato.cuota,
                )
        return None

    def clave_orden(candidato: CandidatoApuesta) -> tuple:
        ev = candidato.ev if candidato.ev is not None else float("-inf")
        edge = candidato.edge_real if candidato.edge_real is not None else float("-inf")
        prob = candidato.probabilidad if candidato.probabilidad is not None else float("-inf")
        cuota = candidato.cuota if candidato.cuota is not None else float("-inf")
        return (
            candidato.score.score_total,
            ev,
            edge,
            prob,
            cuota,
            candidato.mercado.value,
            candidato.lado.value,
            candidato.linea,
        )

    return max(aptos, key=clave_orden)


def determinar_confianza(
    desviacion_total: float,
    probabilidad: Optional[float] = None,
    distancia_z: Optional[float] = None,
) -> FactoresConfianza:
    """Determina factores de confianza con heurística simple."""
    if desviacion_total < 5.5:
        volatilidad = "baja"
        puntaje_volatilidad = 2
    elif desviacion_total < 7.5:
        volatilidad = "moderada"
        puntaje_volatilidad = 1
    else:
        volatilidad = "alta"
        puntaje_volatilidad = 0

    puntaje_probabilidad = 0
    if probabilidad is not None:
        if probabilidad >= 0.70:
            puntaje_probabilidad = 2
        elif probabilidad >= 0.60:
            puntaje_probabilidad = 1

    puntaje_edge = 0
    if distancia_z is not None:
        if distancia_z >= 1.5:
            puntaje_edge = 2
        elif distancia_z >= 1.0:
            puntaje_edge = 1

    tamano_muestra = "moderado"
    frescura = "aceptable"
    puntaje_total = puntaje_volatilidad + puntaje_probabilidad + puntaje_edge

    return FactoresConfianza(
        tamano_muestra=tamano_muestra,
        volatilidad=volatilidad,
        frescura_datos=frescura,
        puntaje_total=puntaje_total,
    )


def _resolver_configuracion_sizing(
    config_sizing_usuario: Optional[Dict[str, Any]],
    bankroll_override: Optional[float],
    perfil_override: Optional[PerfilRiesgo | str],
    bankroll_usuario: Optional[float],
    perfil_default: Optional[PerfilRiesgo | str],
) -> Optional[ConfiguracionSizing]:
    bankroll = bankroll_override if bankroll_override is not None else bankroll_usuario
    if bankroll is None:
        return None

    return ConfiguracionSizing.construir_desde_fuentes(
        config_sizing_usuario=config_sizing_usuario,
        bankroll_override=bankroll,
        perfil_override=perfil_override,
        bankroll_usuario=bankroll_usuario,
        perfil_default=perfil_default,
    )


def analizar_partido(
    modelo: ModeloRidge,
    equipo: str,
    rival: str,
    ubicacion: Ubicacion,
    mercado: str,
    linea: Optional[float] = None,
    cuota: Optional[float] = None,
    cuota_over: Optional[float] = None,
    cuota_under: Optional[float] = None,
    cuota_ganador_equipo: Optional[float] = None,
    cuota_ganador_rival: Optional[float] = None,
    lado: LadoApuesta | str = LadoApuesta.OVER,
    modo_devig: str = "estricto",
    bankroll_override: Optional[float] = None,
    perfil_riesgo_override: Optional[str] = None,
    usuario_config: Optional[Dict[str, Any]] = None,
    config_sizing: Optional[ConfiguracionSizing] = None,
    marcador_q1: Optional[str] = None,
    marcador_q2: Optional[str] = None,
    marcador_q3: Optional[str] = None,
    peso_en_vivo: float = 0.5,
    fecha_partido: Optional[date] = None,
    origen_prediccion: str = "API_USUARIO",
    calibrador_activo: Optional[object] = None,
    incluir_contexto: bool = True,
    h2h_limite: int = 10,
) -> ResultadoAnalisis:
    """Ejecuta el análisis completo para un partido."""
    media_equipo, desviacion_equipo, media_rival, desviacion_rival = predecir_cuartos(
        modelo,
        equipo,
        rival,
        ubicacion,
    )

    es_en_vivo = any([marcador_q1, marcador_q2, marcador_q3])
    cuartos_reales: Dict[str, Tuple[float, float]] = {}
    metadata: Dict[str, object] = {"mercado": mercado}

    if es_en_vivo:
        media_equipo, media_rival, cuartos_reales, metadata = aplicar_ajuste_en_vivo(
            media_equipo,
            media_rival,
            parsear_marcador(marcador_q1),
            parsear_marcador(marcador_q2),
            parsear_marcador(marcador_q3),
            peso_en_vivo,
        )
        metadata["mercado"] = mercado

    predicciones: Dict[str, PrediccionCuarto] = {}
    for indice, cuarto in enumerate(CLAVES_CUARTOS):
        linea_cuarto = linea if mercado == cuarto else None
        predicciones[cuarto] = calcular_prediccion_cuarto(
            cuarto,
            float(media_equipo[indice]),
            float(desviacion_equipo[indice]),
            float(media_rival[indice]),
            float(desviacion_rival[indice]),
            linea=linea_cuarto,
        )

    prediccion_juego_completo = None
    if mercado == "COMPLETO":
        media_total = float(np.sum(media_equipo) + np.sum(media_rival))
        desviacion_total = float(np.sqrt(np.sum(desviacion_equipo ** 2) + np.sum(desviacion_rival ** 2)))
        prediccion_juego_completo = calcular_prediccion_cuarto(
            "COMPLETO",
            float(np.sum(media_equipo)),
            float(np.sqrt(np.sum(desviacion_equipo ** 2))),
            float(np.sum(media_rival)),
            float(np.sqrt(np.sum(desviacion_rival ** 2))),
            linea=linea,
        )

        if prediccion_juego_completo is not None and cuota_ganador_equipo is not None:
            try:
                datos_devig_ganador = calcular_devig(
                    cuota_ganador_equipo,
                    cuota_ganador_rival,
                    modo_estimado=cuota_ganador_rival is None,
                )
                p_modelo_ganador = float(prediccion_juego_completo.probabilidad_ganador)
                p_mercado_ganador = float(datos_devig_ganador.p_mkt_fair)
                p_blend_ganador = limitar_entre_0_y_1(
                    PESO_MODELO_GANADOR * p_modelo_ganador
                    + PESO_MERCADO_GANADOR * p_mercado_ganador
                )
                prediccion_juego_completo.probabilidad_ganador = p_blend_ganador
                prediccion_juego_completo.ganador_probable = (
                    "equipo" if p_blend_ganador >= 0.5 else "rival"
                )
                metadata["blend_ganador"] = {
                    "aplicado": True,
                    "peso_modelo": PESO_MODELO_GANADOR,
                    "peso_mercado": PESO_MERCADO_GANADOR,
                    "p_modelo": p_modelo_ganador,
                    "p_mercado": p_mercado_ganador,
                    "p_final": p_blend_ganador,
                    "metodo_devig": datos_devig_ganador.metodo,
                    "overround": datos_devig_ganador.overround,
                }
            except Exception as exc:
                logger.warning("No se pudo aplicar blend de ganador: %s", exc)
                metadata["blend_ganador"] = {"aplicado": False, "motivo": str(exc)}
    else:
        cuarto_predicho = predicciones[mercado]

    prediccion_referencia = prediccion_juego_completo if mercado == "COMPLETO" and prediccion_juego_completo else predicciones.get(mercado)
    razones = generar_razones_basicas(
        nombre_equipo=equipo,
        nombre_rival=rival,
        media_equipo=prediccion_referencia.media_equipo if prediccion_referencia else float(np.mean(media_equipo)),
        media_rival=prediccion_referencia.media_rival if prediccion_referencia else float(np.mean(media_rival)),
        media_total=prediccion_referencia.media_total if prediccion_referencia else float(np.mean(media_equipo + media_rival)),
        mercado=mercado,
        ganador_probable=prediccion_referencia.ganador_probable if prediccion_referencia else None,
        probabilidad_ganador=prediccion_referencia.probabilidad_ganador if prediccion_referencia else None,
    )

    analisis_mercado = None
    if calibrador_activo is None:
        calibrador_activo = obtener_calibrador_activo(
            mercado=mercado,
            origen=origen_prediccion,
            fecha_partido=fecha_partido,
        )
    sizing: Optional[ResultadoSizing] = None
    datos_devig = None
    probabilidad_lado = None
    try:
        lado_enum = lado if isinstance(lado, LadoApuesta) else LadoApuesta(lado)
    except ValueError:
        raise ValueError("lado debe ser OVER o UNDER.")

    if cuota_over is None and cuota_under is None and cuota is not None:
        if lado_enum == LadoApuesta.UNDER:
            cuota_under = cuota
        else:
            cuota_over = cuota

    cuota_lado = cuota_over if lado_enum == LadoApuesta.OVER else cuota_under
    cuota_opuesta = cuota_under if lado_enum == LadoApuesta.OVER else cuota_over
    modo_devig = str(modo_devig).lower()
    if modo_devig not in ("estimado", "estricto"):
        raise ValueError("modo_devig debe ser 'estimado' o 'estricto'.")
    modo_estimado = modo_devig == "estimado"

    usuario_config = usuario_config or {}
    config_sizing_usuario = usuario_config.get("config_sizing")
    bankroll_usuario = usuario_config.get("bankroll_actual")
    perfil_default = usuario_config.get("perfil_riesgo_default")
    if config_sizing is None:
        config_sizing = _resolver_configuracion_sizing(
            config_sizing_usuario=config_sizing_usuario,
            bankroll_override=bankroll_override,
            perfil_override=perfil_riesgo_override,
            bankroll_usuario=bankroll_usuario,
            perfil_default=perfil_default,
        )
    if config_sizing is not None and config_sizing.bankroll is None:
        config_sizing = None

    if cuota_lado is not None and linea is not None:
        if mercado == "COMPLETO":
            probabilidad_over = prediccion_juego_completo.probabilidad_over if prediccion_juego_completo else 0.0
            probabilidad_under = prediccion_juego_completo.probabilidad_under if prediccion_juego_completo else 0.0
        else:
            prediccion_lado = predicciones[mercado]
            probabilidad_over = prediccion_lado.probabilidad_over or 0.0
            probabilidad_under = prediccion_lado.probabilidad_under or 0.0

        probabilidad_lado = (
            probabilidad_over if lado_enum == LadoApuesta.OVER else probabilidad_under
        )
        probabilidad_calibrada = (
            calibrador_activo.calibrar(probabilidad_lado)
            if calibrador_activo is not None
            else None
        )
        probabilidad_efectiva = (
            probabilidad_calibrada
            if probabilidad_calibrada is not None
            else probabilidad_lado
        )
        datos_devig = calcular_devig(
            cuota_lado,
            cuota_opuesta,
            modo_estimado=modo_estimado,
        )
        analisis_mercado = AnalisisMercado.calcular(
            probabilidad_efectiva,
            cuota_lado,
            datos_devig,
        )

    candidatos: List[CandidatoApuesta] = []
    if linea is not None:
        if mercado == "COMPLETO" and prediccion_juego_completo is not None:
            media_equipo_total = float(np.sum(media_equipo))
            desviacion_equipo_total = float(np.sqrt(np.sum(desviacion_equipo ** 2)))
            media_rival_total = float(np.sum(media_rival))
            desviacion_rival_total = float(np.sqrt(np.sum(desviacion_rival ** 2)))
            candidatos = candidatos_para_cuarto(
                mercado,
                linea,
                media_equipo_total,
                desviacion_equipo_total,
                media_rival_total,
                desviacion_rival_total,
                cuota_over=cuota_over,
                cuota_under=cuota_under,
                modo_devig=modo_devig,
                config_sizing=config_sizing,
                calibrador_activo=calibrador_activo,
            )
        elif mercado in predicciones:
            indice = INDICE_CUARTOS.get(mercado, 0)
            candidatos = candidatos_para_cuarto(
                mercado,
                linea,
                float(media_equipo[indice]),
                float(desviacion_equipo[indice]),
                float(media_rival[indice]),
                float(desviacion_rival[indice]),
                cuota_over=cuota_over,
                cuota_under=cuota_under,
                modo_devig=modo_devig,
                config_sizing=config_sizing,
                calibrador_activo=calibrador_activo,
            )

    mejor_apuesta = seleccionar_mejor_apuesta(candidatos)
    if not candidatos:
        metadata["mensaje_apuesta"] = "NO_APTO: SIN_CANDIDATOS"
    elif mejor_apuesta is None:
        metadata["mensaje_apuesta"] = "NO_APTO: EV<=0 o edge_real<=0 en todos los candidatos"

    if mercado == "COMPLETO" and prediccion_juego_completo is not None:
        probabilidad = None
        distancia_z = None
        if linea is not None:
            probabilidad = max(
                prediccion_juego_completo.probabilidad_over or 0.0,
                prediccion_juego_completo.probabilidad_under or 0.0,
            )
            distancia_z = abs(prediccion_juego_completo.media_total - linea) / max(
                prediccion_juego_completo.desviacion_total, 1e-9
            )
        else:
            probabilidad = prediccion_juego_completo.probabilidad_ganador
        factores_confianza = determinar_confianza(
            prediccion_juego_completo.desviacion_total,
            probabilidad=probabilidad,
            distancia_z=distancia_z,
        )
    else:
        probabilidad = None
        distancia_z = None
        cuarto_predicho = predicciones[mercado]
        if mejor_apuesta is not None:
            probabilidad = mejor_apuesta.probabilidad
            distancia_z = mejor_apuesta.distancia_z
        else:
            probabilidad = cuarto_predicho.probabilidad_ganador
        factores_confianza = determinar_confianza(
            cuarto_predicho.desviacion_total,
            probabilidad=probabilidad,
            distancia_z=distancia_z,
        )

    nivel_confianza = factores_confianza.obtener_nivel()
    riesgo_alto = factores_confianza.volatilidad == "alta"

    if (
        config_sizing is not None
        and analisis_mercado is not None
        and datos_devig is not None
        and probabilidad_lado is not None
        and cuota_lado is not None
    ):
        sizing = calcular_kelly(
            probabilidad=probabilidad_efectiva,
            cuota=cuota_lado,
            config=config_sizing,
            datos_devig=datos_devig,
            riesgo_alto=riesgo_alto,
        )

    contexto = None
    prediccion_ajustada = None
    advertencias_contexto: List[str] = []
    if incluir_contexto:
        try:
            contexto = recolectar_contexto(
                equipo=equipo,
                rival=rival,
                fecha_partido=fecha_partido,
                limite_h2h=h2h_limite,
            )
            if mercado == "COMPLETO" and prediccion_juego_completo is not None:
                prediccion_base = prediccion_juego_completo
            else:
                prediccion_base = predicciones.get(mercado)

            if prediccion_base is not None:
                prediccion_ajustada = aplicar_ajustes_contextuales(
                    contexto=contexto,
                    media_base=prediccion_base.media_total,
                    desviacion_base=prediccion_base.desviacion_total,
                    probabilidad_over_base=prediccion_base.probabilidad_over or 0.0,
                    probabilidad_under_base=prediccion_base.probabilidad_under or 0.0,
                    linea=prediccion_base.linea_analizada,
                    mercado=mercado,
                    confianza_base=nivel_confianza,
                )
                advertencias_contexto = prediccion_ajustada.ajustes_aplicados.advertencias
                razones = generar_razones_ajustes(
                    nombre_equipo=equipo,
                    nombre_rival=rival,
                    mercado=mercado,
                    media_base=prediccion_base.media_total,
                    media_ajustada=prediccion_ajustada.media_ajustada,
                    linea=prediccion_base.linea_analizada,
                    ajustes=prediccion_ajustada.ajustes_aplicados,
                    ganador_probable=prediccion_base.ganador_probable,
                    probabilidad_ganador=prediccion_base.probabilidad_ganador,
                )
        except Exception:
            logger.exception("Error aplicando contexto; se devuelve predicción base.")

    return ResultadoAnalisis(
        equipo=normalizar_nombre(equipo),
        equipo_nombre_completo=equipo,
        rival=normalizar_nombre(rival),
        rival_nombre_completo=rival,
        ubicacion=ubicacion,
        fecha_analisis=datetime.now().isoformat(),
        predicciones=predicciones,
        prediccion_juego_completo=prediccion_juego_completo,
        razones=razones,
        nivel_confianza=nivel_confianza,
        factores_confianza=factores_confianza,
        analisis_mercado=analisis_mercado,
        sizing=sizing,
        mejor_apuesta=mejor_apuesta,
        candidatos=candidatos,
        es_en_vivo=es_en_vivo,
        cuartos_reales=cuartos_reales,
        metadata=metadata,
        contexto=contexto,
        ajustes=prediccion_ajustada.ajustes_aplicados if prediccion_ajustada else None,
        prediccion_ajustada=prediccion_ajustada,
        advertencias_contexto=advertencias_contexto,
    )


def resultado_a_dict(resultado: ResultadoAnalisis) -> Dict[str, object]:
    """Convierte ResultadoAnalisis a diccionario serializable estable."""
    def serializar_prediccion(prediccion: PrediccionCuarto) -> Dict[str, object]:
        return {
            "cuarto": prediccion.cuarto,
            "media_equipo": prediccion.media_equipo,
            "desviacion_equipo": prediccion.desviacion_equipo,
            "rango_equipo": list(prediccion.rango_equipo),
            "media_rival": prediccion.media_rival,
            "desviacion_rival": prediccion.desviacion_rival,
            "rango_rival": list(prediccion.rango_rival),
            "media_total": prediccion.media_total,
            "desviacion_total": prediccion.desviacion_total,
            "rango_total": list(prediccion.rango_total),
            "linea_analizada": prediccion.linea_analizada,
            "probabilidad_over": prediccion.probabilidad_over,
            "probabilidad_under": prediccion.probabilidad_under,
            "ganador_probable": prediccion.ganador_probable,
            "probabilidad_ganador": prediccion.probabilidad_ganador,
        }

    def serializar_score(score: Optional[ScoreApuesta]) -> Dict[str, object]:
        if score is None:
            return {
                "score_total": None,
                "score_componentes": {},
                "score_explicacion": None,
                "score_penalizaciones": [],
            }
        return score.asdict_persistencia()

    def serializar_sizing(sizing: Optional[ResultadoSizing]) -> Dict[str, object]:
        if sizing is None:
            return {
                "kelly_full": None,
                "kelly_fraccional": None,
                "fraccion_kelly": None,
                "stake": None,
                "stake_porcentaje": None,
                "bankroll_momento": None,
                "perfil_riesgo_usado": None,
                "sizing_advertencias": [],
                "sizing_penalizaciones": {},
                "aplicaron_caps": False,
            }
        return sizing.asdict_persistencia()

    def serializar_devig(
        candidato: CandidatoApuesta,
    ) -> Dict[str, object]:
        datos = candidato.datos_devig
        if datos is None:
            return {
                "devig_metodo": None,
                "devig_overround": None,
                "devig_p_mkt_raw": None,
                "devig_p_mkt_fair": None,
                "devig_advertencias": [],
                "edge_raw": None,
            }
        probabilidad_raw = (
            candidato.p_raw
            if candidato.p_raw is not None
            else candidato.probabilidad
        )
        edge_raw = (
            probabilidad_raw - datos.p_mkt_raw
            if probabilidad_raw is not None
            else None
        )
        return {
            "devig_metodo": datos.metodo,
            "devig_overround": datos.overround,
            "devig_p_mkt_raw": datos.p_mkt_raw,
            "devig_p_mkt_fair": datos.p_mkt_fair,
            "devig_advertencias": list(datos.advertencias),
            "edge_raw": edge_raw,
        }

    def serializar_candidato(
        candidato: CandidatoApuesta,
        resumen: bool = False,
    ) -> Dict[str, object]:
        base = {
            "mercado": candidato.cuarto,
            "lado": candidato.lado.value,
            "linea": candidato.linea,
            "cuota": candidato.cuota,
            "probabilidad_sistema": candidato.probabilidad,
            "p_raw": candidato.p_raw,
            "p_calibrada": candidato.p_calibrada,
            "calibrador_usado": candidato.calibrador_usado,
            "edge_real": candidato.edge_real,
            "valor_esperado": candidato.ev,
        }
        if candidato.cuota_over is not None:
            base["cuota_over"] = candidato.cuota_over
        if candidato.cuota_under is not None:
            base["cuota_under"] = candidato.cuota_under

        base.update(serializar_devig(candidato))

        if resumen:
            penalizaciones = (
                candidato.score.penalizaciones_aplicadas if candidato.score else []
            )
            base.update(
                {
                    "score_total": candidato.score.score_total
                    if candidato.score
                    else None,
                    "score_penalizaciones": list(penalizaciones),
                }
            )
            return base

        base.update(
            {
                "prediccion_media": candidato.media,
                "prediccion_desviacion": candidato.desviacion,
                "distancia_z": candidato.distancia_z,
            }
        )
        base.update(serializar_score(candidato.score))
        base.update(serializar_sizing(candidato.sizing))
        return base

    def serializar_razones(razones: List[RazonPrediccion]) -> List[Dict[str, object]]:
        return [asdict(razon) for razon in razones]

    def serializar_contexto(contexto: object) -> Dict[str, object]:
        return asdict(contexto) if contexto is not None else {}

    def serializar_ajustes(ajustes: object) -> Dict[str, object]:
        if ajustes is None:
            return {}
        data = asdict(ajustes)
        data["ajustes"] = [asdict(ajuste) for ajuste in ajustes.ajustes]
        return data

    def serializar_prediccion_ajustada(prediccion: object) -> Dict[str, object]:
        if prediccion is None:
            return {}
        data = asdict(prediccion)
        data["ajustes_aplicados"] = serializar_ajustes(prediccion.ajustes_aplicados)
        return data

    mercado = resultado.metadata.get("mercado") if resultado.metadata else None
    if mercado == "COMPLETO" and resultado.prediccion_juego_completo:
        prediccion_mercado = resultado.prediccion_juego_completo
    elif mercado and mercado in resultado.predicciones:
        prediccion_mercado = resultado.predicciones[mercado]
    else:
        prediccion_mercado = None

    linea = prediccion_mercado.linea_analizada if prediccion_mercado else None
    lado = resultado.mejor_apuesta.lado.value if resultado.mejor_apuesta else None

    advertencias: List[str] = []
    if resultado.analisis_mercado and resultado.analisis_mercado.datos_devig:
        advertencias.extend(resultado.analisis_mercado.datos_devig.advertencias)
    if resultado.mejor_apuesta and resultado.mejor_apuesta.datos_devig:
        advertencias.extend(resultado.mejor_apuesta.datos_devig.advertencias)
    if resultado.mejor_apuesta and resultado.mejor_apuesta.sizing:
        advertencias.extend(resultado.mejor_apuesta.sizing.advertencias)
    advertencias = list(dict.fromkeys(advertencias))

    predicciones = {
        cuarto: serializar_prediccion(prediccion)
        for cuarto, prediccion in resultado.predicciones.items()
    }
    if resultado.prediccion_juego_completo is not None:
        predicciones["COMPLETO"] = serializar_prediccion(resultado.prediccion_juego_completo)

    # Serializar analisis_mercado si existe
    analisis_mercado_dict = None
    if resultado.analisis_mercado is not None:
        am = resultado.analisis_mercado
        analisis_mercado_dict = {
            "cuota": am.cuota,
            "probabilidad_implicita": am.probabilidad_implicita if am.probabilidad_implicita is not None else am.probabilidad_implicita_fair,
            "edge": am.edge if am.edge is not None else am.edge_real,
            "valor_esperado": am.valor_esperado,
            "recomendacion": am.recomendacion.value if hasattr(am.recomendacion, 'value') else am.recomendacion,
        }

    # Extraer probabilidades del mercado si existe
    probabilidad_over = prediccion_mercado.probabilidad_over if prediccion_mercado else None
    probabilidad_under = prediccion_mercado.probabilidad_under if prediccion_mercado else None
    linea_analizada = prediccion_mercado.linea_analizada if prediccion_mercado else None

    # Serializar prediccion_juego_completo por separado para el frontend
    prediccion_juego_completo_dict = None
    if resultado.prediccion_juego_completo is not None:
        prediccion_juego_completo_dict = serializar_prediccion(resultado.prediccion_juego_completo)

    salida: Dict[str, object] = {
        # Campos legacy (mantener compatibilidad)
        "equipo_local": resultado.equipo_nombre_completo,
        "equipo_visitante": resultado.rival_nombre_completo,
        "prediccion": predicciones,
        "confianza_sistema": resultado.nivel_confianza.value,
        # Campos nuevos que espera el frontend
        "equipo": resultado.equipo,
        "equipo_nombre_completo": resultado.equipo_nombre_completo,
        "rival": resultado.rival,
        "rival_nombre_completo": resultado.rival_nombre_completo,
        "ubicacion": resultado.ubicacion.value if hasattr(resultado.ubicacion, 'value') else resultado.ubicacion,
        "fecha_analisis": resultado.fecha_analisis if resultado.fecha_analisis else None,
        "predicciones": predicciones,  # El frontend usa plural
        "prediccion_juego_completo": prediccion_juego_completo_dict,
        "nivel_confianza": resultado.nivel_confianza.value,  # El frontend usa este nombre
        "mercado": mercado,
        "linea": linea,
        "lado": lado,
        "factores_confianza": resultado.factores_confianza.como_diccionario()
        if resultado.factores_confianza
        else None,
        "razones": serializar_razones(resultado.razones),
        "es_en_vivo": resultado.es_en_vivo,
        "cuartos_reales": resultado.cuartos_reales,
        "analisis_mercado": analisis_mercado_dict,
        "metadata": resultado.metadata or {},
        "probabilidad_over": probabilidad_over,
        "probabilidad_under": probabilidad_under,
        "linea_analizada": linea_analizada,
    }

    if resultado.contexto is not None:
        salida["contexto"] = serializar_contexto(resultado.contexto)
    if resultado.ajustes is not None:
        salida["ajustes"] = serializar_ajustes(resultado.ajustes)
    if resultado.prediccion_ajustada is not None:
        salida["prediccion_ajustada"] = serializar_prediccion_ajustada(
            resultado.prediccion_ajustada
        )
        if prediccion_mercado is not None:
            salida["prediccion_base"] = {
                "media": prediccion_mercado.media_total,
                "desviacion": prediccion_mercado.desviacion_total,
                "probabilidad_over": prediccion_mercado.probabilidad_over,
                "probabilidad_under": prediccion_mercado.probabilidad_under,
            }
            salida["comparacion"] = {
                "cambio_media": resultado.prediccion_ajustada.media_ajustada
                - prediccion_mercado.media_total,
                "cambio_prob_over": resultado.prediccion_ajustada.probabilidad_over_ajustada
                - (prediccion_mercado.probabilidad_over or 0.0),
                "cambio_prob_under": resultado.prediccion_ajustada.probabilidad_under_ajustada
                - (prediccion_mercado.probabilidad_under or 0.0),
            }
    if resultado.advertencias_contexto:
        salida["advertencias_contexto"] = list(resultado.advertencias_contexto)

    if resultado.mejor_apuesta is not None:
        salida["mejor_apuesta"] = serializar_candidato(resultado.mejor_apuesta)
    else:
        salida["mejor_apuesta"] = None

    salida["candidatos"] = [
        serializar_candidato(candidato, resumen=True)
        for candidato in resultado.candidatos
    ]

    if resultado.metadata and resultado.metadata.get("mensaje_apuesta"):
        salida["mensaje_apuesta"] = resultado.metadata["mensaje_apuesta"]

    return salida
