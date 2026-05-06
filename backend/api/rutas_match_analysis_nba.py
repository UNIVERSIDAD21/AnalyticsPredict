# -*- coding: utf-8 -*-
"""Endpoint técnico interno para análisis previo de partido NBA."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StrictFloat, StrictInt, field_validator

from scripts.generar_analisis_partido_nba import build_analysis, render_markdown, validate_markets
from .dependencias import UsuarioActual, obtener_usuario_actual

router = APIRouter(prefix="/api/nba", tags=["NBA Match Analysis"])

SourceType = Literal["REAL_MARKET", "DERIVED_FROM_TOTAL_SPREAD", "TECHNICAL_ESTIMATE", "MANUAL_INPUT"]


class MarketInput(BaseModel):
    market: str
    line: StrictFloat | StrictInt
    over_odds: StrictFloat | StrictInt | None = None
    under_odds: StrictFloat | StrictInt | None = None
    source: str = Field(min_length=1)
    source_type: SourceType
    source_url: str | None = None
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def notes_obligatorias_si_no_real(cls, value: str | None, info):
        source_type = info.data.get("source_type")
        if source_type and source_type != "REAL_MARKET" and not (value or "").strip():
            raise ValueError("notes es obligatorio cuando source_type no es REAL_MARKET")
        return value


class MatchAnalysisRequest(BaseModel):
    home: str = Field(min_length=1)
    away: str = Field(min_length=1)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    markets: list[MarketInput] = Field(default_factory=list)


@router.post("/match-analysis")
def generar_match_analysis(
    payload: MatchAnalysisRequest,
    _usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> dict[str, Any]:
    """Genera análisis técnico interno sin picks, stakes ni recomendaciones."""
    try:
        markets = [m.model_dump() for m in payload.markets]
        validate_markets(markets)
        analysis, _slug = build_analysis(payload.home, payload.away, payload.date, None)
        # Reusar evaluación completa escribiendo markets temporal en memoria no está soportado por build_analysis;
        # por contrato interno, inyectamos evaluaciones recreando archivo temporal controlado.
        import tempfile, json
        from pathlib import Path
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump({"markets": markets}, fh, ensure_ascii=False)
            temp_path = Path(fh.name)
        try:
            analysis, _slug = build_analysis(payload.home, payload.away, payload.date, temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
        external_summary = render_markdown(analysis).split("## Resumen para análisis externo", 1)[-1].strip()
        return {
            "ok": True,
            "metadata": analysis["metadata"],
            "teams": analysis["partido"],
            "samples": analysis["muestras"],
            "combined_metrics": analysis["comparaciones"],
            "market_evaluations": analysis["evaluacion_mercados"],
            "data_quality": analysis["muestras"].get("calidad_datos", {}),
            "warnings": analysis.get("advertencias", []),
            "external_summary": external_summary,
            "generated_files": None,
            "policy": {
                "no_picks": True,
                "no_stake": True,
                "no_betting_recommendations": True,
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SystemExit as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
