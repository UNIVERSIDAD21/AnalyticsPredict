from __future__ import annotations

from datetime import date
from typing import Any, Callable, Dict, List, Optional


def inferir_anio_fin_temporada(fecha_evento: date, tipo_partido: str) -> int:
    mes = int(fecha_evento.month)
    anio = int(fecha_evento.year)
    if mes >= 10:
        return anio + 1
    return anio


def registrar_advertencia_temporada(
    warnings: List[Dict[str, Any]],
    event_id: str,
    equipo: str,
    causa: str,
    detalle: Dict[str, Any],
    verbose: bool = False,
) -> None:
    warning = {
        "event_id": str(event_id),
        "equipo": str(equipo),
        "causa": str(causa),
        "detalle": detalle,
    }
    warnings.append(warning)
    if verbose:
        print(f"   ⚠️  Temporada: {causa} | event_id={event_id} | equipo={equipo} | detalle={detalle}", flush=True)


def resolver_temporada_id_evento(
    conexion,
    fecha_evento: date,
    season_api: Optional[int],
    tipo_partido: str,
    temporada_por_anio_fin: Dict[int, str],
    warnings: List[Dict[str, Any]],
    event_id: str,
    equipo: str,
    asegurar_temporadas_fn: Callable[[Any, List[int]], Dict[int, str]],
    verbose: bool = False,
) -> Optional[str]:
    candidatos: List[int] = []

    if season_api is not None:
        candidatos.append(int(season_api))

    inferida = inferir_anio_fin_temporada(fecha_evento, tipo_partido)
    if season_api is not None and int(season_api) != inferida:
        registrar_advertencia_temporada(
            warnings=warnings,
            event_id=event_id,
            equipo=equipo,
            causa="season_api_difiere_de_fecha",
            detalle={
                "season_api": int(season_api),
                "temporada_inferida": inferida,
                "tipo_partido": tipo_partido,
                "fecha_evento": str(fecha_evento),
            },
            verbose=verbose,
        )

    if inferida not in candidatos:
        candidatos.append(inferida)

    for candidato in candidatos:
        temporada_id = temporada_por_anio_fin.get(int(candidato))
        if temporada_id:
            return str(temporada_id)

        creada = asegurar_temporadas_fn(conexion, [int(candidato)]).get(int(candidato))
        if creada:
            temporada_por_anio_fin[int(candidato)] = str(creada)
            return str(creada)

    registrar_advertencia_temporada(
        warnings=warnings,
        event_id=event_id,
        equipo=equipo,
        causa="temporada_no_resuelta",
        detalle={
            "season_api": season_api,
            "temporada_inferida": inferida,
            "tipo_partido": tipo_partido,
            "fecha_evento": str(fecha_evento),
        },
        verbose=verbose,
    )
    return None
