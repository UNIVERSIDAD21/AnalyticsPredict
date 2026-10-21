"""Resolución conservadora y trazable de estadísticas nulas multi-fuente.

Normaliza evidencia capturada, valida identidad de partido y produce un plan
campo-a-campo. La red queda fuera de este módulo. No deduce valores, no convierte
ausencia en cero y nunca reemplaza datos canónicos no nulos. La única aplicación
SQL requiere llamada explícita, transacción activa y revalidación bajo bloqueo.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping


FUENTES_PERMITIDAS = frozenset({
    "PITCHAPI", "ESPN_SOCCER", "SOFASCORE", "THESTATSAPI", "DATAHUB_FOOTBALL_DATA",
    "KAGGLE_GOKHANERGUL", "HF_EATPIZZANOT", "WEB",
})
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
MAPEO_METRICAS_DATAHUB_FOOTBALL_DATA = {
    ("corners", "All"): ("local_corners_total", "visitante_corners_total"),
    ("shots", "All"): ("local_disparos_total", "visitante_disparos_total"),
    ("shots_on_target", "All"): ("local_disparos_arco", "visitante_disparos_arco"),
}
MAPEO_METRICAS_KAGGLE_GOKHANERGUL = {
    ("Corner_Kicks", "All"): ("local_corners_total", "visitante_corners_total"),
    ("Goal_Attempts", "All"): ("local_disparos_total", "visitante_disparos_total"),
    ("Shots_on_Goal", "All"): ("local_disparos_arco", "visitante_disparos_arco"),
}
MAPEO_METRICAS_HF_EATPIZZANOT = {
    "home_corners": "local_corners_total",
    "away_corners": "visitante_corners_total",
    "home_shots_total": "local_disparos_total",
    "away_shots_total": "visitante_disparos_total",
    "home_shots_on_goal": "local_disparos_arco",
    "away_shots_on_goal": "visitante_disparos_arco",
}
METODO_IDENTIDAD_ESTRICTA = "MAPPED_PROVIDER_IDS_AND_EVENT_CONCILIATION_V1"
METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA = (
    "MAPPED_PROVIDER_IDS_AND_LEGACY_SOFASCORE_BOGOTA_NAIVE_TIME_V1"
)


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


def validar_inicio_identidad(
    inicio_canonico: datetime,
    inicio_proveedor: datetime,
    *,
    metodo: str = METODO_IDENTIDAD_ESTRICTA,
    fuente_proveedor: str,
    fuente_canonica: str | None = None,
    tolerancia: timedelta = timedelta(minutes=2),
) -> None:
    """Valida fechas con una excepción explícita para el importador histórico.

    `cargar_historico_futbol.py` guardó timestamps SofaScore usando
    `datetime.fromtimestamp()` sin zona; en el host America/Bogota esos valores
    quedaron cinco horas antes al persistirlos como timestamptz. La excepción
    solo acepta la diferencia exacta ESPN − SofaScore = +5 h, el mismo día UTC
    y el origen canónico SofaScore. No normaliza ni corrige la fecha guardada.
    """
    canonico = _utc(inicio_canonico)
    proveedor = _utc(inicio_proveedor)
    if metodo == METODO_IDENTIDAD_ESTRICTA:
        if abs(proveedor - canonico) > tolerancia:
            raise EvidenciaNoValida("Inicio UTC fuera de la tolerancia de identidad")
        return
    if metodo != METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA:
        raise EvidenciaNoValida("Método de identidad no aprobado")
    if fuente_proveedor.upper() != "ESPN_SOCCER" or fuente_canonica != "SOFASCORE":
        raise EvidenciaNoValida("El desfase histórico solo aplica a ESPN sobre SofaScore")
    if proveedor.date() != canonico.date():
        raise EvidenciaNoValida("El desfase histórico cruza el día UTC")
    if proveedor - canonico != timedelta(hours=5):
        raise EvidenciaNoValida("Desfase histórico distinto de +5 horas exactas")


def validar_vinculo_partido(
    canonico: PartidoCanonico,
    proveedor: PartidoProveedor,
    *,
    mapeo_competiciones: Mapping[tuple[str, str], str],
    mapeo_equipos: Mapping[tuple[str, str], str],
    metodo_identidad: str = METODO_IDENTIDAD_ESTRICTA,
    fuente_canonica: str | None = None,
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
    validar_inicio_identidad(
        canonico.inicio_utc,
        proveedor.inicio_utc,
        metodo=metodo_identidad,
        fuente_proveedor=fuente,
        fuente_canonica=fuente_canonica,
        tolerancia=tolerancia_inicio,
    )


def vincular_partido_unico(
    candidatos: Iterable[PartidoCanonico],
    proveedor: PartidoProveedor,
    *,
    mapeo_competiciones: Mapping[tuple[str, str], str],
    mapeo_equipos: Mapping[tuple[str, str], str],
    metodo_identidad: str = METODO_IDENTIDAD_ESTRICTA,
    fuente_canonica: str | None = None,
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
                metodo_identidad=metodo_identidad,
                fuente_canonica=fuente_canonica,
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


def extraer_evidencia_datahub_football_data_csv(
    *,
    evento_id: str,
    payload: Mapping[str, Any],
    esperado: Mapping[str, Any],
    observado_en: datetime,
) -> tuple[EvidenciaCampo, ...]:
    """Extrae corners/tiros de una fila DataHub (origen football-data.co.uk).

    La identidad de equipo/partido se concilia externamente con nombres exactos,
    competición, fecha local y FT; esta función verifica que la fila CSV y su
    hash correspondan a la expectativa recibida y conserva el archivo/fila.
    No interpreta fecha como hora de inicio ni completa estadísticas ausentes.
    """
    if not isinstance(payload, Mapping) or not isinstance(esperado, Mapping):
        raise EvidenciaNoValida("Payload o identidad DataHub inválidos")
    slugs = {
        "ENG_PREMIER": "english-premier-league",
        "ESP_LALIGA": "spanish-la-liga",
        "GER_BUNDESLIGA": "german-bundesliga",
        "ITA_SERIEA": "italian-serie-a",
        "FRA_LIGUE1": "french-ligue-1",
    }
    codigo = str(payload.get("competition_code") or "")
    temporada = str(payload.get("season") or "")
    archivo_hash = str(payload.get("source_file_sha256") or "")
    fila_hash = str(payload.get("source_row_sha256") or "")
    fila_numero = payload.get("source_row_number")
    fila = payload.get("raw_row")
    if codigo not in slugs or not re.fullmatch(r"[0-9]{4}", temporada):
        raise EvidenciaNoValida("Competición/temporada DataHub no reconocida")
    if payload.get("license") != "ODC-PDDL-1.0":
        raise EvidenciaNoValida("Licencia del dataset DataHub no verificada")
    url_esperada = (
        f"https://datahub.io/football/{slugs[codigo]}/_r/-/season-{temporada}.csv"
    )
    if payload.get("source_url") != url_esperada:
        raise EvidenciaNoValida("URL de dataset DataHub inesperada")
    if (not re.fullmatch(r"[0-9a-f]{64}", archivo_hash)
            or not re.fullmatch(r"[0-9a-f]{64}", fila_hash)
            or isinstance(fila_numero, bool) or not isinstance(fila_numero, int)
            or fila_numero < 2 or not isinstance(fila, Mapping)):
        raise EvidenciaNoValida("Hash o localizador de fila CSV inválido")
    if sha256_json(fila) != fila_hash:
        raise EvidenciaNoValida("El hash de la fila no reproduce el CSV normalizado")
    if str(payload.get("event_id") or "") != evento_id or str(esperado.get("event_id") or "") != evento_id:
        raise EvidenciaNoValida("ID del evento DataHub no coincide")
    identity_fields = {
        "competition_code": "comp_code",
        "season": "season",
        "date": "date",
        "home": "home",
        "away": "away",
        "ft_home": "ft_home",
        "ft_away": "ft_away",
    }
    for payload_key, expected_key in identity_fields.items():
        if payload.get(payload_key) != esperado.get(expected_key):
            raise EvidenciaNoValida("Identidad de fila DataHub no concilia con la expectativa")
    if (
        fila.get("Date") != payload.get("date")
        or fila.get("HomeTeam") != payload.get("home")
        or fila.get("AwayTeam") != payload.get("away")
        or fila.get("FTHG") != str(payload.get("ft_home"))
        or fila.get("FTAG") != str(payload.get("ft_away"))
    ):
        raise EvidenciaNoValida("Identidad CSV no concilia con sus metadatos")

    estadisticas = [
        {
            "key": "corners",
            "home": fila.get("HC"),
            "away": fila.get("AC"),
            "format_type": "integer",
        },
        {
            "key": "shots",
            "home": fila.get("HS"),
            "away": fila.get("AS"),
            "format_type": "integer",
        },
        {
            "key": "shots_on_target",
            "home": fila.get("HST"),
            "away": fila.get("AST"),
            "format_type": "integer",
        },
    ]
    normalized = {
        "match_id": evento_id,
        "home_team": {"id": payload["home"]},
        "away_team": {"id": payload["away"]},
        "periods": [{"period": "All", "groups": [{"items": estadisticas}]}],
        "source_file_sha256": archivo_hash,
        "source_row_sha256": fila_hash,
        "source_row_number": fila_numero,
        "source_url": url_esperada,
        "license": "ODC-PDDL-1.0",
        "raw_row": dict(fila),
    }
    evidencia = extraer_evidencia_estadistica(
        fuente="DATAHUB_FOOTBALL_DATA",
        evento_id=evento_id,
        payload=normalized,
        esperado_local_proveedor_id=str(payload["home"]),
        esperado_visitante_proveedor_id=str(payload["away"]),
        mapeo_metricas=MAPEO_METRICAS_DATAHUB_FOOTBALL_DATA,
        observado_en=observado_en,
        contrato="DATAHUB_FOOTBALL_DATA_CSV_V1",
    )
    return tuple(replace(item, sha256_payload=fila_hash) for item in evidencia)


def extraer_evidencia_kaggle_gokhanergul_csv(
    *,
    evento_id: str,
    payload: Mapping[str, Any],
    esperado: Mapping[str, Any],
    observado_en: datetime,
) -> tuple[EvidenciaCampo, ...]:
    """Extrae stats de una fila CSV Kaggle V2 bajo licencia declarada MIT.

    El dataset no publica IDs ni zona horaria de inicio: la identidad debe ser
    verificada por el caller con competición, temporada, fecha local, nombres
    de ambos lados/orden, FT y unicidad. Esta función solo autentica metadatos,
    localizador y contenido de la fila; no inventa un timestamp UTC.

    Las columnas Goal_Attempts, Shots_on_Goal y Corner_Kicks son métricas
    directas según el card del dataset. Los valores numéricos como "8.0" se
    aceptan únicamente si son enteros exactos y no negativos. Cuando están los
    componentes, Goal_Attempts debe ser igual a SOT + disparos fuera + bloqueados.
    """
    if not isinstance(payload, Mapping) or not isinstance(esperado, Mapping):
        raise EvidenciaNoValida("Payload o identidad Kaggle inválidos")
    if payload.get("license") != "MIT":
        raise EvidenciaNoValida("La licencia declarada del dataset Kaggle no es MIT")
    if payload.get("dataset") != "gokhanergul/football-match-statistics" or payload.get("dataset_version") != 2:
        raise EvidenciaNoValida("Dataset Kaggle o versión distintos a la auditoría")
    archive_hash = str(payload.get("source_archive_sha256") or "")
    row_hash = str(payload.get("source_row_sha256") or "")
    row = payload.get("raw_row")
    row_number = payload.get("source_row_number")
    if (
        not re.fullmatch(r"[0-9a-f]{64}", archive_hash)
        or not re.fullmatch(r"[0-9a-f]{64}", row_hash)
        or isinstance(row_number, bool)
        or not isinstance(row_number, int)
        or row_number < 2
        or not isinstance(row, Mapping)
        or sha256_json(row) != row_hash
    ):
        raise EvidenciaNoValida("Hash/localizador del CSV Kaggle inválido")
    expected_fields = {
        "Country": "country",
        "League": "league",
        "season_year": "season",
        "Date_day": "date_day",
        "home_team": "home",
        "away_team": "away",
    }
    for source_field, expected_field in expected_fields.items():
        if row.get(source_field) != esperado.get(expected_field) or payload.get(expected_field) != esperado.get(expected_field):
            raise EvidenciaNoValida("Identidad de fila Kaggle no concilia con los metadatos")
    if (
        str(payload.get("event_id") or "") != evento_id
        or str(esperado.get("event_id") or "") != evento_id
        or row.get("home_score") != str(esperado.get("ft_home"))
        or row.get("away_score") != str(esperado.get("ft_away"))
        or payload.get("ft_home") != esperado.get("ft_home")
        or payload.get("ft_away") != esperado.get("ft_away")
        or payload.get("date_local_inferred") != esperado.get("date_local")
    ):
        raise EvidenciaNoValida("Marcador/fecha/ID del evento Kaggle no concilia")
    if payload.get("dataset_url") != "https://www.kaggle.com/datasets/gokhanergul/football-match-statistics":
        raise EvidenciaNoValida("URL del dataset Kaggle inesperada")

    def _integer(raw: Any, field: str) -> int | None:
        if raw in (None, ""):
            return None
        try:
            number = Decimal(str(raw).strip())
        except (InvalidOperation, ValueError):
            raise EvidenciaNoValida(f"Campo Kaggle {field} no numérico") from None
        if not number.is_finite() or number < 0 or number != number.to_integral_value():
            raise EvidenciaNoValida(f"Campo Kaggle {field} no es entero no negativo")
        return int(number)

    raw_metrics = {
        "Corner_Kicks": ("Corner_Kicks_Home", "Corner_Kicks_Host"),
        "Goal_Attempts": ("Goal_Attempts_Home", "Goal_Attempts_Host"),
        "Shots_on_Goal": ("Shots_on_Goal_Home", "Shots_on_Goal_Host"),
    }
    parsed: dict[str, tuple[int | None, int | None]] = {}
    for key, (home_key, away_key) in raw_metrics.items():
        parsed[key] = (_integer(row.get(home_key), home_key), _integer(row.get(away_key), away_key))
    for side_index, side_name in enumerate(("Home", "Host")):
        attempts = parsed["Goal_Attempts"][side_index]
        on_target = parsed["Shots_on_Goal"][side_index]
        off_target = _integer(row.get(f"Shots_off_Goal_{side_name}"), f"Shots_off_Goal_{side_name}")
        blocked = _integer(row.get(f"Blocked_Shots_{side_name}"), f"Blocked_Shots_{side_name}")
        if on_target is not None and attempts is not None and on_target > attempts:
            raise EvidenciaNoValida("Shots_on_Goal excede Goal_Attempts")
        if all(value is not None for value in (attempts, on_target, off_target, blocked)):
            if attempts != on_target + off_target + blocked:
                raise EvidenciaNoValida("Goal_Attempts no concilia con los componentes de disparos")

    normalized_items = []
    for key, values in parsed.items():
        for side, value in (("home", values[0]), ("away", values[1])):
            if value is not None:
                normalized_items.append({"key": key, "home": values[0], "away": values[1], "format_type": "integer"})
                break
    normalized = {
        "match_id": evento_id,
        "home_team": {"id": str(esperado.get("home"))},
        "away_team": {"id": str(esperado.get("away"))},
        "periods": [{"period": "All", "groups": [{"items": normalized_items}]}],
        "dataset": payload.get("dataset"),
        "dataset_version": payload.get("dataset_version"),
        "license": payload.get("license"),
        "dataset_url": payload.get("dataset_url"),
        "source_archive_sha256": archive_hash,
        "source_row_sha256": row_hash,
        "source_row_number": row_number,
        "raw_row": dict(row),
    }
    evidencia = extraer_evidencia_estadistica(
        fuente="KAGGLE_GOKHANERGUL",
        evento_id=evento_id,
        payload=normalized,
        esperado_local_proveedor_id=str(esperado.get("home")),
        esperado_visitante_proveedor_id=str(esperado.get("away")),
        mapeo_metricas=MAPEO_METRICAS_KAGGLE_GOKHANERGUL,
        observado_en=observado_en,
        contrato="KAGGLE_GOKHANERGUL_CUP_STATS_V2",
    )
    return tuple(replace(item, sha256_payload=row_hash) for item in evidencia)


def extraer_evidencia_hf_eatpizzanot_dataset(
    *,
    partido_auditado: Mapping[str, Any],
    observado_en: datetime,
    revision_esperada: str,
) -> tuple[EvidenciaCampo, ...]:
    """Extrae estadísticas positivas de la revisión fijada del dataset HF.

    El dataset declara CC-BY-4.0 y atribuye sus datos a API-Football y
    football-data.co.uk. Su propio card advierte que podría no conceder todos
    los derechos del contenido upstream; conservar atribución y caveat es parte
    del registro de procedencia. Los ceros no se usan: la auditoría detectó
    placeholders y conflictos de cero frente a valores canónicos positivos.

    El llamador debe validar por separado identidad única, IDs API-Football,
    marcador, fecha y precisión temporal antes de construir el merge.
    """
    if not isinstance(partido_auditado, Mapping):
        raise EvidenciaNoValida("Registro auditado HF inválido")
    observado = _utc(observado_en)
    revision = str(partido_auditado.get("dataset_revision") or "")
    if revision != revision_esperada or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise EvidenciaNoValida("La revisión HF no coincide con el pin esperado")
    if partido_auditado.get("declared_license") != "CC-BY-4.0":
        raise EvidenciaNoValida("La licencia declarada del dataset HF no coincide")
    if partido_auditado.get("dataset_url") != "https://huggingface.co/datasets/eatpizzanot/soccer-dataset":
        raise EvidenciaNoValida("URL del dataset HF inesperada")
    if partido_auditado.get("source_quality_policy") != (
        "Reject every source zero as ambiguous because all-zero placeholder rows and conflicts with positive canonical values were observed; "
        "reject both shot total and shots-on-target for a side when source shots-on-target exceeds source total; "
        "apply only positive integer values to canonical NULL; preserve equal or conflicting non-NULL; "
        "require unique competition/date/ordered teams/FT identity."
    ):
        raise EvidenciaNoValida("La política conservadora de calidad HF cambió")

    raw = partido_auditado.get("raw_source_payload")
    if not isinstance(raw, Mapping) or sha256_json(raw) != partido_auditado.get("source_row_sha256"):
        raise EvidenciaNoValida("Hash del registro fuente HF no reproduce el payload")
    ft = partido_auditado.get("source_ft")
    if not isinstance(ft, list) or len(ft) != 2:
        raise EvidenciaNoValida("Marcador HF mal formado")
    if (
        raw.get("dataset_revision") != revision
        or raw.get("status_norm") != "FT"
        or raw.get("fixture_id") != partido_auditado.get("source_fixture_id")
        or raw.get("api_football_id") != partido_auditado.get("source_api_football_id")
        or raw.get("goals_home") != ft[0]
        or raw.get("goals_away") != ft[1]
        or raw.get("league_id") != partido_auditado.get("source_competition_id")
        or raw.get("home_team_id") != partido_auditado.get("source_home_team_id", raw.get("home_team_id"))
        or raw.get("away_team_id") != partido_auditado.get("source_away_team_id", raw.get("away_team_id"))
    ):
        raise EvidenciaNoValida("Estado, marcador o IDs del payload HF no concilian con auditoría")
    stats = raw.get("match_stats")
    if not isinstance(stats, Mapping):
        raise EvidenciaNoValida("Estadísticas HF ausentes o mal formadas")
    event_id = str(partido_auditado.get("source_event_id") or "")
    api_id = partido_auditado.get("source_api_football_id")
    expected_event = (
        f"API_FOOTBALL/{api_id}" if api_id is not None
        else f"HF_DATASET/{revision}/fixture/{partido_auditado.get('source_fixture_id')}"
    )
    if event_id != expected_event or len(event_id) > 128:
        raise EvidenciaNoValida("ID determinista de evento HF inválido")

    values: dict[str, int] = {}
    for source_key, canonical_field in MAPEO_METRICAS_HF_EATPIZZANOT.items():
        value = stats.get(source_key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EvidenciaNoValida("Conteo HF no es entero no negativo")
        if value > 0:
            values[canonical_field] = value
    for side, shots, target in (
        ("local", "local_disparos_total", "local_disparos_arco"),
        ("visitante", "visitante_disparos_total", "visitante_disparos_arco"),
    ):
        if shots in values and target in values and values[target] > values[shots]:
            raise EvidenciaNoValida(f"Tiros a puerta HF exceden los tiros totales: {side}")
    expected_updates = partido_auditado.get("updates")
    if not isinstance(expected_updates, Mapping) or dict(expected_updates) != values:
        raise EvidenciaNoValida("Los valores positivos HF no reproducen el lote NULL-only auditado")

    payload_hash = str(partido_auditado.get("source_row_sha256"))
    return tuple(
        EvidenciaCampo(
            campo=canonical_field,
            valor=values[canonical_field],
            fuente="HF_EATPIZZANOT",
            evento_id=event_id,
            clave_proveedor=source_key,
            periodo_proveedor="All",
            sha256_payload=payload_hash,
            observado_en=observado,
            contrato="HF_EATPIZZANOT_STATS_V1",
        )
        for source_key, canonical_field in MAPEO_METRICAS_HF_EATPIZZANOT.items()
        if canonical_field in values
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

    campos_identidad_base = {
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
            if not isinstance(identidad, Mapping):
                raise EvidenciaNoValida("Evidencia de identidad incompleta o con campos inesperados")
            metodo = identidad.get("metodo")
            campos_esperados = (
                campos_identidad_base
                if metodo == METODO_IDENTIDAD_ESTRICTA
                else campos_identidad_base | {"canonical_source"}
                if metodo == METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA
                else set()
            )
            if not campos_esperados or set(identidad) != campos_esperados:
                raise EvidenciaNoValida("Método de identidad no aprobado")
            campos_requeridos = campos_esperados - {"canonical_ft", "provider_ft"}
            if not all(identidad[k] for k in campos_requeridos):
                raise EvidenciaNoValida("Identificadores o fechas de identidad vacíos")
            if (metodo == METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA
                    and (evidencia.fuente.upper() != "ESPN_SOCCER"
                         or identidad["canonical_source"] != "SOFASCORE")):
                raise EvidenciaNoValida("El método de desfase histórico no aplica a este origen")
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
            validar_inicio_identidad(
                identidad_limpia["canonical_start_utc"],
                identidad_limpia["provider_start_utc"],
                metodo=metodo,
                fuente_proveedor=evidencia.fuente,
                fuente_canonica=identidad.get("canonical_source"),
            )
            identidades_limpias[clave_identidad] = identidad_limpia

    from psycopg import sql
    from psycopg.types.json import Jsonb

    columnas = sorted(CAMPOS_RECUPERABLES)
    seleccion = [
        "estado", "competicion_id", "equipo_local_id", "equipo_visitante_id", "fecha_partido",
        "fuente_datos", "local_goles_total", "visitante_goles_total",
        "hubo_tiempo_extra", "hubo_penales", *columnas,
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
    for (fuente, _evento_id), identidad in identidades_limpias.items():
        if (str(canonico["competicion_id"]) != str(identidad["canonical_competition_id"])
                or str(canonico["equipo_local_id"]) != str(identidad["canonical_home_team_id"])
                or str(canonico["equipo_visitante_id"]) != str(identidad["canonical_away_team_id"])):
            raise ConflictoConcurrente("Competición o equipos canónicos cambiaron antes de aplicar")
        if inicio_db != identidad["canonical_start_utc"]:
            raise ConflictoConcurrente("Fecha canónica cambió antes de aplicar")
        if identidad["metodo"] == METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA:
            if (canonico["fuente_datos"] != identidad["canonical_source"]
                    or identidad["canonical_source"] != "SOFASCORE"):
                raise ConflictoConcurrente("El origen canónico ya no concilia con el desfase histórico")
        validar_inicio_identidad(
            inicio_db,
            identidad["provider_start_utc"],
            metodo=identidad["metodo"],
            fuente_proveedor=fuente,
            fuente_canonica=identidad.get("canonical_source"),
        )

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
            if identidad["metodo"] == METODO_IDENTIDAD_SOFASCORE_HORA_LOCAL_BOGOTA:
                identidad_json["canonical_source"] = identidad["canonical_source"]
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
