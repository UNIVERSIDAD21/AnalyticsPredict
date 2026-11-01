"""Recorrido mensual LATAM, recuperación por consulta y exportaciones verificables."""

from __future__ import annotations

import calendar
import csv
import io
import json
import math
from collections import Counter, deque
from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from . import VERSION
from .ligas import ARGENTINA
from .archivo import ArchivoError, append_json, atomico, guardar_json, sha256
from .cliente import ConsultaError, FuenteError, url_consulta
from .contrato import (
    ContratoError,
    METRICAS,
    PERIODOS,
    REQUERIDOS,
    competicion,
    enriquecer,
    eventos_scoreboard,
    exigir,
    identificador,
    instante,
    lados,
    normalizar,
    objeto,
)

NY = ZoneInfo("America/New_York")
CORE = (
    "source_game_id",
    "inicio_utc",
    "temporada",
    "season_type_fuente",
    "fase_fuente",
    "estado_fuente",
    "local_id_fuente",
    "visitante_id_fuente",
    "local_goles",
    "visitante_goles",
)
COBERTURA = [
    f"{side}_{k}" for side in ("local", "visitante") for k in ("goles", *METRICAS)
] + PERIODOS


def ventana(desde, hasta, zona):
    if desde > hasta or desde.year < 1996 or (hasta - desde).days > 3660:
        raise ValueError("Rango desde 1996, ordenado y de como máximo 3661 días")
    tz = ZoneInfo(zona)
    start = datetime.combine(desde, time.min, tz).astimezone(timezone.utc)
    end = datetime.combine(hasta + timedelta(days=1), time.min, tz).astimezone(timezone.utc)
    first = start.astimezone(NY).date()
    last = (end - timedelta(microseconds=1)).astimezone(NY).date()
    month = first.replace(day=1)
    months = []
    while month <= last:
        months.append(month.strftime("%Y%m"))
        month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, end, first, last, months


def plan(desde, hasta, zona="America/Bogota", torneo=ARGENTINA):
    start, end, first, last, months = ventana(desde, hasta, zona)
    return {
        "competicion": torneo.codigo,
        "pais": torneo.pais,
        "torneo_nombre": torneo.nombre,
        "liga_espn": torneo.slug,
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "zona": zona,
        "inicio_utc_inclusivo": start.isoformat(),
        "fin_utc_exclusivo": end.isoformat(),
        "ventanas_espn": months,
        "ventanas_previstas": len(months),
        "unidad_ventana": "MES_ESPN_EASTERN",
        "expansion_diaria": "Automática si una respuesta mensual puede estar truncada",
        "estadisticas_por_defecto": True,
        "escribe_bd": False,
        "entrena": False,
        "cobertura_historica_certificada": False,
    }


def celda(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: celda(row.get(k)) for k in fields})
    return stream.getvalue().encode("utf-8")


def coverage(rows):
    finals = [r for r in rows if r["final_completo"]]
    counts = {k: sum(r[k] is not None for r in finals) for k in COBERTURA}
    return {
        "partidos": len(rows),
        "finales": len(finals),
        "no_finales": len(rows) - len(finals),
        "finales_con_estadisticas_completas": sum(r["estadisticas_completas"] for r in finals),
        "campos": {
            k: {
                "presentes": n,
                "finales": len(finals),
                "porcentaje": round(100 * n / len(finals), 2) if finals else None,
            }
            for k, n in counts.items()
        },
    }


def exportar(run, records, quarantine, pending, report):
    rows = sorted(records.values(), key=lambda r: (r["inicio_utc"], r["source_game_id"]))
    fields = (
        list(rows[0])
        if rows
        else ["contrato", "competicion", "source_game_id", "inicio_utc", "estado"]
    )
    names = []
    for name, selected in [
        ("partidos", rows),
        ("partidos_finales", [r for r in rows if r["final_completo"]]),
        (
            "partidos_completos",
            [r for r in rows if r["final_completo"] and r["estadisticas_completas"]],
        ),
    ]:
        atomico(run / f"{name}.csv", csv_bytes(selected, fields))
        names.append(f"{name}.csv")
    atomico(
        run / "partidos.jsonl",
        b"".join(
            (json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()
            for r in rows
        ),
    )
    names.append("partidos.jsonl")
    atomico(
        run / "cuarentena.jsonl",
        b"".join(
            (json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode() for r in quarantine
        ),
    )
    names.append("cuarentena.jsonl")
    atomico(
        run / "pendientes.jsonl",
        b"".join(
            (json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode()
            for _, r in sorted(pending.items())
        ),
    )
    names.append("pendientes.jsonl")
    warnings = [
        {"source_game_id": r["source_game_id"], **w, "evidencia": r["evidencia"]}
        for r in rows
        for w in r["incidencias"]
    ]
    atomico(
        run / "advertencias.jsonl",
        b"".join(
            (json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode() for r in warnings
        ),
    )
    names.append("advertencias.jsonl")
    report["cobertura"] = coverage(rows)
    years = sorted(set(range(int(report["desde"][:4]), int(report["hasta"][:4]) + 1)) | {r["temporada"] for r in rows})
    report["cobertura_por_temporada"] = {
        str(y): coverage([r for r in rows if r["temporada"] == y]) for y in years
    }
    table = []
    for year, cov in report["cobertura_por_temporada"].items():
        row = {"temporada": year, **{k: v for k, v in cov.items() if k != "campos"}}
        row.update({k + "_presentes": v["presentes"] for k, v in cov["campos"].items()})
        table.append(row)
    atomico(
        run / "cobertura_por_temporada.csv",
        csv_bytes(table, list(table[0]) if table else ["temporada", "finales"]),
    )
    names.append("cobertura_por_temporada.csv")
    names += ["checkpoint.jsonl", "incidencias.jsonl"]
    report["sha256_archivos"] = {n: sha256((run / n).read_bytes()) for n in names}
    guardar_json(run / "reporte.json", report)
    names.append("reporte.json")
    atomico(
        run / "SHA256SUMS",
        "".join(f"{sha256((run/n).read_bytes())}  {n}\n" for n in names).encode(),
    )
    guardar_json(
        run.parent.parent / "ultima_ejecucion.json",
        {
            "ejecucion": run.name,
            "estado": report["estado"],
            "reporte": str(run / "reporte.json"),
            "csv": str(run / "partidos.csv"),
        },
    )


def ejecutar(
    client,
    *,
    desde,
    hasta,
    zona="America/Bogota",
    con_estadisticas=True,
    rondas=3,
    espera_rondas=15,
    checkpoint_cada=25,
    progreso=None,
):
    if not 1 <= rondas <= 10 or not 1 <= checkpoint_cada <= 1000:
        raise ValueError("Rondas 1..10 y checkpoint 1..1000")
    if not math.isfinite(espera_rondas) or not 0 <= espera_rondas <= 60:
        raise ValueError("Espera entre rondas 0..60 s")
    torneo = client.torneo
    start, end, first, last, months = ventana(desde, hasta, zona)
    run = (
        client.archivo.root
        / "ejecuciones"
        / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12])
    )
    run.mkdir(parents=True, mode=0o700)
    for name in ("checkpoint.jsonl", "incidencias.jsonl"):
        atomico(run / name, b"")
    records = {}
    quarantine = []
    excluded = set()
    pending = {}
    tasks = {}
    identities = {}
    refs = {}
    verified = set()
    empty = set()
    children = {m: [m] for m in months}
    seen = set()
    operations = 0
    last_snapshot = client.reloj()
    current_round = 0
    code = 0
    report = {
        **plan(desde, hasta, zona, torneo),
        "version_scraper": VERSION,
        "contrato": "espn_latam_v1",
        "modo": "OFFLINE" if client.offline else "HTTP",
        "estadisticas_solicitadas": con_estadisticas,
        "inicio_ejecucion_utc": client.ahora().isoformat(),
        "estado": "EN_CURSO",
        "error": None,
        "rondas_ejecutadas": 0,
        "duplicados_identicos": 0,
        "eventos_observados": 0,
        "eventos_fuera_ventana": 0,
        "limite_cobertura": "Recorrido de los feeds ESPN; no equivale a un censo independiente de todos los partidos reales.",
    }

    def reference(meta):
        refs[(meta["url"], meta["sha256"], meta["observado_utc"])] = meta

    def age(param):
        day = date(
            int(param[:4]),
            int(param[4:6]),
            (
                int(param[6:])
                if len(param) == 8
                else calendar.monthrange(int(param[:4]), int(param[4:6]))[1]
            ),
        )
        today = client.ahora().astimezone(NY).date()
        return None if day < today - timedelta(days=7) else 60 if day >= today else 86400

    def failure(endpoint, param, exc, *, event=None, meta=None, window=None, fields=None):
        key = (endpoint, param)
        old = pending.get(key, {})
        item = {
            "endpoint": endpoint,
            "parametro": param,
            "source_game_id": param if endpoint == "summary" else None,
            "ventana": window,
            "url": url_consulta(endpoint, param, torneo),
            "codigo": getattr(exc, "codigo", type(exc).__name__),
            "error": str(exc),
            "http_status": getattr(exc, "http_status", None),
            "reintentar": isinstance(exc, ConsultaError) and exc.reintentar and not client.offline,
            "ultima_ronda": current_round + 1,
            "intentos_ronda": old.get("intentos_ronda", 0) + 1,
            "observado_utc": client.ahora().isoformat(),
            "campos_faltantes": fields or [],
        }
        if meta:
            item["evidencia"] = [meta]
        pending[key] = item
        if event is not None:
            tasks[key] = (event, meta, window)
        append_json(run / "incidencias.jsonl", item)

    def snapshot():
        nonlocal last_snapshot
        done = [m for m in months if all(q in verified for q in children[m])]
        finals = [r for r in records.values() if r["final_completo"]]
        report.update(
            {
                "actualizado_utc": client.ahora().isoformat(),
                "partidos_exportados": len(records),
                "finales_completos": len(finals),
                "finales_con_estadisticas_completas": sum(
                    r["estadisticas_completas"] for r in finals
                ),
                "no_finales": len(records) - len(finals),
                "ids_unicos_observados": len(seen),
                "ventanas_verificadas": done,
                "ventanas_pendientes": [m for m in months if m not in done],
                "meses_expandidos": {m: q for m, q in children.items() if q != [m]},
                "consultas_scoreboard_verificadas": sorted(verified),
                "consultas_sin_eventos": sorted(empty),
                "recorrido_completo": len(done) == len(months),
                "consultas_pendientes": len(pending),
                "detalles_pendientes": sum(k[0] == "summary" for k in pending),
                "resultados_pendientes": sum(
                    k[0] == "summary" and k[1] not in records for k in pending
                ),
                "consultas_pendientes_reintentables": sum(
                    v["reintentar"] for v in pending.values()
                ),
                "incidencias_cuarentena": len(quarantine),
                "ids_cuarentena": sorted(excluded),
                "advertencias": sum(len(r["incidencias"]) for r in records.values()),
                "por_fase": dict(Counter(r["fase"] for r in records.values())),
                "por_estado": dict(Counter(r["estado"] for r in records.values())),
                "contadores_http": dict(client.contadores),
                "exit_code": code,
                "observaciones_fuente": sorted(
                    refs.values(), key=lambda x: (x["url"], x["observado_utc"])
                ),
            }
        )
        exportar(run, records, quarantine, pending, report)
        last_snapshot = client.reloj()

    def tick(window, event_id=None):
        nonlocal operations
        operations += 1
        if operations % checkpoint_cada == 0 or client.reloj() - last_snapshot >= 60:
            snapshot()
        if progreso:
            progreso(
                {
                    "ejecucion": str(run),
                    "ronda": current_round + 1,
                    "ventana": window,
                    "unidad": "MES_ESPN_EASTERN",
                    "ventanas": sum(all(q in verified for q in children[m]) for m in months),
                    "total": len(months),
                    "partidos_validos": len(records),
                    "evento": event_id,
                    "estadisticas_completas": sum(
                        r["estadisticas_completas"] for r in records.values()
                    ),
                    "cuarentena": len(quarantine),
                    "pendientes": len(pending),
                    **client.contadores,
                }
            )

    def process(event, meta, window, retry=False):
        eid = None
        evidence = [meta]
        try:
            objeto(event, "event")
            eid = identificador(event.get("id"), "event.id")
            seen.add(eid)
            exigir(event.get("uid") == f"{torneo.uid}~e:{eid}", "OTRA_LIGA", "event.uid")
            dt = instante(event.get("date"))
            teams = lados(competicion(event))
            identity = (
                dt.isoformat(),
                str(teams["home"]["team"]["id"]),
                str(teams["away"]["team"]["id"]),
            )
            if eid in identities:
                exigir(identities[eid] == identity, "DUPLICADO_CONFLICTIVO", "event")
            identities[eid] = identity
            if not start <= dt < end:
                report["eventos_fuera_ventana"] += int(not retry)
                return
            if eid in excluded:
                return
            core = normalizar(event, torneo)
            if eid in records:
                exigir(
                    all(records[eid][k] == core[k] for k in CORE), "DUPLICADO_CONFLICTIVO", "event"
                )
            if eid in records and not retry:
                report["duplicados_identicos"] += 1
                if meta not in records[eid]["evidencia"]:
                    records[eid]["evidencia"].append(meta)
                return
            if core["final_completo"]:
                exigir(
                    dt <= instante(meta["observado_utc"]), "FINAL_CON_INICIO_FUTURO", "inicio_utc"
                )
                if con_estadisticas:
                    try:
                        param = dt.astimezone(NY).strftime("%Y%m%d")
                        payload, smeta = client.obtener("summary", eid, max_age=age(param))
                        reference(smeta)
                        evidence.append(smeta)
                        exigir(
                            dt <= instante(smeta["observado_utc"]),
                            "FINAL_CON_INICIO_FUTURO",
                            "summary.observado_utc",
                        )
                        core = enriquecer(core, payload, event)
                        if core["campos_faltantes"]:
                            failure(
                                "summary",
                                eid,
                                ContratoError(
                                    "DATOS_ESTADISTICOS_INCOMPLETOS",
                                    ",".join(core["campos_faltantes"]),
                                ),
                                event=event,
                                meta=meta,
                                window=window,
                                fields=core["campos_faltantes"],
                            )
                        else:
                            pending.pop(("summary", eid), None)
                            tasks.pop(("summary", eid), None)
                    except (FuenteError, ArchivoError) as exc:
                        if isinstance(exc, ConsultaError):
                            core["detalle_estado"] = "NO_DISPONIBLE"
                        else:
                            core["detalle_estado"] = "INTERRUMPIDO"
                        failure(
                            "summary", eid, exc, event=event, meta=meta,
                            window=window, fields=core["campos_faltantes"],
                        )
                        core["evidencia"] = evidence
                        records[eid] = core
                        if not isinstance(exc, ConsultaError):
                            raise
                    except ContratoError as exc:
                        core["detalle_estado"] = "NO_DISPONIBLE"
                        failure(
                            "summary",
                            eid,
                            exc,
                            event=event,
                            meta=meta,
                            window=window,
                            fields=core["campos_faltantes"],
                        )
                else:
                    core["detalle_estado"] = "NO_SOLICITADO"
            if eid in records:
                evidence.extend(m for m in records[eid]["evidencia"] if m not in evidence)
            core["evidencia"] = evidence
            records[eid] = core
        except ContratoError as exc:
            if eid is not None:
                excluded.add(eid)
                old = records.pop(eid, None)
                if old:
                    evidence.extend(m for m in old["evidencia"] if m not in evidence)
                pending.pop(("summary", eid), None)
                tasks.pop(("summary", eid), None)
            quarantine.append(
                {
                    "source_game_id": eid,
                    "ventana": window,
                    "codigo": exc.codigo,
                    "campo": exc.campo,
                    "evidencia": evidence,
                }
            )

    try:
        snapshot()
        for current_round in range(rondas):
            day_queue = deque(
                months
                if current_round == 0
                else [k[1] for k, v in pending.items() if k[0] == "scoreboard" and v["reintentar"]]
            )
            work_events = (
                []
                if current_round == 0
                else [k for k, v in pending.items() if k[0] == "summary" and v["reintentar"]]
            )
            if current_round and not day_queue and not work_events:
                break
            report["rondas_ejecutadas"] = current_round + 1
            if current_round:
                if progreso:
                    progreso(
                        {
                            "estado": "ESPERANDO_REINTENTO",
                            "segundos": espera_rondas,
                            "consultas": len(day_queue) + len(work_events),
                        }
                    )
                client.dormir(espera_rondas)
            while day_queue:
                query = day_queue.popleft()
                try:
                    payload, meta = client.obtener("scoreboard", query, max_age=age(query))
                    reference(meta)
                    events = eventos_scoreboard(payload, torneo)
                except (ConsultaError, ContratoError) as exc:
                    if (
                        getattr(exc, "codigo", None)
                        in ("POSIBLE_TRUNCAMIENTO", "RESPUESTA_EXCESIVA")
                        and len(query) == 6
                    ):
                        y, m = int(query[:4]), int(query[4:])
                        lo = max(first, date(y, m, 1))
                        hi = min(last, date(y, m, calendar.monthrange(y, m)[1]))
                        children[query] = [
                            (lo + timedelta(days=i)).strftime("%Y%m%d")
                            for i in range((hi - lo).days + 1)
                        ]
                        pending.pop(("scoreboard", query), None)
                        day_queue.extend(children[query])
                        tick(query)
                        continue
                    failure("scoreboard", query, exc, window=query)
                    tick(query)
                    continue
                pending.pop(("scoreboard", query), None)
                report["eventos_observados"] += len(events)
                if not events:
                    empty.add(query)
                for event in events:
                    process(event, meta, query)
                    tick(query, event.get("id") if isinstance(event, dict) else None)
                verified.add(query)
                append_json(
                    run / "checkpoint.jsonl",
                    {
                        "consulta": query,
                        "eventos": len(events),
                        "sha256": meta["sha256"],
                        "observado_utc": meta["observado_utc"],
                        "registros_validos": len(records),
                    },
                )
                tick(query)
            for key in work_events:
                if key in pending and pending[key]["ultima_ronda"] < current_round + 1:
                    event, meta, window = tasks[key]
                    process(event, meta, window, retry=True)
                    tick(window, key[1])
            snapshot()
        missing = any(not all(q in verified for q in children[m]) for m in months)
        if missing or any(k[0] == "summary" and k[1] not in records for k in pending):
            report["estado"], report["error"], code = (
                "INCOMPLETO",
                "Faltan ventanas o resultados; consultar pendientes.jsonl",
                3,
            )
        elif pending or quarantine or any(r["incidencias"] for r in records.values()):
            report["estado"], code = "COMPLETO_CON_INCIDENCIAS", 2
        else:
            report["estado"], code = "COMPLETO_EN_VENTANA_ESPN", 0
    except KeyboardInterrupt:
        report["estado"], report["error"], code = (
            "INTERRUMPIDO",
            "Interrupción del operador o SIGTERM; reanudación disponible",
            130,
        )
    except (FuenteError, ArchivoError, OSError) as exc:
        report["estado"], report["error"], code = "INCOMPLETO", str(exc), 3
    except Exception as exc:
        report["estado"], report["error"], code = "ERROR_INTERNO", f"{type(exc).__name__}: {exc}", 4
    finally:
        report["fin_ejecucion_utc"] = client.ahora().isoformat()
        snapshot()
    return run, report, code
