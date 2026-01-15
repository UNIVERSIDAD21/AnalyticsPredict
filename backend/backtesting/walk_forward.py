from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Generator, Iterable, Sequence

from .configuracion import ConfiguracionBacktest, ModoCutoff, ModoVentana


@dataclass(frozen=True)
class IteracionWalkForward:
    cutoff_date: date
    partidos_entrenamiento: list[dict[str, Any]]
    partidos_a_predecir: list[dict[str, Any]]
    metadata: dict[str, Any]


def iterar_walk_forward(
    partidos: Sequence[dict[str, Any]],
    config: ConfiguracionBacktest,
    logger: logging.Logger | None = None,
) -> Generator[IteracionWalkForward, None, None]:
    logger = logger or logging.getLogger(__name__)
    fecha_fin = config.fecha_fin or date.today()

    partidos_filtrados = [
        partido
        for partido in partidos
        if _get_fecha(partido) >= config.fecha_inicio and _get_fecha(partido) <= fecha_fin
    ]

    partidos_filtrados.sort(key=_get_fecha)

    if config.modo_cutoff == ModoCutoff.POR_BLOQUE:
        yield from _iterar_por_bloque(partidos_filtrados, config, logger)
        return

    corte = config.fecha_inicio
    delta = timedelta(days=1) if config.modo_cutoff == ModoCutoff.DIARIO else timedelta(days=7)

    while corte <= fecha_fin:
        siguiente_corte = corte + delta
        iteracion = _construir_iteracion(
            partidos_filtrados,
            corte,
            siguiente_corte,
            config,
            logger,
        )
        if iteracion:
            yield iteracion
        corte = siguiente_corte


def _iterar_por_bloque(
    partidos: Sequence[dict[str, Any]],
    config: ConfiguracionBacktest,
    logger: logging.Logger,
) -> Generator[IteracionWalkForward, None, None]:
    if not partidos:
        return

    tamano = config.tamano_bloque or 0
    bloques = [
        partidos[indice : indice + tamano] for indice in range(0, len(partidos), tamano)
    ]

    for indice, bloque in enumerate(bloques):
        if not bloque:
            continue
        cutoff_date = _get_fecha(bloque[0])
        siguiente_cutoff = _get_fecha(bloques[indice + 1][0]) if indice + 1 < len(bloques) else None
        iteracion = _construir_iteracion(
            partidos,
            cutoff_date,
            siguiente_cutoff,
            config,
            logger,
            bloque_prediccion=bloque,
        )
        if iteracion:
            yield iteracion


def _construir_iteracion(
    partidos: Sequence[dict[str, Any]],
    cutoff_date: date,
    siguiente_cutoff: date | None,
    config: ConfiguracionBacktest,
    logger: logging.Logger,
    bloque_prediccion: Sequence[dict[str, Any]] | None = None,
) -> IteracionWalkForward | None:
    partidos_entrenamiento = [
        partido for partido in partidos if _get_fecha(partido) < cutoff_date
    ]

    excluidos_pretemporada = 0
    if config.excluir_pretemporada:
        filtrados = []
        for partido in partidos_entrenamiento:
            if _es_pretemporada(partido):
                excluidos_pretemporada += 1
                continue
            filtrados.append(partido)
        partidos_entrenamiento = filtrados

    partidos_entrenamiento = _aplicar_ventana(partidos_entrenamiento, config)

    if bloque_prediccion is not None:
        partidos_a_predecir = list(bloque_prediccion)
    else:
        partidos_a_predecir = [
            partido
            for partido in partidos
            if _get_fecha(partido) >= cutoff_date
            and (siguiente_cutoff is None or _get_fecha(partido) < siguiente_cutoff)
        ]

    if not partidos_a_predecir:
        logger.warning(
            "Iteración sin partidos a predecir para cutoff %s. Se omite.", cutoff_date
        )
        return None

    temporadas_historia = _contar_temporadas(partidos_entrenamiento)
    if temporadas_historia < config.min_temporadas_historia:
        logger.warning(
            "Skip cutoff %s: historia insuficiente (%s temporadas, mínimo %s).",
            cutoff_date,
            temporadas_historia,
            config.min_temporadas_historia,
        )
        return None

    if len(partidos_entrenamiento) < config.min_partidos_entrenamiento:
        logger.warning(
            "Skip cutoff %s: entrenamiento insuficiente (%s partidos, mínimo %s).",
            cutoff_date,
            len(partidos_entrenamiento),
            config.min_partidos_entrenamiento,
        )
        return None

    metadata = _construir_metadata(
        cutoff_date,
        partidos_entrenamiento,
        partidos_a_predecir,
        config,
        excluidos_pretemporada,
    )

    logger.info(
        "Iteración cutoff=%s entrenamiento=%s prediccion=%s",
        cutoff_date,
        metadata["n_entrenamiento"],
        metadata["n_prediccion"],
    )

    return IteracionWalkForward(
        cutoff_date=cutoff_date,
        partidos_entrenamiento=partidos_entrenamiento,
        partidos_a_predecir=partidos_a_predecir,
        metadata=metadata,
    )


def _aplicar_ventana(
    partidos_entrenamiento: Sequence[dict[str, Any]],
    config: ConfiguracionBacktest,
) -> list[dict[str, Any]]:
    if config.modo_ventana == ModoVentana.TODAS_TEMPORADAS:
        return list(partidos_entrenamiento)

    if config.modo_ventana == ModoVentana.ULTIMAS_N_TEMPORADAS:
        temporadas = sorted({_get_temporada(partido) for partido in partidos_entrenamiento if _get_temporada(partido) is not None})
        if not temporadas:
            return []
        ultimas = set(temporadas[-(config.n_temporadas or 0) :])
        return [
            partido
            for partido in partidos_entrenamiento
            if _get_temporada(partido) in ultimas
        ]

    if config.modo_ventana == ModoVentana.ULTIMOS_N_PARTIDOS:
        return _filtrar_ultimos_partidos(partidos_entrenamiento, config.n_partidos_por_equipo or 0)

    return list(partidos_entrenamiento)


def _filtrar_ultimos_partidos(
    partidos_entrenamiento: Sequence[dict[str, Any]],
    n_partidos_por_equipo: int,
) -> list[dict[str, Any]]:
    partidos_ordenados = sorted(partidos_entrenamiento, key=_get_fecha, reverse=True)
    contador: dict[Any, int] = {}
    seleccionados = []

    for partido in partidos_ordenados:
        equipo_local = _get_equipo(partido, "equipo_local_id")
        equipo_visitante = _get_equipo(partido, "equipo_visitante_id")
        if equipo_local is None or equipo_visitante is None:
            raise ValueError("equipo_local_id y equipo_visitante_id son requeridos")

        if contador.get(equipo_local, 0) >= n_partidos_por_equipo:
            continue
        if contador.get(equipo_visitante, 0) >= n_partidos_por_equipo:
            continue

        seleccionados.append(partido)
        contador[equipo_local] = contador.get(equipo_local, 0) + 1
        contador[equipo_visitante] = contador.get(equipo_visitante, 0) + 1

    return list(reversed(seleccionados))


def _construir_metadata(
    cutoff_date: date,
    partidos_entrenamiento: Sequence[dict[str, Any]],
    partidos_a_predecir: Sequence[dict[str, Any]],
    config: ConfiguracionBacktest,
    excluidos_pretemporada: int,
) -> dict[str, Any]:
    return {
        "cutoff_date": cutoff_date,
        "n_entrenamiento": len(partidos_entrenamiento),
        "n_prediccion": len(partidos_a_predecir),
        "fecha_min_entrenamiento": _min_fecha(partidos_entrenamiento),
        "fecha_max_entrenamiento": _max_fecha(partidos_entrenamiento),
        "fecha_min_prediccion": _min_fecha(partidos_a_predecir),
        "fecha_max_prediccion": _max_fecha(partidos_a_predecir),
        "modo_cutoff": config.modo_cutoff,
        "modo_ventana": config.modo_ventana,
        "excluyo_pretemporada": config.excluir_pretemporada,
        "partidos_excluidos_pretemporada": excluidos_pretemporada,
    }


def _min_fecha(partidos: Sequence[dict[str, Any]]) -> date | None:
    if not partidos:
        return None
    return min(_get_fecha(partido) for partido in partidos)


def _max_fecha(partidos: Sequence[dict[str, Any]]) -> date | None:
    if not partidos:
        return None
    return max(_get_fecha(partido) for partido in partidos)


def _contar_temporadas(partidos: Sequence[dict[str, Any]]) -> int:
    temporadas = {_get_temporada(partido) for partido in partidos if _get_temporada(partido) is not None}
    return len(temporadas)


def _get_fecha(partido: dict[str, Any]) -> date:
    fecha = partido.get("fecha_partido")
    if not isinstance(fecha, date):
        raise ValueError("fecha_partido es obligatoria y debe ser date")
    return fecha


def _get_temporada(partido: dict[str, Any]) -> Any:
    return partido.get("temporada_id", partido.get("temporada"))


def _get_equipo(partido: dict[str, Any], clave: str) -> Any:
    return partido.get(clave)


def _es_pretemporada(partido: dict[str, Any]) -> bool:
    return partido.get("tipo_partido") == "PRE"
