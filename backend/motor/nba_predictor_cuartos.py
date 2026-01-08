# -*- coding: utf-8 -*-
"""
nba_predictor_cuartos.py — Motor de predicción por cuartos.

Este módulo expone funciones para cargar el modelo y generar predicciones
por cuarto o juego completo, incluyendo probabilidades y recomendaciones.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import json
import numpy as np

from .calculadora_probabilidad import (
    calcular_intervalo_confianza,
    calcular_kelly,
    calcular_devig,
    calcular_probabilidad_over,
    calcular_probabilidad_victoria,
)
from .generador_razones import generar_razones_basicas
from .tipos import (
    AnalisisMercado,
    CandidatoApuesta,
    ConfiguracionSizing,
    FactoresConfianza,
    LadoApuesta,
    ModeloRidge,
    NivelConfianza,
    PrediccionCuarto,
    ResultadoAnalisis,
    ResultadoSizing,
    TipoMercado,
    Ubicacion,
)
from .utilidades import (
    limitar_entre_0_y_1,
    normalizar_nombre,
    parsear_marcador,
    resolver_nombre_en_modelo,
)

CLAVES_CUARTOS = ("Q1", "Q2", "Q3", "Q4")
INDICE_CUARTOS = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3}


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

    probabilidad_ganador = calcular_probabilidad_victoria(
        media_equipo,
        desviacion_equipo,
        media_rival,
        desviacion_rival,
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
) -> List[CandidatoApuesta]:
    """Genera candidatos de apuesta para un cuarto específico."""
    candidatos: List[CandidatoApuesta] = []
    media_total = media_equipo + media_rival
    desviacion_total = float(np.sqrt(desviacion_equipo ** 2 + desviacion_rival ** 2))

    prob_over_total = calcular_probabilidad_over(media_total, desviacion_total, linea)
    distancia_z_total = abs(media_total - linea) / max(desviacion_total, 1e-9)

    candidatos.append(
        CandidatoApuesta(
            cuarto=cuarto,
            mercado=TipoMercado.TOTAL,
            lado=LadoApuesta.OVER,
            linea=linea,
            probabilidad=prob_over_total,
            media=media_total,
            desviacion=desviacion_total,
            distancia_z=distancia_z_total,
        )
    )
    candidatos.append(
        CandidatoApuesta(
            cuarto=cuarto,
            mercado=TipoMercado.TOTAL,
            lado=LadoApuesta.UNDER,
            linea=linea,
            probabilidad=1.0 - prob_over_total,
            media=media_total,
            desviacion=desviacion_total,
            distancia_z=distancia_z_total,
        )
    )

    return candidatos


def seleccionar_mejor_apuesta(candidatos: List[CandidatoApuesta]) -> Optional[CandidatoApuesta]:
    """Selecciona el candidato con mayor probabilidad."""
    if not candidatos:
        return None
    return max(candidatos, key=lambda c: c.probabilidad)


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
    lado: LadoApuesta | str = LadoApuesta.OVER,
    modo_devig: str = "estricto",
    config_sizing: Optional[ConfiguracionSizing] = None,
    modo_devig_estimado: Optional[bool] = None,
    marcador_q1: Optional[str] = None,
    marcador_q2: Optional[str] = None,
    marcador_q3: Optional[str] = None,
    peso_en_vivo: float = 0.5,
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
    else:
        cuarto_predicho = predicciones[mercado]

    razones = generar_razones_basicas(
        nombre_equipo=equipo,
        nombre_rival=rival,
        media_equipo=predicciones[mercado].media_equipo
        if mercado in predicciones else float(np.mean(media_equipo)),
        media_rival=predicciones[mercado].media_rival
        if mercado in predicciones else float(np.mean(media_rival)),
        media_total=predicciones[mercado].media_total
        if mercado in predicciones else float(np.mean(media_equipo + media_rival)),
    )

    analisis_mercado = None
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
    if modo_devig not in ("estimado", "estricto"):
        raise ValueError("modo_devig debe ser 'estimado' o 'estricto'.")
    modo_estimado = modo_devig_estimado if modo_devig_estimado is not None else modo_devig == "estimado"

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
        datos_devig = calcular_devig(
            cuota_lado,
            cuota_opuesta,
            modo_estimado=modo_estimado,
        )
        analisis_mercado = AnalisisMercado.calcular(
            probabilidad_lado,
            cuota_lado,
            datos_devig,
        )

    candidatos = []
    if linea is not None and mercado in predicciones:
        indice = INDICE_CUARTOS.get(mercado, 0)
        candidatos = candidatos_para_cuarto(
            mercado,
            linea,
            float(media_equipo[indice]),
            float(desviacion_equipo[indice]),
            float(media_rival[indice]),
            float(desviacion_rival[indice]),
        )

    mejor_apuesta = seleccionar_mejor_apuesta(candidatos)

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
            probabilidad=probabilidad_lado,
            cuota=cuota_lado,
            config=config_sizing,
            datos_devig=datos_devig,
            riesgo_alto=riesgo_alto,
        )

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
        es_en_vivo=es_en_vivo,
        cuartos_reales=cuartos_reales,
        metadata=metadata,
    )


def resultado_a_dict(resultado: ResultadoAnalisis) -> Dict[str, object]:
    """Convierte ResultadoAnalisis a diccionario serializable."""
    def convertir(objeto):
        if hasattr(objeto, "__dict__"):
            return asdict(objeto)
        return objeto

    salida = asdict(resultado)
    salida["nivel_confianza"] = resultado.nivel_confianza.value
    salida["ubicacion"] = resultado.ubicacion.value
    if resultado.analisis_mercado:
        salida["analisis_mercado"]["recomendacion"] = resultado.analisis_mercado.recomendacion.value
    if resultado.mejor_apuesta:
        salida["mejor_apuesta"]["mercado"] = resultado.mejor_apuesta.mercado.value
        salida["mejor_apuesta"]["lado"] = resultado.mejor_apuesta.lado.value
    if resultado.prediccion_juego_completo:
        salida["prediccion_juego_completo"]["ganador_probable"] = (
            "equipo" if resultado.prediccion_juego_completo.probabilidad_ganador >= 0.5 else "rival"
        )
    salida["predicciones"] = {
        cuarto: convertir(prediccion) for cuarto, prediccion in resultado.predicciones.items()
    }
    mercado = resultado.metadata.get("mercado") if resultado.metadata else None
    if mercado == "COMPLETO" and resultado.prediccion_juego_completo:
        prediccion = resultado.prediccion_juego_completo
        salida["probabilidad_over"] = prediccion.probabilidad_over
        salida["probabilidad_under"] = prediccion.probabilidad_under
        salida["linea_analizada"] = prediccion.linea_analizada
    elif mercado and mercado in resultado.predicciones:
        prediccion = resultado.predicciones[mercado]
        salida["probabilidad_over"] = prediccion.probabilidad_over
        salida["probabilidad_under"] = prediccion.probabilidad_under
        salida["linea_analizada"] = prediccion.linea_analizada
    return salida
