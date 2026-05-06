#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida por lote la generación de análisis previo NBA."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BATCH = ROOT / "reports" / "match_markets" / "lote_validacion_nba_2026-05-05.json"
OUT_JSON = ROOT / "reports" / "data_quality" / "nba_match_analysis_batch_validation.json"
OUT_MD = ROOT / "reports" / "data_quality" / "nba_match_analysis_batch_validation.md"
TMP_MARKETS_DIR = ROOT / "reports" / "match_markets" / "generated_batch"
ANALYSIS_SCRIPT = ROOT / "backend" / "scripts" / "generar_analisis_partido_nba.py"
PROHIBITED_TERMS = ["apuesta segura", "value bet", "pick", "stake"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_summary(md_text: str) -> str:
    marker = "## Resumen para análisis externo"
    if marker not in md_text:
        return ""
    return md_text[md_text.index(marker):].strip()


def has_prohibited_language(text: str) -> list[str]:
    low = text.lower()
    # Permitir negaciones/avisos de no recomendación; bloquear lenguaje afirmativo problemático.
    hits = []
    for term in PROHIBITED_TERMS:
        if term in low:
            if term in {"pick", "stake"} and ("no calcula stake" in low or "no gener" in low):
                continue
            hits.append(term)
    return hits


def run_match(match: dict[str, Any]) -> dict[str, Any]:
    match_id = match["id"]
    markets_path = TMP_MARKETS_DIR / f"{match_id}_markets.json"
    write_json(markets_path, {"metadata": {k: v for k, v in match.items() if k != "markets"}, "markets": match.get("markets", [])})
    cmd = [
        sys.executable,
        str(ANALYSIS_SCRIPT),
        "--home",
        match["home"],
        "--away",
        match["away"],
        "--date",
        match["date"],
        "--markets",
        str(markets_path.relative_to(ROOT)),
    ]
    result = {
        "id": match_id,
        "home": match["home"],
        "away": match["away"],
        "date": match["date"],
        "markets_file": str(markets_path.relative_to(ROOT)),
        "command": " ".join(cmd),
        "status": "ERROR",
        "warnings": [],
        "generated": {},
        "market_source_types": Counter(),
    }
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
    result["stdout"] = proc.stdout.strip()
    result["stderr"] = proc.stderr.strip()
    if proc.returncode != 0:
        result["warnings"].append(f"script falló con código {proc.returncode}")
        return result
    try:
        generated = json.loads(proc.stdout)
        result["generated"] = generated
        json_path = ROOT / generated["json"]
        md_path = ROOT / generated["markdown"]
        analysis = load_json(json_path)
        md_text = md_path.read_text(encoding="utf-8")
        result["summary_external"] = extract_summary(md_text)
        quality = analysis.get("muestras", {}).get("calidad_datos", {})
        result["quality"] = {
            "candidatas": quality.get("candidatas_total"),
            "usadas": quality.get("usadas_total"),
            "excluidas": quality.get("excluidas_total"),
            "porcentaje_excluido": quality.get("porcentaje_excluido"),
        }
        if (quality.get("porcentaje_excluido") or 0) > 10:
            result["warnings"].append("más de 10% de exclusiones")
        if analysis.get("advertencias"):
            result["warnings"].extend(analysis["advertencias"])
        market_eval = analysis.get("evaluacion_mercados", [])
        result["markets"] = []
        for m in market_eval:
            st = m.get("source_type") or "MANUAL_INPUT"
            result["market_source_types"][st] += 1
            if st != "REAL_MARKET":
                result["warnings"].append(f"línea no real en {m.get('market')}: {st}")
            if not m.get("evaluable", True):
                result["warnings"].append(f"mercado no evaluable: {m.get('market')}")
            if any((isinstance(w, dict) and w.get("code") == "RECENT_FULL_SAMPLE_DIVERGENCE") or ("diferencia fuerte" in str(w)) for w in m.get("advertencias", [])):
                result["warnings"].append(f"diferencia fuerte reciente/completa en {m.get('market')}")
            result["markets"].append({
                "market": m.get("market"),
                "source_type": st,
                "clasificacion": m.get("clasificacion"),
                "advertencias": m.get("advertencias", []),
            })
        bad_terms = has_prohibited_language(md_text)
        if bad_terms:
            result["warnings"].append(f"lenguaje prohibido detectado: {bad_terms}")
        result["status"] = "WARNING" if result["warnings"] else "OK"
    except Exception as exc:  # noqa: BLE001
        result["status"] = "ERROR"
        result["warnings"].append(f"error leyendo salida generada: {exc}")
    result["market_source_types"] = dict(result["market_source_types"])
    return result


def render_md(data: dict[str, Any]) -> str:
    lines = [
        "# Validación por lote de análisis de partidos NBA",
        "",
        f"Generado: {data['generated_at']}",
        "",
        "## Resumen",
        f"- Total partidos validados: {data['totals']['total']}",
        f"- OK: {data['totals']['OK']}",
        f"- WARNING: {data['totals']['WARNING']}",
        f"- ERROR: {data['totals']['ERROR']}",
        "",
        "## Principales advertencias",
    ]
    if data["warning_counts"]:
        for w, c in sorted(data["warning_counts"].items(), key=lambda x: (-x[1], x[0]))[:30]:
            lines.append(f"- {w}: {c}")
    else:
        lines.append("- Sin advertencias.")
    lines += ["", "## Resultado por partido", "", "| Estado | Partido | Fecha | Candidatas | Usadas | Excluidas | JSON | Markdown |", "|---|---|---|---:|---:|---:|---|---|"]
    for r in data["results"]:
        q = r.get("quality", {})
        g = r.get("generated", {})
        lines.append(f"| {r['status']} | {r['home']} vs {r['away']} | {r['date']} | {q.get('candidatas','N/D')} | {q.get('usadas','N/D')} | {q.get('excluidas','N/D')} | `{g.get('json','')}` | `{g.get('markdown','')}` |")
    lines += ["", "## Detalle de warnings por partido"]
    for r in data["results"]:
        lines += ["", f"### {r['id']} — {r['status']}"]
        if r.get("warnings"):
            lines.extend(f"- {json.dumps(w, ensure_ascii=False) if isinstance(w, dict) else w}" for w in r["warnings"])
        else:
            lines.append("- Sin warnings.")
        lines.append("- Source types: " + json.dumps(r.get("market_source_types", {}), ensure_ascii=False))
    lines += ["", "## Resúmenes para análisis externo"]
    for r in data["results"]:
        lines += ["", f"### {r['id']}", r.get("summary_external", "N/D")]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--batch", default=str(DEFAULT_BATCH))
    args = parser.parse_args()
    batch = load_json(Path(args.batch))
    results = [run_match(m) for m in batch.get("matches", [])]
    totals = Counter(r["status"] for r in results)
    warning_counts = Counter()
    for r in results:
        warning_counts.update(json.dumps(w, ensure_ascii=False, sort_keys=True) if isinstance(w, dict) else str(w) for w in r.get("warnings", []))
    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_file": str(Path(args.batch).relative_to(ROOT) if Path(args.batch).is_absolute() and ROOT in Path(args.batch).parents else args.batch),
        "totals": {"total": len(results), "OK": totals.get("OK", 0), "WARNING": totals.get("WARNING", 0), "ERROR": totals.get("ERROR", 0)},
        "warning_counts": dict(warning_counts),
        "results": results,
    }
    write_json(OUT_JSON, data)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(data), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON.relative_to(ROOT)), "markdown": str(OUT_MD.relative_to(ROOT)), "totals": data["totals"]}, indent=2, ensure_ascii=False))
    return 1 if totals.get("ERROR", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
