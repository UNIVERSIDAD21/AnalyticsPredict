"""Resolución conservadora y trazable de estadísticas nulas multi-fuente.

Normaliza evidencia capturada, valida identidad de partido y produce un plan
campo-a-campo. La red queda fuera de este módulo. No deduce valores, no convierte
ausencia en cero y nunca reemplaza datos canónicos no nulos. La única aplicación
SQL requiere llamada explícita, transacción activa y revalidación bajo bloqueo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping


FUENTES_PERMITIDAS = frozenset({"PITCHAPI", "ESPN_SOCCER", "SOFASCORE", "THESTATSAPI"})
CAMPOS_RECUPERABLES = frozenset(
    {
        "local_goles_1t", "local_goles_2t", "local_goles_et",
        "visitante_goles_1t", "visitante_goles_2t", "visitante_goles_et",
        "local_penales", "visitante_penales",
        "local_corners_total",
        "visitante_corners_total",
        "local_corners_1t",
        "visitante_corners_1t",
        "local_corners_2t",
        "visitante_corners_2t",
        "local_disparos_total",
        "visitante_disparos_total",
        "local_disparos_arco",
        "visitante_disparos_arco",
        "local_disparos_fuera", "visitante_disparos_fuera",
        "local_disparos_bloqueados", "visitante_disparos_bloqueados",
        "local_posesion", "visitante_posesion",
        "local_faltas", "visitante_faltas",
        "local_tarjetas_amarillas", "visitante_tarjetas_amarillas",
        "local_tarjetas_rojas", "visitante_tarjetas_rojas",
        "local_fueras_juego", "visitante_fueras_juego",
        "local_xg", "visitante_xg", "local_xg_1t", "visitante_xg_1t",
    }
)
_CAMPOS_DECIMALES = frozenset({
    "local_posesion", "visitante_posesion", "local_xg", "visitante_xg",
    "local_xg_1t", "visitante_xg_1t",
})
_CAMPOS_ENTEROS = CAMPOS_RECUPERABLES - _CAMPOS_DECIMALES
_ENTERO = re.compile(r"^(?:0|[1-9][0-9]*)$")
_CONTRATO = re.compile(r"^[A-Z0-9_]{3,80}$")
_PERIODOS = frozenset({"All", "FirstHalf", "SecondHalf", "ExtraTime"})
MAPEO_METRICAS_PITCHAPI = {
    ("shots", "All"): ("local_disparos_total", "visitante_disparos_total"),
    ("BallPossesion", "All"): ("local_posesion", "visitante_posesion"),
}


class EvidenciaNoValida(ValueError):
    """La identidad o el contenido no acredita el campo propuesto."""


class ConflictoConcurrente(EvidenciaNoValida):
    """El estado canónico cambió desde la construcción del plan."""


@dataclass(frozen=True)
class PartidoCanonico:
    partido_id: str
    competicion_id: str
    equipo_local_id: str
    equipo_visitante_id: str
    inicio_utc: datetime
    estado: str
    goles_local: int | None
    goles_visitante: int | None


@dataclass(frozen=True)
class PartidoProveedor:
    fuente: str
    evento_id: str
    competicion_id: str
    equipo_local_id: str
    equipo_visitante_id: str
    inicio_utc: datetime
    estado: str
    goles_local: int | None
    goles_visitante: int | None


@dataclass(frozen=True)
class EvidenciaCampo:
    campo: str
    valor: int | Decimal
    fuente: str
    evento_id: str
    clave_proveedor: str
    periodo_proveedor: str
    sha256_payload: str
    observado_en: datetime
    contrato: str = "MULTIFUENTE_CAMPO_V1"


@dataclass(frozen=True)
class PlanResolucion:
    actualizaciones: Mapping[str, int | Decimal]
    procedencia: Mapping[str, tuple[EvidenciaCampo, ...]]
    preservados: tuple[str, ...]
    conflictos: Mapping[str, str]


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise EvidenciaNoValida("Fecha debe incluir zona horaria")
    return value.astimezone(timezone.utc)


def sha256_json(payload: Mapping[str, Any]) -> str:
    contenido = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(contenido.encode("utf-8")).hexdigest()


def validar_vinculo_partido(
    canonico: PartidoCanonico,
    proveedor: PartidoProveedor,
    *,
    mapeo_competiciones: Mapping[tuple[str, str], str],
    mapeo_equipos: Mapping[tuple[str, str], str],
    tolerancia_inicio: timedelta = timedelta(minutes=2),
) -> None:
    """Exige IDs externos mapeados y conciliación exacta de la identidad deportiva.

    Los nombres visibles no forman parte de la función: no se hace fuzzy matching.
    Un ID de evento preexistente tampoco basta si contradice equipos, fecha o FT.
    """
    fuente = proveedor.fuente.upper()
    if fuente not in FUENTES_PERMITIDAS:
        raise EvidenciaNoValida("Fuente no habilitada para esta resolución")
    if not proveedor.evento_id:
        raise EvidenciaNoValida("ID de evento externo ausente")
    if mapeo_competiciones.get((fuente, proveedor.competicion_id)) != canonico.competicion_id:
        raise EvidenciaNoValida("Competición externa sin mapeo exacto al catálogo canónico")
    if mapeo_equipos.get((fuente, proveedor.equipo_local_id)) != canonico.equipo_local_id:
        raise EvidenciaNoValida("Equipo local externo sin mapeo exacto")
    if mapeo_equipos.get((fuente, proveedor.equipo_visitante_id)) != canonico.equipo_visitante_id:
        raise EvidenciaNoValida("Equipo visitante externo sin mapeo exacto")
    if canonico.estado != "FINALIZADO" or proveedor.estado.lower() not in {"finished", "final", "full_time", "ft"}:
        raise EvidenciaNoValida("Ambos registros deben estar finalizados")
    if canonico.goles_local is None or canonico.goles_visitante is None:
        raise EvidenciaNoValida("El partido canónico no tiene FT para validar identidad")
    if (proveedor.goles_local, proveedor.goles_visitante) != (
        canonico.goles_local,
        canonico.goles_visitante,
    ):
        raise EvidenciaNoValida("El marcador FT del proveedor contradice el canónico")
    if abs(_utc(proveedor.inicio_utc) - _utc(canonico.inicio_utc)) > tolerancia_inicio:
        raise EvidenciaNoValida("Inicio UTC fuera de la tolerancia de identidad")


def vincular_partido_unico(
    candidatos: Iterable[PartidoCanonico],
    proveedor: PartidoProveedor,
    *,
    mapeo_competiciones: Mapping[tuple[str, str], str],
    mapeo_equipos: Mapping[tuple[str, str], str],
    tolerancia_inicio: timedelta = timedelta(minutes=2),
) -> PartidoCanonico:
    """Acepta solo una coincidencia completa; cero o múltiples quedan en revisión."""
    aceptados = []
    for candidato in candidatos:
        try:
            validar_vinculo_partido(
                candidato,
                proveedor,
                mapeo_competiciones=mapeo_competiciones,
                mapeo_equipos=mapeo_equipos,
                tolerancia_inicio=tolerancia_inicio,
            )
        except EvidenciaNoValida:
            continue
        aceptados.append(candidato)
    if not aceptados:
        raise EvidenciaNoValida("No hay un partido canónico que concilie con la fuente")
    if len(aceptados) != 1:
        raise EvidenciaNoValida("Vínculo externo ambiguo: más de un partido concilia")
    return aceptados[0]


def _leer_entero_observado(value: Any, format_type: Any) -> int:
    """Solo acepta enteros explícitos; porcentajes, floats y null no se reinterpretan."""
    if format_type not in ("integer", ""):
        raise EvidenciaNoValida("Formato de métrica no es entero simple")
    if isinstance(value, bool) or isinstance(value, int):
        if isinstance(value, bool) or value < 0:
            raise EvidenciaNoValida("Conteo inválido")
        return value
    if isinstance(value, str) and _ENTERO.fullmatch(value.strip()):
        return int(value.strip())
    raise EvidenciaNoValida("Valor estadístico ausente o no entero explícito")


def _leer_decimal_observado(value: Any, format_type: Any) -> Decimal:
    """Acepta número decimal simple sin porcentaje, locale ni notación narrativa."""
    if format_type not in {"double", "integer", ""}:
        raise EvidenciaNoValida("Formato de métrica no es decimal simple")
    if isinstance(value, bool) or value is None:
        raise EvidenciaNoValida("Valor decimal ausente o inválido")
    try:
        numero = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise EvidenciaNoValida("Valor decimal no numérico") from None
    if not numero.is_finite() or numero < 0:
        raise EvidenciaNoValida("Valor decimal fuera de dominio")
    return numero


def _leer_valor_campo(campo: str, value: Any, format_type: Any) -> int | Decimal:
    if campo in _CAMPOS_DECIMALES:
        numero = _leer_decimal_observado(value, format_type)
        if campo in {"local_posesion", "visitante_posesion"} and numero > 100:
            raise EvidenciaNoValida("Posesión porcentual fuera del rango 0–100")
        return numero
    return _leer_entero_observado(value, format_type)


def extraer_evidencia_estadistica(
    *,
    fuente: str,
    evento_id: str,
    payload: Mapping[str, Any],
    esperado_local_proveedor_id: str,
    esperado_visitante_proveedor_id: str,
    mapeo_metricas: Mapping[tuple[str, str], tuple[str, str]],
    observado_en: datetime,
    contrato: str = "MULTIFUENTE_CAMPO_V1",
) -> tuple[EvidenciaCampo, ...]:
    """Extrae campos solo con claves/periodos mapeados explícitamente.

    `mapeo_metricas[(clave, periodo)] = (campo_local, campo_visitante)` debe
    provenir de documentación del proveedor o de muestras reales verificadas.
    No hay alias por similitud ni se calculan totales a partir de mitades.
    """
    if not isinstance(fuente, str):
        raise EvidenciaNoValida("Fuente no habilitada para esta resolución")
    fuente = fuente.upper()
    if fuente not in FUENTES_PERMITIDAS:
        raise EvidenciaNoValida("Fuente no habilitada para esta resolución")
    if not isinstance(payload, Mapping) or not isinstance(mapeo_metricas, Mapping):
        raise EvidenciaNoValida("Payload o mapeo de estadísticas inválidos")
    if not isinstance(contrato, str):
        raise EvidenciaNoValida("Identificador de contrato estadístico inválido")
    for spec in mapeo_metricas.values():
        if (not isinstance(spec, (tuple, list)) or len(spec) != 2
                or any(campo not in CAMPOS_RECUPERABLES for campo in spec)):
            raise EvidenciaNoValida("El mapeo contiene columnas no autorizadas")
    _utc(observado_en)
    if not _CONTRATO.fullmatch(contrato):
        raise EvidenciaNoValida("Identificador de contrato estadístico inválido")
    if payload.get("match_id") != evento_id:
        raise EvidenciaNoValida("Las estadísticas pertenecen a otro evento")
    home = payload.get("home_team")
    away = payload.get("away_team")
    if not isinstance(home, Mapping) or not isinstance(away, Mapping):
        raise EvidenciaNoValida("Identidad de lados ausente en respuesta estadística")
    if (str(home.get("id")) != esperado_local_proveedor_id
            or str(away.get("id")) != esperado_visitante_proveedor_id):
        raise EvidenciaNoValida("Orden o identidad de equipos no coincide con el evento validado")
    periodos = payload.get("periods")
    if not isinstance(periodos, list):
        raise EvidenciaNoValida("Lista de periodos ausente")
    payload_hash = sha256_json(payload)
    salida: list[EvidenciaCampo] = []
    vistos: set[tuple[str, str]] = set()
    for periodo in periodos:
        if not isinstance(periodo, Mapping):
            raise EvidenciaNoValida("Periodo con forma inválida")
        nombre_periodo = periodo.get("period")
        if nombre_periodo not in _PERIODOS:
            continue
        groups = periodo.get("groups")
        if not isinstance(groups, list):
            raise EvidenciaNoValida("Grupos estadísticos con forma inválida")
        for group in groups:
            if not isinstance(group, Mapping) or not isinstance(group.get("items"), list):
                raise EvidenciaNoValida("Grupo estadístico con forma inválida")
            for item in group["items"]:
                if not isinstance(item, Mapping):
                    raise EvidenciaNoValida("Ítem estadístico con forma inválida")
                key = item.get("key")
                spec = mapeo_metricas.get((key, nombre_periodo))
                if spec is None:
                    continue
                if (key, nombre_periodo) in vistos:
                    raise EvidenciaNoValida("Métrica repetida para el mismo periodo")
                vistos.add((key, nombre_periodo))
                campo_local, campo_visitante = spec
                if campo_local not in CAMPOS_RECUPERABLES or campo_visitante not in CAMPOS_RECUPERABLES:
                    raise EvidenciaNoValida("El mapeo contiene columnas no autorizadas")
                for lado, campo in (("home", campo_local), ("away", campo_visitante)):
                    bruto = item.get(lado)
                    if bruto is None:
                        continue
                    valor = _leer_valor_campo(campo, bruto, item.get("format_type"))
                    salida.append(
                        EvidenciaCampo(campo, valor, fuente, evento_id, str(key), nombre_periodo,
                                      payload_hash, _utc(observado_en), contrato)
                    )
    return tuple(salida)


def extraer_evidencia_pitchapi_estadistica(
    *,
    evento_id: str,
    payload: Mapping[str, Any],
    esperado_local_proveedor_id: str,
    esperado_visitante_proveedor_id: str,
    observado_en: datetime,
) -> tuple[EvidenciaCampo, ...]:
    """Mapeo verificado contra la documentación oficial pública de PitchAPI.

    `shots` y `BallPossesion` son los únicos campos de la documentación PitchAPI
    mapeados aquí. `shots_on_target` usa una definición que puede contar bloqueos;
    xG es específico de cada modelo y la documentación prohíbe mezclar proveedores.
    Ambos quedan fuera del merge canónico hasta demostrar compatibilidad. Tampoco
    se mapea `is_on_target`, que incluye bloqueos dirigidos al arco.
    """
    return extraer_evidencia_estadistica(
        fuente="PITCHAPI",
        evento_id=evento_id,
        payload=payload,
        esperado_local_proveedor_id=esperado_local_proveedor_id,
        esperado_visitante_proveedor_id=esperado_visitante_proveedor_id,
        mapeo_metricas=MAPEO_METRICAS_PITCHAPI,
        observado_en=observado_en,
        contrato="PITCHAPI_TEAM_STATS_DOCS_2026_10_20_V1",
    )


def extraer_evidencia_espn(
    payload: Mapping[str, Any],
    esperado: Mapping[str, Any],
    *,
    observado_en: datetime,
    mapeo_metricas: Mapping[str, tuple[str, str]] | None = None,
) -> tuple[EvidenciaCampo, ...]:
    """Extrae cada campo ESPN presente tras conciliar evento, lados, fecha y FT.

    ESPN puede devolver un boxscore sin estadísticas. En ese caso retorna una
    tupla vacía; no transforma la ausencia en ceros ni rechaza datos parciales
    que sí estén explícitamente asignados a un equipo.
    """
    if not isinstance(payload, Mapping) or not isinstance(esperado, Mapping):
        raise EvidenciaNoValida("Payload/identidad ESPN inválidos")
    fuente_id = str(esperado.get("id_fuente") or "")
    liga = str(esperado.get("liga") or "")
    header = payload.get("header")
    if not isinstance(header, Mapping):
        raise EvidenciaNoValida("Encabezado del resumen ESPN ausente o inválido")
    if not fuente_id or not liga or str(header.get("id")) != fuente_id:
        raise EvidenciaNoValida("ID de resumen ESPN distinto al evento vinculado")
    competiciones = header.get("competitions")
    if not isinstance(competiciones, list) or len(competiciones) != 1:
        raise EvidenciaNoValida("Resumen ESPN sin una competición única")
    partido = competiciones[0]
    if not isinstance(partido, Mapping):
        raise EvidenciaNoValida("Datos de competición ESPN inválidos")
    if str(partido.get("id")) != fuente_id:
        raise EvidenciaNoValida("Competición ESPN distinta al evento vinculado")
    fecha = partido.get("date")
    try:
        fecha_payload = _utc(datetime.fromisoformat(str(fecha).replace("Z", "+00:00")))
        inicio_esperado_raw = esperado.get("inicio_utc")
        inicio_esperado = (
            inicio_esperado_raw
            if isinstance(inicio_esperado_raw, datetime)
            else datetime.fromisoformat(str(inicio_esperado_raw).replace("Z", "+00:00"))
        )
        inicio_esperado = _utc(inicio_esperado)
    except (TypeError, ValueError):
        raise EvidenciaNoValida("Fecha ESPN inválida o ausente") from None
    if abs(fecha_payload - inicio_esperado) > timedelta(minutes=2):
        raise EvidenciaNoValida("Fecha ESPN no concilia con el evento vinculado")
    status_container = partido.get("status")
    if not isinstance(status_container, Mapping):
        raise EvidenciaNoValida("Estado ESPN con forma inválida")
    status = status_container.get("type") or {}
    if not isinstance(status, Mapping):
        raise EvidenciaNoValida("Tipo de estado ESPN con forma inválida")
    if status.get("completed") is not True or status.get("name") not in {
        "STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FINAL_AET", "STATUS_FINAL_PEN"
    }:
        raise EvidenciaNoValida("El resumen ESPN no acredita partido final")

    competidores = partido.get("competitors")
    if not isinstance(competidores, list) or len(competidores) != 2:
        raise EvidenciaNoValida("Identidad local/visitante ESPN incompleta")
    lados = {x.get("homeAway"): x for x in competidores if isinstance(x, Mapping)}
    if set(lados) != {"home", "away"}:
        raise EvidenciaNoValida("Orden local/visitante ESPN ambiguo")
    expected_ids = {
        "home": str(esperado.get("local_id_fuente") or ""),
        "away": str(esperado.get("visitante_id_fuente") or ""),
    }
    expected_scores = {
        "home": esperado.get("local_goles"),
        "away": esperado.get("visitante_goles"),
    }
    for lado in ("home", "away"):
        team = lados[lado].get("team")
        if not isinstance(team, Mapping):
            raise EvidenciaNoValida("ID de equipo ESPN ausente")
        if not expected_ids[lado] or str(team.get("id")) != expected_ids[lado]:
            raise EvidenciaNoValida("ID de equipo ESPN no concilia con el vínculo existente")
        if (isinstance(expected_scores[lado], bool) or not isinstance(expected_scores[lado], int)
                or expected_scores[lado] < 0):
            raise EvidenciaNoValida("Marcador canónico de control inválido")
        valor_ft = _leer_entero_observado(lados[lado].get("score"), "integer")
        if valor_ft != expected_scores[lado]:
            raise EvidenciaNoValida("Marcador ESPN no concilia con el vínculo existente")

    boxscore = payload.get("boxscore")
    if not isinstance(boxscore, Mapping):
        raise EvidenciaNoValida("Boxscore ESPN ausente")
    equipos = boxscore.get("teams")
    if not isinstance(equipos, list) or len(equipos) != 2:
        raise EvidenciaNoValida("Boxscore ESPN incompleto")
    stats_por_equipo: dict[str, dict[str, int | Decimal]] = {}
    if mapeo_metricas is not None and not isinstance(mapeo_metricas, Mapping):
        raise EvidenciaNoValida("Mapa de estadísticas ESPN inválido")
    key_to_field = dict(mapeo_metricas if mapeo_metricas is not None else {
        "wonCorners": ("local_corners_total", "visitante_corners_total"),
        "totalShots": ("local_disparos_total", "visitante_disparos_total"),
        "shotsOnTarget": ("local_disparos_arco", "visitante_disparos_arco"),
    })
    for provider_key, fields in key_to_field.items():
        if (not isinstance(provider_key, str) or not provider_key
                or not isinstance(fields, (tuple, list)) or len(fields) != 2
                or (fields[0] in _CAMPOS_DECIMALES) != (fields[1] in _CAMPOS_DECIMALES)
                or any(field not in CAMPOS_RECUPERABLES for field in fields)):
            raise EvidenciaNoValida("Mapa de estadísticas ESPN inválido")
    for equipo in equipos:
        if not isinstance(equipo, Mapping):
            raise EvidenciaNoValida("Equipo boxscore ESPN inválido")
        team = equipo.get("team")
        if not isinstance(team, Mapping):
            raise EvidenciaNoValida("Equipo boxscore ESPN sin identidad")
        team_id = str(team.get("id") or "")
        if not team_id or team_id in stats_por_equipo:
            raise EvidenciaNoValida("IDs de equipos boxscore ESPN ausentes o duplicados")
        valores: dict[str, int | Decimal] = {}
        statistics = equipo.get("statistics")
        if statistics is None:
            statistics = []
        if not isinstance(statistics, list):
            raise EvidenciaNoValida("Lista de estadísticas ESPN con forma inválida")
        for item in statistics:
            if not isinstance(item, Mapping) or item.get("name") not in key_to_field:
                continue
            key = str(item["name"])
            if key in valores:
                raise EvidenciaNoValida("Estadística ESPN duplicada para equipo")
            bruto = item.get("displayValue")
            if bruto is None:
                continue
            campo = key_to_field[key][0]
            valores[key] = _leer_valor_campo(campo, bruto, "double" if campo in _CAMPOS_DECIMALES else "integer")
        stats_por_equipo[team_id] = valores
    if set(stats_por_equipo) != set(expected_ids.values()):
        raise EvidenciaNoValida("IDs de boxscore ESPN no concilian con el evento")

    payload_hash = sha256_json(payload)
    salida: list[EvidenciaCampo] = []
    for provider_key, (campo_local, campo_visitante) in key_to_field.items():
        for lado, campo in (("home", campo_local), ("away", campo_visitante)):
            team_id = expected_ids[lado]
            valor = stats_por_equipo[team_id].get(provider_key)
            if valor is None:
                continue
            salida.append(
                EvidenciaCampo(
                    campo=campo,
                    valor=valor,
                    fuente="ESPN_SOCCER",
                    evento_id=fuente_id,
                    clave_proveedor=provider_key,
                    periodo_proveedor="All",
                    sha256_payload=payload_hash,
                    observado_en=_utc(observado_en),
                    contrato="ESPN_BOX_SCORE_FIELD_STATS_V1",
                )
            )
    return tuple(salida)


def construir_plan_resolucion(
    valores_canonicos: Mapping[str, Any],
    evidencias: Iterable[EvidenciaCampo],
) -> PlanResolucion:
    """Produce un merge conservador con procedencia y conflictos explícitos."""
    observaciones: dict[str, list[EvidenciaCampo]] = {}
    for evidencia in evidencias:
        if evidencia.campo not in CAMPOS_RECUPERABLES:
            raise EvidenciaNoValida("La evidencia contiene un campo no permitido")
        if evidencia.campo in _CAMPOS_ENTEROS and (
            isinstance(evidencia.valor, bool) or not isinstance(evidencia.valor, int) or evidencia.valor < 0
        ):
            raise EvidenciaNoValida("La evidencia contiene un conteo entero inválido")
        if evidencia.campo in _CAMPOS_DECIMALES and (
            not isinstance(evidencia.valor, Decimal)
            or not evidencia.valor.is_finite()
            or evidencia.valor < 0
            or evidencia.campo in {"local_posesion", "visitante_posesion"}
            and evidencia.valor > 100
        ):
            raise EvidenciaNoValida("La evidencia contiene un conteo inválido")
        if (evidencia.fuente.upper() not in FUENTES_PERMITIDAS
                or not re.fullmatch(r"[0-9a-f]{64}", evidencia.sha256_payload)
                or not _CONTRATO.fullmatch(evidencia.contrato)):
            raise EvidenciaNoValida("La evidencia no conserva fuente/hash válidos")
        if (not evidencia.evento_id or len(evidencia.evento_id) > 128
                or not evidencia.clave_proveedor or len(evidencia.clave_proveedor) > 128
                or evidencia.periodo_proveedor not in _PERIODOS):
            raise EvidenciaNoValida("La evidencia no cumple el contrato de evento/métrica/periodo")
        _utc(evidencia.observado_en)
        observaciones.setdefault(evidencia.campo, []).append(evidencia)

    conflictos: dict[str, str] = {}
    decisiones: dict[str, int | Decimal] = {}
    procedencia: dict[str, tuple[EvidenciaCampo, ...]] = {}
    preservados: set[str] = set()

    for campo, items in observaciones.items():
        valores = {x.valor for x in items}
        canonico = valores_canonicos.get(campo)
        if len(valores) > 1:
            conflictos[campo] = "Fuentes discrepan para el mismo campo; requiere revisión"
            continue
        valor = next(iter(valores))
        if canonico is not None:
            preservados.add(campo)
            if canonico != valor:
                conflictos[campo] = "Dato canónico no nulo contradice la observación; se preserva"
            else:
                procedencia[campo] = tuple(items)
            continue
        decisiones[campo] = valor
        procedencia[campo] = tuple(items)

    combinados = {campo: valores_canonicos.get(campo) for campo in CAMPOS_RECUPERABLES}
    combinados.update(decisiones)
    for pareja, etiqueta in (
        (("local_goles_et", "visitante_goles_et"), "prórroga"),
        (("local_penales", "visitante_penales"), "tanda de penales"),
    ):
        if any(campo in decisiones for campo in pareja) and any(
            combinados.get(campo) is None for campo in pareja
        ):
            for campo in pareja:
                if campo in decisiones:
                    decisiones.pop(campo, None)
                    procedencia.pop(campo, None)
                conflictos[campo] = f"Faltan ambos lados explícitos para validar {etiqueta}"
            combinados.update({campo: valores_canonicos.get(campo) for campo in pareja})
            combinados.update(decisiones)
    relacion_corners = (
        ("local_corners_total", "local_corners_1t", "local_corners_2t"),
        ("visitante_corners_total", "visitante_corners_1t", "visitante_corners_2t"),
    )
    for total, primero, segundo in relacion_corners:
        if all(combinados.get(x) is not None for x in (total, primero, segundo)):
            if combinados[total] != combinados[primero] + combinados[segundo]:
                for campo in (total, primero, segundo):
                    if campo in decisiones:
                        decisiones.pop(campo, None)
                        procedencia.pop(campo, None)
                    conflictos[campo] = "Total de corners no concilia con los dos periodos"

    for equipo in ("local", "visitante"):
        total, a_puerta = f"{equipo}_disparos_total", f"{equipo}_disparos_arco"
        if combinados.get(total) is not None and combinados.get(a_puerta) is not None:
            if combinados[a_puerta] > combinados[total]:
                for campo in (total, a_puerta):
                    if campo in decisiones:
                        decisiones.pop(campo, None)
                        procedencia.pop(campo, None)
                    conflictos[campo] = "Disparos a puerta exceden disparos totales"

    return PlanResolucion(
        actualizaciones=dict(decisiones),
        procedencia=dict(procedencia),
        preservados=tuple(sorted(preservados)),
        conflictos=dict(conflictos),
    )


def aplicar_plan_resolucion(
    connection: Any,
    *,
    partido_id: str,
    goles_local_ft: int,
    goles_visitante_ft: int,
    plan: PlanResolucion,
    identidades: Mapping[tuple[str, str], Mapping[str, Any]],
    dry_run: bool = True,
) -> dict[str, Any]:
    """Aplica solo si se solicita expresamente y registra procedencia atómica.

    `dry_run=True` no emite SQL. En modo de aplicación el caller debe envolver
    esta función en una transacción. Se bloquea y revalida el partido; cualquier
    valor canónico no nulo distinto aborta antes de cambiar datos.
    """
    actualizaciones = dict(plan.actualizaciones)
    for campo, valor in actualizaciones.items():
        tipo_invalido = (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 0
            if campo in _CAMPOS_ENTEROS else
            not isinstance(valor, Decimal) or not valor.is_finite() or valor < 0
            or campo in {"local_posesion", "visitante_posesion"} and valor > 100
        )
        if campo not in CAMPOS_RECUPERABLES or tipo_invalido:
            raise EvidenciaNoValida("Plan contiene un valor o columna no permitidos")
        fuentes = plan.procedencia.get(campo, ())
        if not fuentes or any(e.valor != valor for e in fuentes):
            raise EvidenciaNoValida("Cada actualización debe tener procedencia concordante")

    preview = {
        "partido_id": str(partido_id),
        "actualizaciones": actualizaciones,
        "flags_derivados": sorted(
            flag for campos, flag in (
                (("local_goles_et", "visitante_goles_et"), "hubo_tiempo_extra=true"),
                (("local_penales", "visitante_penales"), "hubo_penales=true"),
            ) if any(campo in actualizaciones for campo in campos)
        ),
        "n_evidencias": sum(len(xs) for xs in plan.procedencia.values()),
        "conflictos": dict(plan.conflictos),
        "modo": "DRY_RUN" if dry_run else "APLICAR",
    }
    if dry_run:
        return preview

    if isinstance(goles_local_ft, bool) or not isinstance(goles_local_ft, int) or goles_local_ft < 0:
        raise EvidenciaNoValida("Marcador local de control inválido")
    if isinstance(goles_visitante_ft, bool) or not isinstance(goles_visitante_ft, int) or goles_visitante_ft < 0:
        raise EvidenciaNoValida("Marcador visitante de control inválido")
    if not isinstance(identidades, Mapping):
        raise EvidenciaNoValida("Se requieren identificadores de identidad por fuente")
    if getattr(connection, "autocommit", False):
        raise EvidenciaNoValida("La aplicación requiere una transacción explícita")
    from psycopg.pq import TransactionStatus
    if connection.info.transaction_status != TransactionStatus.INTRANS:
        raise EvidenciaNoValida("La aplicación requiere un bloque connection.transaction() activo")

    campos_identidad = {
        "metodo", "canonical_competition_id", "provider_competition_id",
        "canonical_home_team_id", "provider_home_team_id",
        "canonical_away_team_id", "provider_away_team_id",
        "canonical_start_utc", "provider_start_utc", "canonical_ft", "provider_ft",
    }
    identidades_limpias: dict[tuple[str, str], dict[str, Any]] = {}
    for campo, observaciones in plan.procedencia.items():
        for evidencia in observaciones:
            clave_identidad = (evidencia.fuente.upper(), evidencia.evento_id)
            identidad = identidades.get(clave_identidad)
            if not isinstance(identidad, Mapping) or set(identidad) != campos_identidad:
                raise EvidenciaNoValida("Evidencia de identidad incompleta o con campos inesperados")
            if identidad["metodo"] != "MAPPED_PROVIDER_IDS_AND_EVENT_CONCILIATION_V1":
                raise EvidenciaNoValida("Método de identidad no aprobado")
            if not all(identidad[k] for k in campos_identidad - {"canonical_ft", "provider_ft"}):
                raise EvidenciaNoValida("Identificadores o fechas de identidad vacíos")
            if identidad["canonical_ft"] != identidad["provider_ft"]:
                raise EvidenciaNoValida("Marcadores dentro de la evidencia de identidad discrepan")
            if identidad["canonical_ft"] != [goles_local_ft, goles_visitante_ft]:
                raise EvidenciaNoValida("La evidencia de identidad no corresponde al FT del plan")
            if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in identidad["canonical_ft"]):
                raise EvidenciaNoValida("Marcador en evidencia de identidad inválido")
            try:
                identidad_limpia = dict(identidad)
                identidad_limpia["canonical_start_utc"] = _utc(datetime.fromisoformat(
                    str(identidad_limpia["canonical_start_utc"]).replace("Z", "+00:00")))
                identidad_limpia["provider_start_utc"] = _utc(datetime.fromisoformat(
                    str(identidad_limpia["provider_start_utc"]).replace("Z", "+00:00")))
            except (TypeError, ValueError):
                raise EvidenciaNoValida("Fechas en evidencia de identidad inválidas") from None
            identidades_limpias[clave_identidad] = identidad_limpia

    from psycopg import sql
    from psycopg.types.json import Jsonb

    columnas = sorted(CAMPOS_RECUPERABLES)
    seleccion = [
        "estado", "competicion_id", "equipo_local_id", "equipo_visitante_id", "fecha_partido",
        "local_goles_total", "visitante_goles_total", "hubo_tiempo_extra", "hubo_penales", *columnas,
    ]
    fila = connection.execute(
        sql.SQL("SELECT {} FROM partidos_futbol WHERE id=%s FOR UPDATE").format(
            sql.SQL(",").join(map(sql.Identifier, seleccion))
        ),
        (partido_id,),
    ).fetchone()
    if fila is None:
        raise EvidenciaNoValida("Partido canónico inexistente")
    if isinstance(fila, Mapping):
        canonico = dict(fila)
    else:
        canonico = dict(zip(seleccion, fila))
    if (canonico["estado"] != "FINALIZADO"
            or canonico["local_goles_total"] != goles_local_ft
            or canonico["visitante_goles_total"] != goles_visitante_ft):
        raise ConflictoConcurrente("Estado o marcador canónico cambió antes de aplicar")
    inicio_db = _utc(canonico["fecha_partido"])
    for identidad in identidades_limpias.values():
        if (str(canonico["competicion_id"]) != str(identidad["canonical_competition_id"])
                or str(canonico["equipo_local_id"]) != str(identidad["canonical_home_team_id"])
                or str(canonico["equipo_visitante_id"]) != str(identidad["canonical_away_team_id"])):
            raise ConflictoConcurrente("Competición o equipos canónicos cambiaron antes de aplicar")
        if inicio_db != identidad["canonical_start_utc"]:
            raise ConflictoConcurrente("Fecha canónica cambió antes de aplicar")
        if abs(identidad["provider_start_utc"] - inicio_db) > timedelta(minutes=2):
            raise EvidenciaNoValida("Inicio externo fuera de tolerancia al aplicar")

    vinculos_nuevos = 0
    for fuente, evento_id in identidades_limpias:
        cursor = connection.execute(
            """INSERT INTO vinculos_multifuente_partidos_futbol
               (fuente,id_evento_fuente,partido_id) VALUES (%s,%s,%s)
               ON CONFLICT (fuente,id_evento_fuente) DO NOTHING RETURNING 1""",
            (fuente, evento_id, partido_id),
        )
        vinculos_nuevos += int(cursor.fetchone() is not None)
        vinculo = connection.execute(
            "SELECT partido_id FROM vinculos_multifuente_partidos_futbol "
            "WHERE fuente=%s AND id_evento_fuente=%s",
            (fuente, evento_id),
        ).fetchone()
        if vinculo is None or str(vinculo[0] if not isinstance(vinculo, Mapping) else vinculo["partido_id"]) != str(partido_id):
            raise ConflictoConcurrente("El evento de proveedor ya está vinculado a otro partido")

    a_aplicar: dict[str, int] = {}
    for campo, valor in actualizaciones.items():
        actual = canonico[campo]
        if actual is None:
            a_aplicar[campo] = valor
        elif actual == valor:
            continue
        else:
            raise ConflictoConcurrente(f"El campo {campo} dejó de ser NULL y no se sobrescribe")

    flags_derivados: dict[str, bool] = {}
    for campos, flag, etiqueta in (
        (("local_goles_et", "visitante_goles_et"), "hubo_tiempo_extra", "prórroga"),
        (("local_penales", "visitante_penales"), "hubo_penales", "tanda de penales"),
    ):
        if any(campo in a_aplicar for campo in campos):
            if any(canonico[campo] is None and campo not in a_aplicar for campo in campos):
                raise EvidenciaNoValida(f"Se requieren valores explícitos de ambos lados para {etiqueta}")
            flags_derivados[flag] = True

    if a_aplicar:
        campos_update: dict[str, Any] = dict(a_aplicar)
        campos_update.update(flags_derivados)
        asignaciones = sql.SQL(",").join(
            sql.SQL("{}=%s").format(sql.Identifier(campo)) for campo in campos_update
        )
        guardas_null = sql.SQL(" AND ").join(
            sql.SQL("{} IS NULL").format(sql.Identifier(campo)) for campo in a_aplicar
        )
        cursor = connection.execute(
            sql.SQL(
                "UPDATE partidos_futbol SET {} WHERE id=%s AND estado='FINALIZADO' "
                "AND local_goles_total=%s AND visitante_goles_total=%s AND {} RETURNING id"
            ).format(asignaciones, guardas_null),
            (*campos_update.values(), partido_id, goles_local_ft, goles_visitante_ft),
        )
        if cursor.fetchone() is None:
            raise ConflictoConcurrente("El UPDATE protegido no encontró el estado esperado")

    insertados = 0
    for campo, observaciones in plan.procedencia.items():
        if campo not in CAMPOS_RECUPERABLES:
            raise EvidenciaNoValida("Procedencia contiene una columna no permitida")
        for evidencia in observaciones:
            identidad = identidades_limpias[(evidencia.fuente.upper(), evidencia.evento_id)]
            identidad_json = {
                "metodo": identidad["metodo"],
                "canonical_competition_id": str(identidad["canonical_competition_id"]),
                "provider_competition_id": str(identidad["provider_competition_id"]),
                "canonical_home_team_id": str(identidad["canonical_home_team_id"]),
                "provider_home_team_id": str(identidad["provider_home_team_id"]),
                "canonical_away_team_id": str(identidad["canonical_away_team_id"]),
                "provider_away_team_id": str(identidad["provider_away_team_id"]),
                "canonical_start_utc": identidad["canonical_start_utc"].isoformat(),
                "provider_start_utc": identidad["provider_start_utc"].isoformat(),
                "canonical_ft": list(identidad["canonical_ft"]),
                "provider_ft": list(identidad["provider_ft"]),
            }
            cursor = connection.execute(
                """INSERT INTO observaciones_multifuente_estadisticas_futbol
                   (fuente, id_evento_fuente, partido_id, campo, valor, clave_proveedor,
                    periodo_proveedor, sha256_payload, contrato, evidencia_identidad, observado_en)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (fuente,id_evento_fuente,campo,clave_proveedor,periodo_proveedor,sha256_payload,contrato)
                   DO NOTHING RETURNING 1""",
                (
                    evidencia.fuente.upper(), evidencia.evento_id, partido_id, campo, evidencia.valor,
                    evidencia.clave_proveedor, evidencia.periodo_proveedor, evidencia.sha256_payload,
                    evidencia.contrato, Jsonb(identidad_json), evidencia.observado_en,
                ),
            )
            insertados += int(cursor.fetchone() is not None)

    return {
        **preview,
        "campos_aplicados": sorted(a_aplicar),
        "vinculos_nuevos": vinculos_nuevos,
        "filas_evidencia_insertadas": insertados,
    }
