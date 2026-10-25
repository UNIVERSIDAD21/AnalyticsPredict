"""Ventanas acotadas, deduplicación por ID, cuarentena y reportes reproducibles."""
from __future__ import annotations

import csv
import io
import json
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from . import VERSION
from .archivo import ArchivoError, append_json, atomico, guardar_json, sha256
from .cliente import ClienteESPN, FuenteError
from .contrato import (ContratoError, VERSION_CONTRATO, competicion, exigir, eventos_scoreboard,
                       identificador, instante, lados, normalizar, objeto)

NY = ZoneInfo("America/New_York")


def ventana(desde: date, hasta: date, zona: str) -> tuple[datetime, datetime, list[date]]:
    if desde > hasta or desde.year < 2006 or (hasta - desde).days > 3660:
        raise ValueError("Ventana inválida: desde 2006, ordenada y como máximo 3661 días")
    tz = ZoneInfo(zona)
    inicio = datetime.combine(desde, time.min, tz).astimezone(timezone.utc)
    fin = datetime.combine(hasta + timedelta(days=1), time.min, tz).astimezone(timezone.utc)
    # El feed indexa por día Eastern; consultar también el día limítrofe cuando corresponda.
    first = inicio.astimezone(NY).date()
    last = (fin - timedelta(microseconds=1)).astimezone(NY).date()
    days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    return inicio, fin, days


def plan(desde: date, hasta: date, zona: str) -> dict:
    inicio, fin, days = ventana(desde, hasta, zona)
    return {"competicion": "wnba", "desde": desde.isoformat(), "hasta": hasta.isoformat(),
            "zona": zona, "inicio_utc_inclusivo": inicio.isoformat(), "fin_utc_exclusivo": fin.isoformat(),
            "ventanas_espn": [d.isoformat() for d in days], "scoreboards_previstos": len(days),
            "summaries_previstos": "N/D: depende de finales sin cuartos y de --estadisticas",
            "escribe_bd": False, "entrena": False, "cobertura_historica_certificada": False}


def celda_csv(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def exportar(run: Path, records: list, quarantine: list, report: dict) -> None:
    atomico(run / "partidos.jsonl", b"".join(
        (json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode() for r in records))
    atomico(run / "cuarentena.jsonl", b"".join(
        (json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode() for r in quarantine))
    stream = io.StringIO(newline="")
    fields = list(records[0]) if records else ["contrato", "competicion", "source_game_id", "inicio_utc", "estado"]
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in records:
        writer.writerow({key: celda_csv(row.get(key)) for key in fields})
    atomico(run / "partidos.csv", stream.getvalue().encode("utf-8"))
    report["sha256_archivos"] = {name: sha256((run / name).read_bytes()) for name in
                                  ("partidos.jsonl", "partidos.csv", "cuarentena.jsonl", "checkpoint.jsonl")}
    guardar_json(run / "reporte.json", report)
    names = [*report["sha256_archivos"], "reporte.json"]
    atomico(run / "SHA256SUMS", "".join(f"{sha256((run / n).read_bytes())}  {n}\n" for n in names).encode())


def ejecutar(client: ClienteESPN, *, desde: date, hasta: date, zona="America/Bogota",
             con_estadisticas=False, progreso=None) -> tuple[Path, dict, int]:
    inicio, fin, days = ventana(desde, hasta, zona)
    run = client.archivo.root / "ejecuciones" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12])
    run.mkdir(parents=True, mode=0o700)
    atomico(run / "checkpoint.jsonl", b"")
    records, quarantine, excluded = {}, [], set()
    seen, references, identities = set(), {}, {}
    report = {**plan(desde, hasta, zona), "version_scraper": VERSION, "contrato": VERSION_CONTRATO,
              "modo": "OFFLINE" if client.offline else "HTTP", "estadisticas_solicitadas": con_estadisticas,
              "inicio_ejecucion_utc": datetime.now(timezone.utc).isoformat(),
              "ventanas_verificadas": [], "ventanas_sin_eventos": [], "eventos_observados": 0,
              "eventos_fuera_ventana": 0, "duplicados_identicos": 0, "estado": "EN_CURSO",
              "limite_cobertura": "Ventanas de ESPN procesadas, no censo independiente de todos los partidos reales.",
              "licencia_datos": "No acreditada por una respuesta HTTP; respetar términos del proveedor.",
              "error": None}
    exit_code = 0
    try:
        for day in days:
            age = 60 if day >= client.ahora().astimezone(NY).date() else 86400
            payload, meta = client.obtener("scoreboard", day.strftime("%Y%m%d"), max_age=age)
            references[(meta["url"], meta["sha256"], meta["observado_utc"])] = meta
            eventos = eventos_scoreboard(payload)
            report["eventos_observados"] += len(eventos)
            if not eventos:
                report["ventanas_sin_eventos"].append(day.isoformat())
            for event in eventos:
                eid = None
                evidence = [meta]
                try:
                    objeto(event, "event")
                    eid = identificador(event.get("id"), "event.id")
                    seen.add(eid)
                    exigir(event.get("uid") == f"s:40~l:59~e:{eid}", "OTRA_LIGA", "event.uid")
                    dt = instante(event.get("date"))
                    teams = lados(competicion(event))
                    identity = (dt.isoformat(), str(teams["home"]["team"]["id"]), str(teams["away"]["team"]["id"]))
                    if eid in identities:
                        exigir(identities[eid] == identity, "IDENTIDAD_CAMBIANTE_ENTRE_VENTANAS", "event")
                    identities[eid] = identity
                    if not inicio <= dt < fin:
                        report["eventos_fuera_ventana"] += 1
                        continue
                    summary = None
                    try:
                        record = normalizar(event)
                    except ContratoError as exc:
                        if exc.codigo != "PERIODOS_INCOMPLETOS":
                            raise
                        summary, smeta = client.obtener("summary", eid)
                        evidence.append(smeta)
                        references[(smeta["url"], smeta["sha256"], smeta["observado_utc"])] = smeta
                        record = normalizar(event, summary)
                    if con_estadisticas and record["final_completo"] and summary is None:
                        summary, smeta = client.obtener("summary", eid)
                        evidence.append(smeta)
                        references[(smeta["url"], smeta["sha256"], smeta["observado_utc"])] = smeta
                        record = normalizar(event, summary)
                    if record["final_completo"]:
                        exigir(all(dt <= instante(m["observado_utc"]) for m in evidence),
                               "FINAL_CON_INICIO_FUTURO", "inicio_utc/observado_utc")
                    # No se elige silenciosamente una de dos versiones contradictorias del mismo ID.
                    if eid in records:
                        previous = {k: v for k, v in records[eid].items() if k != "evidencia"}
                        exigir(previous == record, "DUPLICADO_CONFLICTIVO", "source_game_id")
                        report["duplicados_identicos"] += 1
                        records[eid]["evidencia"].extend(m for m in evidence if m not in records[eid]["evidencia"])
                    elif eid not in excluded:
                        record["evidencia"] = evidence
                        records[eid] = record
                except ContratoError as exc:
                    if eid is not None:
                        excluded.add(eid)
                        previous = records.pop(eid, None)
                        if previous:
                            evidence.extend(m for m in previous["evidencia"] if m not in evidence)
                    quarantine.append({"source_game_id": eid, "dia_feed": day.isoformat(),
                                       "codigo": exc.codigo, "campo": exc.campo, "evidencia": evidence})
            report["ventanas_verificadas"].append(day.isoformat())
            append_json(run / "checkpoint.jsonl", {"dia_feed": day.isoformat(), "eventos": len(eventos),
                        "sha256": meta["sha256"], "observado_utc": meta["observado_utc"],
                        "registros_validos_acumulados": len(records), "incidencias_acumuladas": len(quarantine)})
            if progreso:
                progreso({"ventanas": len(report["ventanas_verificadas"]), "total": len(days),
                          "partidos_validos": len(records), "cuarentena": len(quarantine)})
        report["estado"] = "CON_CUARENTENA" if quarantine else "COMPLETO_EN_VENTANA_ESPN"
        exit_code = 2 if quarantine else 0
    except KeyboardInterrupt:
        report["estado"], report["error"], exit_code = "INTERRUMPIDO", "Interrupción del operador", 130
    except (FuenteError, ArchivoError, ContratoError, OSError) as exc:
        report["estado"], report["error"], exit_code = "INCOMPLETO", str(exc), 3
    except Exception as exc:
        report["estado"], report["error"], exit_code = "ERROR_INTERNO", type(exc).__name__, 4
    finally:
        rows = sorted(records.values(), key=lambda r: (r["inicio_utc"], r["source_game_id"]))
        finals = [r for r in rows if r["final_completo"]]
        report.update({"fin_ejecucion_utc": datetime.now(timezone.utc).isoformat(),
                       "partidos_exportados": len(rows), "finales_completos": len(finals),
                       "no_finales": len(rows) - len(finals), "incidencias_cuarentena": len(quarantine),
                       "ids_cuarentena": sorted(excluded), "ids_unicos_observados": len(seen),
                       "por_estado": dict(Counter(r["estado"] for r in rows)),
                       "por_fase": dict(Counter(r["fase"] for r in rows)),
                       "ventanas_pendientes": [d.isoformat() for d in days if d.isoformat() not in report["ventanas_verificadas"]],
                       "contadores_http": dict(client.contadores), "exit_code": exit_code,
                       "observaciones_fuente": sorted(references.values(), key=lambda m: (m["url"], m["observado_utc"]))})
        # Numerador y denominador campo a campo; nunca equiparar NULL con cero.
        coverage = Counter()
        for record in finals:
            for side, stats in record["estadisticas"].items():
                for key, value in stats.items():
                    coverage[f"{side}.{key}"] += int(value is not None)
        report["cobertura_estadisticas"] = {k: {"presentes": n, "finales": len(finals)} for k, n in sorted(coverage.items())}
        exportar(run, rows, quarantine, report)
    return run, report, exit_code
