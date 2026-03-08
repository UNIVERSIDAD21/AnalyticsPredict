# -*- coding: utf-8 -*-
"""Contrato canónico de explicación de predicción v1.0."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QualityCoherenceError(ValueError):
    """Error cuando calidad y warnings entran en contradicción."""


Sport = Literal["NBA", "FOOTBALL"]
Recommendation = Literal["over", "under", "skip"]
ConfidenceLevel = Literal["high", "medium", "low"]
QualityLevel = Literal["A", "B", "C"]


class GameInfo(BaseModel):
    home_team: str
    away_team: str
    game_date: datetime
    league: str


class PredictionInterval(BaseModel):
    lower: float
    upper: float


class PredictionConfidence(BaseModel):
    level: ConfidenceLevel
    numeric: float = Field(ge=0, le=100)
    interval: PredictionInterval


class PredictionData(BaseModel):
    value: float
    unit: Literal["points", "goals"]
    line: float
    recommendation: Recommendation
    confidence: PredictionConfidence


class QualityFlag(BaseModel):
    type: Literal["drift", "incomplete", "stale", "outlier", "quality", "coverage", "beta"]
    severity: Literal["critical", "high", "medium", "low"]
    message: str


class DataQuality(BaseModel):
    score: float = Field(ge=0, le=100)
    level: QualityLevel
    flags: List[QualityFlag] = Field(default_factory=list)


class TopFactor(BaseModel):
    factor_name: str
    contribution: float = Field(ge=-100, le=100)
    value: float
    description: str


class ExplanationWarning(BaseModel):
    type: Literal["quality", "drift", "coverage", "beta", "stale", "outlier", "incomplete"]
    message: str
    severity: Literal["high", "medium", "low"]


class HistoricalContext(BaseModel):
    similar_predictions: int = Field(ge=0)
    accuracy_rate: float = Field(ge=0, le=1)
    sample_size: int = Field(ge=0)


class ExplanationData(BaseModel):
    top_factors: List[TopFactor]
    warnings: List[ExplanationWarning] = Field(default_factory=list)
    historical_context: Optional[HistoricalContext] = None


class Metadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    model_version: str
    generated_at: datetime
    backend_version: str
    is_legacy_contract: bool
    debt_flags: List[str]


class ContratoExplicacion(BaseModel):
    version: str = "1.0.0"
    prediction_id: UUID | str
    sport: Sport
    market: Literal["over_under"]
    game: GameInfo
    prediction: PredictionData
    data_quality: DataQuality
    explanation: ExplanationData
    metadata: Metadata


ALERT_TO_WARNING_TYPE: Dict[str, str] = {
    "DQ-CRIT-01": "quality",
    "DQ-CRIT-02": "quality",
    "DQ-CRIT-03": "drift",
    "DQ-CRIT-04": "stale",
    "DQ-HIGH-01": "quality",
    "DQ-HIGH-02": "incomplete",
    "DQ-HIGH-03": "outlier",
    "DQ-HIGH-04": "coverage",
    "DQ-HIGH-05": "drift",
    "DQ-MED-01": "coverage",
    "DQ-MED-02": "coverage",
    "DQ-MED-03": "quality",
    "DQ-MED-04": "quality",
    "DQ-MED-05": "drift",
}


def _severity_to_warning(sev: str) -> str:
    sev_up = (sev or "").upper()
    if sev_up == "CRITICA":
        return "high"
    if sev_up == "ALTA":
        return "medium"
    return "low"


def _quality_flags_from_alertas(alertas: List[Dict[str, Any]]) -> List[QualityFlag]:
    flags: List[QualityFlag] = []
    for a in alertas:
        w_type = ALERT_TO_WARNING_TYPE.get(a.get("alert_id"), "quality")
        sev_raw = (a.get("severity") or "MEDIA").upper()
        sev = "critical" if sev_raw == "CRITICA" else ("high" if sev_raw == "ALTA" else "medium")
        flags.append(
            QualityFlag(
                type=w_type,
                severity=sev,
                message=a.get("title") or a.get("condition_text") or "Alerta de calidad activa",
            )
        )
    return flags


def _apply_quality_aware_confidence(numeric: float, level: str) -> tuple[str, float]:
    if level == "A":
        return ("high" if numeric >= 70 else "medium", numeric)
    if level == "B":
        return ("medium", min(numeric, 69.0))
    return ("low", min(numeric, 49.0))


def _debt_flags_for_contract(sport: str, level: str, flags: List[QualityFlag]) -> List[str]:
    debt = [
        "confidence_parcial_bloque_05",
        "contratos_legacy_coexistentes_bloque_05",
    ]
    if sport == "FOOTBALL" or any(f.type == "drift" for f in flags):
        debt.append("drift_futbol_parcial_alto_bloque_05")
    if level in {"B", "C"}:
        debt.append("quality_gate_activo")
    return debt


def construir_contrato(
    prediccion: Dict[str, Any],
    scorecard: Dict[str, Any],
    alertas: List[Dict[str, Any]],
    factores: List[Dict[str, Any]],
    historico: Optional[Dict[str, Any]] = None,
) -> ContratoExplicacion:
    """Construye contrato canónico quality-aware."""
    level = str(scorecard.get("nivel", "C")).upper()
    score = float(scorecard.get("score_final", 0.0))

    flags = _quality_flags_from_alertas(alertas)
    has_critical_warning = any(f.severity == "critical" for f in flags)
    if level == "A" and has_critical_warning:
        raise QualityCoherenceError("Nivel A no puede coexistir con warning crítico")

    base_conf = float(prediccion.get("confidence_numeric", 50.0))
    conf_level, conf_numeric = _apply_quality_aware_confidence(base_conf, level)

    warnings: List[ExplanationWarning] = [
        ExplanationWarning(
            type=ALERT_TO_WARNING_TYPE.get(a.get("alert_id"), "quality"),
            message=a.get("title") or a.get("condition_text") or "Advertencia de calidad",
            severity=_severity_to_warning(a.get("severity", "MEDIA")),
        )
        for a in alertas
    ]

    if level == "B":
        warnings.append(
            ExplanationWarning(
                type="quality",
                message="Algunos datos presentan calidad reducida",
                severity="medium",
            )
        )
    if level == "C":
        warnings.append(
            ExplanationWarning(
                type="quality",
                message="ADVERTENCIA: Calidad de datos insuficiente",
                severity="high",
            )
        )

    if prediccion.get("sport") == "FOOTBALL":
        warnings.append(
            ExplanationWarning(
                type="beta",
                message="Modelo en fase beta",
                severity="medium",
            )
        )

    top_factors = [TopFactor(**f) for f in factores[:5]]
    hist_model = HistoricalContext(**historico) if historico else None

    debt_flags = _debt_flags_for_contract(prediccion["sport"], level, flags)

    contrato = ContratoExplicacion(
        version="1.0.0",
        prediction_id=prediccion["prediction_id"],
        sport=prediccion["sport"],
        market="over_under",
        game=GameInfo(
            home_team=prediccion["home_team"],
            away_team=prediccion["away_team"],
            game_date=prediccion["game_date"],
            league=prediccion["league"],
        ),
        prediction=PredictionData(
            value=float(prediccion["value"]),
            unit=prediccion["unit"],
            line=float(prediccion["line"]),
            recommendation=prediccion["recommendation"],
            confidence=PredictionConfidence(
                level=conf_level,
                numeric=conf_numeric,
                interval=PredictionInterval(
                    lower=float(prediccion["interval_lower"]),
                    upper=float(prediccion["interval_upper"]),
                ),
            ),
        ),
        data_quality=DataQuality(score=score, level=level, flags=flags),
        explanation=ExplanationData(
            top_factors=top_factors,
            warnings=warnings,
            historical_context=hist_model,
        ),
        metadata=Metadata(
            model_version=str(prediccion.get("model_version", "unknown")),
            generated_at=datetime.now(timezone.utc),
            backend_version=str(prediccion.get("backend_version", "api-unknown")),
            is_legacy_contract=False,
            debt_flags=debt_flags,
        ),
    )
    return contrato


def adaptar_legacy(contrato_v1: ContratoExplicacion) -> Dict[str, Any]:
    """Adapta el contrato canónico a salida compatible legacy."""
    data = contrato_v1.model_dump(mode="json")
    data["metadata"]["is_legacy_contract"] = True
    return {
        "id": data["prediction_id"],
        "deporte": data["sport"],
        "mercado": data["market"],
        "equipo_local": data["game"]["home_team"],
        "equipo_visitante": data["game"]["away_team"],
        "fecha_partido": data["game"]["game_date"],
        "valor_predicho": data["prediction"]["value"],
        "linea": data["prediction"]["line"],
        "recomendacion": data["prediction"]["recommendation"].upper(),
        "confianza": data["prediction"]["confidence"]["numeric"],
        "calidad_score": data["data_quality"]["score"],
        "calidad_nivel": data["data_quality"]["level"],
        "warnings": data["explanation"]["warnings"],
        "metadata": data["metadata"],
    }
