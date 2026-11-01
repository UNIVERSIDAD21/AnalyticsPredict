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
from .cliente import ClienteESPN, ConsultaError, FuenteError, url_consulta
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
    atomico(run / "advertencias_estadisticas.jsonl", b"".join(
        (json.dumps({"source_game_id": r["source_game_id"], **warning, "evidencia": r["evidencia"]},
                    ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()
        for r in records for warning in r.get("incidencias_estadisticas", [])))
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
                                  ("partidos.jsonl", "partidos.csv", "cuarentena.jsonl", "checkpoint.jsonl",
                                   "pendientes.jsonl", "incidencias.jsonl", "advertencias_estadisticas.jsonl")}
    guardar_json(run / "reporte.json", report)
    names = [*report["sha256_archivos"], "reporte.json"]
    atomico(run / "SHA256SUMS", "".join(f"{sha256((run / n).read_bytes())}  {n}\n" for n in names).encode())


def ejecutar(client: ClienteESPN, *, desde: date, hasta: date, zona="America/Bogota",
             con_estadisticas=False, progreso=None, rondas=1, espera_rondas=15,
             checkpoint_cada=25) -> tuple[Path, dict, int]:
    """Escanea todo el rango y después reintenta únicamente consultas transitorias.

    Las respuestas crudas son el checkpoint durable de cada GET. Las instantáneas
    periódicas permiten inspeccionar resultados mientras sigue la ejecución.
    Repetir la orden reconstruye con el contrato actual desde el archivo verificado.
    """
    import math

    if not 1 <= rondas <= 10 or not 1 <= checkpoint_cada <= 1000:
        raise ValueError("Rondas (1..10) o frecuencia de checkpoint (1..1000) inválidas")
    if not math.isfinite(espera_rondas) or not 0 <= espera_rondas <= 60:
        raise ValueError("Espera entre rondas: 0..60 segundos")
    inicio, fin, days = ventana(desde, hasta, zona)
    run = client.archivo.root / "ejecuciones" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12])
    run.mkdir(parents=True, mode=0o700)
    for name in ("checkpoint.jsonl", "incidencias.jsonl", "pendientes.jsonl"):
        atomico(run / name, b"")
    records, quarantine, excluded = {}, [], set()
    seen, references, identities = set(), {}, {}
    pending, verified = {}, set()
    # Payloads usados para reintentar enriquecimientos; no se serializan en el informe.
    event_tasks = {}
    report = {**plan(desde, hasta, zona), "version_scraper": VERSION, "contrato": VERSION_CONTRATO,
              "modo": "OFFLINE" if client.offline else "HTTP", "estadisticas_solicitadas": con_estadisticas,
              "inicio_ejecucion_utc": datetime.now(timezone.utc).isoformat(),
              "ventanas_verificadas": [], "ventanas_sin_eventos": [], "eventos_observados": 0,
              "eventos_fuera_ventana": 0, "duplicados_identicos": 0, "estado": "EN_CURSO",
              "rondas_previstas": rondas, "rondas_ejecutadas": 0,
              "limite_cobertura": "Ventanas de ESPN procesadas, no censo independiente de todos los partidos reales.",
              "licencia_datos": "No acreditada por una respuesta HTTP; respetar términos del proveedor.",
              "error": None}
    exit_code = 0
    current_round = 0
    operations = 0
    last_snapshot = client.reloj()

    def reference(meta):
        references[(meta["url"], meta["sha256"], meta["observado_utc"])] = meta

    def age_for(day):
        today = client.ahora().astimezone(NY).date()
        # Históricos estables no caducan durante una reanudación días después.
        # Los siete días recientes sí se actualizan; --refresh fuerza todos.
        return None if day < today - timedelta(days=7) else (60 if day >= today else 86400)

    def failure(endpoint, parametro, day, exc, *, event=None, meta=None):
        key = (endpoint, parametro)
        previous = pending.get(key, {})
        item = {"endpoint": endpoint, "parametro": parametro, "dia_feed": day.isoformat(),
                "source_game_id": parametro if endpoint == "summary" else None,
                "url": url_consulta(endpoint, parametro), "error": str(exc),
                "http_status": getattr(exc, "http_status", None),
                "codigo": getattr(exc, "codigo", type(exc).__name__),
                "reintentar": isinstance(exc, ConsultaError) and exc.reintentar and not client.offline,
                "intentos_ronda": previous.get("intentos_ronda", 0) + 1,
                "ultima_ronda": current_round + 1,
                "observado_utc": client.ahora().isoformat()}
        if meta:
            item["evidencia"] = [meta]
        pending[key] = item
        if event is not None:
            event_tasks[key] = (event, meta, day)
        append_json(run / "incidencias.jsonl", item)

    def snapshot():
        nonlocal last_snapshot
        rows = sorted(records.values(), key=lambda r: (r["inicio_utc"], r["source_game_id"]))
        finals = [r for r in rows if r["final_completo"]]
        report.update({"actualizado_utc": client.ahora().isoformat(),
                       "partidos_exportados": len(rows), "finales_completos": len(finals),
                       "no_finales": len(rows) - len(finals), "incidencias_cuarentena": len(quarantine),
                       "ids_cuarentena": sorted(excluded), "ids_unicos_observados": len(seen),
                       "por_estado": dict(Counter(r["estado"] for r in rows)),
                       "por_fase": dict(Counter(r["fase"] for r in rows)),
                       "ventanas_verificadas": sorted(verified),
                       "ventanas_pendientes": [d.isoformat() for d in days if d.isoformat() not in verified],
                       "consultas_pendientes": len(pending),
                       "consultas_pendientes_reintentables": sum(v["reintentar"] for v in pending.values()),
                       "detalles_pendientes": sum(k[0] == "summary" for k in pending),
                       "recorrido_completo": len(verified) == len(days),
                       "resultados_pendientes": sum(k[0] == "summary" and k[1] not in records for k in pending),
                       "partidos_con_advertencias_estadisticas": sum(bool(r["incidencias_estadisticas"]) for r in rows),
                       "campos_estadisticos_apartados": sum(len(r["incidencias_estadisticas"]) for r in rows),
                       "contadores_http": dict(client.contadores), "exit_code": exit_code,
                       "observaciones_fuente": sorted(references.values(), key=lambda m: (m["url"], m["observado_utc"]))})
        coverage = Counter()
        for record in finals:
            for side, stats in record["estadisticas"].items():
                for key, value in stats.items():
                    coverage[f"{side}.{key}"] += int(value is not None)
        report["cobertura_estadisticas"] = {k: {"presentes": n, "finales": len(finals)} for k, n in sorted(coverage.items())}
        atomico(run / "pendientes.jsonl", b"".join(
            (json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n").encode() for _, v in sorted(pending.items())))
        exportar(run, rows, quarantine, report)
        last_snapshot = client.reloj()

    def tick(day):
        nonlocal operations
        operations += 1
        if operations % checkpoint_cada == 0 or client.reloj() - last_snapshot >= 60:
            snapshot()
        if progreso:
            progreso({"ejecucion": str(run), "ronda": current_round + 1,
                      "dia_feed": day.isoformat(), "ventanas": len(verified), "total": len(days),
                      "partidos_validos": len(records), "cuarentena": len(quarantine),
                      "consultas_pendientes": len(pending), **client.contadores})

    def process_event(event, meta, day, *, retry=False):
        eid, evidence = None, [meta]
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
                report["eventos_fuera_ventana"] += int(not retry)
                return
            if eid in excluded:
                return
            summary, smeta, record = None, None, None
            needs_periods = False
            try:
                record = normalizar(event)
            except ContratoError as exc:
                if exc.codigo != "PERIODOS_INCOMPLETOS":
                    raise
                needs_periods = True
            if needs_periods or (con_estadisticas and record["final_completo"]):
                key = ("summary", eid)
                try:
                    summary, smeta = client.obtener("summary", eid, max_age=age_for(day))
                    reference(smeta)
                    evidence.append(smeta)
                    # Primero validar identidad y resultado; un error estadístico no borra cuartos válidos.
                    core = normalizar(event, summary, incluir_estadisticas=False)
                    record = core
                    try:
                        record = normalizar(event, summary, aislar_estadisticas_invalidas=True)
                    except ContratoError as exc:
                        failure("summary", eid, day, exc, event=event, meta=meta)
                    else:
                        pending.pop(key, None)
                        event_tasks.pop(key, None)
                except (ConsultaError, ContratoError) as exc:
                    failure("summary", eid, day, exc, event=event, meta=meta)
                if record is None:
                    return  # Resultado sin cuartos: pendiente, nunca fabricar un final.
            if record["final_completo"]:
                exigir(all(dt <= instante(m["observado_utc"]) for m in evidence),
                       "FINAL_CON_INICIO_FUTURO", "inicio_utc/observado_utc")
            if eid in records:
                previous = records[eid]
                core_keys = set(record) - {"estadisticas", "evidencia", "incidencias_estadisticas"}
                exigir(all(previous[k] == record[k] for k in core_keys), "DUPLICADO_CONFLICTIVO", "source_game_id")
                if record["estadisticas"] is not None:
                    for side, values in record["estadisticas"].items():
                        for key, value in values.items():
                            old = previous["estadisticas"][side][key]
                            exigir(old is None or value is None or old == value,
                                   "DUPLICADO_CONFLICTIVO", f"estadisticas.{side}.{key}")
                            if value is None:
                                values[key] = old
                report["duplicados_identicos"] += int(not retry)
                evidence.extend(m for m in previous["evidencia"] if m not in evidence)
            record["evidencia"] = evidence
            records[eid] = record
        except ContratoError as exc:
            if eid is not None:
                excluded.add(eid)
                previous = records.pop(eid, None)
                if previous:
                    evidence.extend(m for m in previous["evidencia"] if m not in evidence)
                pending.pop(("summary", eid), None)
                event_tasks.pop(("summary", eid), None)
            quarantine.append({"source_game_id": eid, "dia_feed": day.isoformat(),
                               "codigo": exc.codigo, "campo": exc.campo, "evidencia": evidence})

    try:
        snapshot()  # El directorio y el estado son visibles desde el comienzo.
        for current_round in range(rondas):
            report["rondas_ejecutadas"] = current_round + 1
            if current_round:
                work_days = [date.fromisoformat(v["dia_feed"]) for k, v in pending.items()
                             if k[0] == "scoreboard" and v["reintentar"]]
                work_events = [k for k, v in pending.items() if k[0] == "summary" and v["reintentar"]]
                if not work_days and not work_events:
                    report["rondas_ejecutadas"] = current_round
                    break
                if progreso:
                    progreso({"estado": "ESPERANDO_REINTENTO", "segundos": espera_rondas,
                              "consultas": len(work_days) + len(work_events)})
                client.dormir(espera_rondas)
            else:
                work_days, work_events = days, []
            for day in work_days:
                param = day.strftime("%Y%m%d")
                try:
                    payload, meta = client.obtener("scoreboard", param, max_age=age_for(day))
                    reference(meta)
                    eventos = eventos_scoreboard(payload)
                except (ConsultaError, ContratoError) as exc:
                    failure("scoreboard", param, day, exc)
                    tick(day)
                    continue
                pending.pop(("scoreboard", param), None)
                report["eventos_observados"] += len(eventos)
                if not eventos:
                    report["ventanas_sin_eventos"].append(day.isoformat())
                for event in eventos:
                    process_event(event, meta, day)
                verified.add(day.isoformat())
                append_json(run / "checkpoint.jsonl", {"dia_feed": day.isoformat(), "eventos": len(eventos),
                            "sha256": meta["sha256"], "observado_utc": meta["observado_utc"],
                            "registros_validos_acumulados": len(records), "incidencias_acumuladas": len(quarantine)})
                tick(day)
            for key in work_events:
                if key in pending and pending[key]["ultima_ronda"] < current_round + 1:
                    event, meta, day = event_tasks[key]
                    process_event(event, meta, day, retry=True)
                    tick(day)
            snapshot()
        resultados_pendientes = any(k[0] == "summary" and k[1] not in records for k in pending)
        if len(verified) < len(days) or resultados_pendientes:
            report["estado"], report["error"], exit_code = "INCOMPLETO", "Hay consultas pendientes; consultar pendientes.jsonl", 3
        elif pending or quarantine or any(r["incidencias_estadisticas"] for r in records.values()):
            report["estado"], report["error"], exit_code = "COMPLETO_CON_INCIDENCIAS", None, 2
        else:
            report["estado"], exit_code = "COMPLETO_EN_VENTANA_ESPN", 0
    except KeyboardInterrupt:
        report["estado"], report["error"], exit_code = "INTERRUMPIDO", "Interrupción del operador o SIGTERM; reanudación disponible", 130
    except (FuenteError, ArchivoError, OSError) as exc:
        report["estado"], report["error"], exit_code = "INCOMPLETO", str(exc), 3
    except Exception as exc:
        report["estado"], report["error"], exit_code = "ERROR_INTERNO", f"{type(exc).__name__}: {exc}", 4
    finally:
        report["fin_ejecucion_utc"] = datetime.now(timezone.utc).isoformat()
        snapshot()
    return run, report, exit_code
