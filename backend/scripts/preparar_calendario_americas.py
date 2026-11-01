"""Calendario acotado de seis feeds ESPN; solo archivos, no BD/modelos.

Reutiliza transporte, límites, archivo inmutable, normalizador y turnos LATAM.
No toca los directorios/locks de las descargas históricas activas.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.futbol_latam.archivo import Archivo, bloqueo, guardar_json, atomico, append_json
from scrapers.futbol_latam.cliente import ClienteESPN, ConsultaError, FuenteError, url_consulta
from scrapers.futbol_latam.contrato import ContratoError, eventos_scoreboard, normalizar, instante
from scrapers.futbol_latam.ligas import POR_SLUG, Torneo
from scrapers.futbol_latam.pipeline import ventana, exportar
from scrapers.futbol_latam.red import ControlRed


def ejecutar(salida, control, desde, hasta, ligas=None, offline=False):
    inicio, fin, _, _, meses = ventana(desde, hasta, "America/Bogota")
    records, quarantine, refs, comprobaciones, pendientes = {}, [], [], [], {}
    contadores = {"requests": 0, "cache_hits": 0, "reintentos": 0}
    torneos = [Torneo("mls", "usa.1", "770", "Estados Unidos/Canadá", "MLS"), *POR_SLUG.values()]
    torneos = [t for t in torneos if not ligas or t.slug in ligas]
    detener = False
    with bloqueo(salida):
        run = salida / "ejecuciones" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run.mkdir(parents=True, mode=0o700)
        for t in torneos:
            fuente = salida / "fuentes" / t.slug
            fuente.mkdir(parents=True, exist_ok=True, mode=0o700)
            client = ClienteESPN(Archivo(fuente), torneo=t, control_red=ControlRed(control), offline=offline,
                                 intervalo=5, max_requests=30, intentos=2)
            try:
                for mes in meses:
                    try:
                        payload, meta = client.obtener("scoreboard", mes, max_age=0)
                        events = eventos_scoreboard(payload, t)
                    except (ConsultaError, FuenteError, ContratoError) as exc:
                        url = url_consulta("scoreboard", mes, t)
                        pendientes[url] = {"codigo_liga": t.slug, "endpoint": "scoreboard", "parametro": mes,
                                           "url": url, "error": str(exc), "observado_utc": datetime.now(timezone.utc).isoformat()}
                        guardar_json(run / "pendientes_parciales.json", pendientes)
                        if not isinstance(exc, ConsultaError):
                            detener = True  # Auth/límites/circuit breaker/truncamiento: no evadir.
                            break
                        continue
                    refs.append(meta)
                    comp = {"liga": t.slug, "mes": mes, "eventos_fuente": len(events), "fixtures_aceptados": 0,
                            "observado_utc": meta["observado_utc"], "sha256": meta["sha256"], "url": meta["url"]}
                    for ev in events:
                        try:
                            # No convertir incidencias de finales ajenos a la
                            # ventana en huecos del calendario solicitado.
                            fecha = instante(ev.get("date"))
                            if not inicio <= fecha < fin:
                                continue
                            row = normalizar(ev, t)
                            dt = datetime.fromisoformat(row["inicio_utc"])
                            if not inicio <= dt < fin or row["estado"] != "PROGRAMADO":
                                continue
                            row["evidencia"] = [meta]
                            key = f"{t.slug}:{row['source_game_id']}"
                            if key in records and records[key] != row:
                                raise ValueError("Evento contradictorio entre meses")
                            records[key] = row
                            comp["fixtures_aceptados"] += 1
                        except ContratoError as exc:
                            quarantine.append({"codigo_liga": t.slug, "source_game_id": ev.get("id"), "mes": mes,
                                               "motivo": str(exc), "evidencia": meta})
                    comprobaciones.append(comp)
                    guardar_json(run / "comprobaciones.json", comprobaciones)
                    guardar_json(run / "fixtures_parciales.json", records)
                    print(t.slug, mes, "eventos", len(events), "fixtures", comp["fixtures_aceptados"], flush=True)
            finally:
                for clave in contadores:
                    contadores[clave] += client.contadores[clave]
                client.close()
            if detener:
                break
        for name in ("checkpoint.jsonl", "incidencias.jsonl"):
            atomico(run / name, b"")
        esperadas = {(t.slug, mes) for t in torneos for mes in meses}
        verificadas = {(r["liga"], r["mes"]) for r in comprobaciones}
        for item in pendientes.values():
            append_json(run / "incidencias.jsonl", item)
        report = {"estado": "INCOMPLETO" if verificadas != esperadas else "COMPLETO_CON_INCIDENCIAS" if quarantine else "COMPLETO_EN_VENTANA_ESPN",
                  "desde": desde.isoformat(), "hasta": hasta.isoformat(), "zona": "America/Bogota",
                  "modo": "OFFLINE" if offline else "HTTP", "contadores_http": contadores,
                  "partidos_exportados": len(records), "finales_completos": 0, "finales_con_estadisticas_completas": 0,
                  "consultas_pendientes": len(pendientes), "observaciones_fuente": refs,
                  "ventanas_previstas": len(esperadas), "ventanas_completadas": len(verificadas),
                  "ventanas_pendientes": sorted(esperadas - verificadas),
                  "cobertura_independiente_certificada": False, "comprobaciones": comprobaciones,
                  "limite": "Feed ESPN por mes; ausencia o fechas máximas no certifican publicación oficial íntegra."}
        exportar(run, records, quarantine, pendientes, report)
        return run


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--control-red", type=Path, required=True)
    p.add_argument("--desde", type=date.fromisoformat, required=True)
    p.add_argument("--hasta", type=date.fromisoformat, required=True)
    p.add_argument("--fetch", action="store_true")
    p.add_argument("--offline", action="store_true")
    p.add_argument("--liga", action="append", choices=["usa.1", *POR_SLUG])
    a = p.parse_args()
    repo = Path(__file__).resolve().parents[2]
    if a.salida.resolve() == repo or repo in a.salida.resolve().parents or a.fetch and a.offline:
        p.error("Salida externa al repositorio y modos fetch/offline excluyentes")
    if a.fetch or a.offline:
        print(ejecutar(a.salida, a.control_red, a.desde, a.hasta, a.liga, a.offline))
    else:
        print({"modo": "PLAN_SIN_RED", "ventanas_por_feed": ventana(a.desde, a.hasta, "America/Bogota")[-1], "feeds": 6})
