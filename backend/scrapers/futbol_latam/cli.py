"""Tres entradas independientes, archivo por torneo y exportación consolidada por país."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import signal
import sys
from uuid import uuid4
from zoneinfo import ZoneInfoNotFoundError

from . import VERSION
from .archivo import Archivo, ArchivoError, atomico, bloqueo, guardar_json
from .cliente import ClienteESPN, url_consulta
from .ligas import POR_PAIS
from .pipeline import ejecutar, exportar, plan
from .red import ControlRed

REPO = Path(__file__).resolve().parents[3]


def parser(pais):
    p = argparse.ArgumentParser(description=f"ESPN {pais.title()}: goles, córners y tiros a CSV/JSONL; sin BD.")
    p.add_argument("--version", action="version", version=f"{pais.title()} LATAM {VERSION}")
    p.add_argument("--desde", required=True, type=date.fromisoformat)
    p.add_argument("--hasta", required=True, type=date.fromisoformat)
    p.add_argument("--zona", default="America/Bogota")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--fetch", action="store_true")
    mode.add_argument("--offline", action="store_true")
    p.add_argument("--salida", type=Path)
    p.add_argument("--torneos", choices=["todos", "principal"], default="todos", help="Argentina: todos incluye Copa de la Liga y Copa de la Superliga históricas; no Copa Argentina")
    stats = p.add_mutually_exclusive_group()
    stats.add_argument("--estadisticas", dest="estadisticas", action="store_true", default=True)
    stats.add_argument("--solo-resultados", dest="estadisticas", action="store_false")
    mode_cache = p.add_mutually_exclusive_group()
    mode_cache.add_argument("--refresh", action="store_true")
    mode_cache.add_argument("--reintentar-pendientes", action="store_true")
    p.add_argument("--intervalo", type=float, default=5, help="Segundos entre GET, mínimo 3; recomendado 5 o más")
    p.add_argument("--max-requests", type=int, default=20000, help="Presupuesto conjunto de todos los torneos, incluidos reintentos; 1..20000")
    p.add_argument("--intentos-http", type=int, default=5)
    p.add_argument("--rondas", type=int, default=3)
    p.add_argument("--espera-rondas", type=float, default=30)
    p.add_argument("--checkpoint-cada", type=int, default=25)
    p.add_argument("--control-red", type=Path, help="Directorio de turnos/pausa compartidos. Predeterminado: SALIDA/../.control_red_espn_latam")
    return p


@contextmanager
def guardar_al_terminar():
    def terminar(signum, frame):
        raise KeyboardInterrupt
    previous = signal.signal(signal.SIGTERM, terminar)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def pendientes_previos(root, torneo):
    pointer = root / "ultima_ejecucion.json"
    if not pointer.exists():
        return set()
    try:
        name = json.loads(pointer.read_bytes())["ejecucion"]
        if not isinstance(name, str) or not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{12}", name):
            raise ValueError("Ruta inválida")
        urls = set()
        for line in (root / "ejecuciones" / name / "pendientes.jsonl").read_text(encoding='utf-8').splitlines():
            item = json.loads(line)
            expected = url_consulta(item["endpoint"], item["parametro"], torneo)
            if item["url"] != expected:
                raise ValueError("URL de otro torneo o alterada")
            urls.add(expected)
        return urls
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise ArchivoError("No se pueden leer los pendientes anteriores") from exc


def consolidar(root, run, pais, args, torneos, entregas):
    """Solo consolida subejecuciones de esta invocación, nunca restos de otro rango."""
    records, quarantine, pending, refs = {}, [], {}, []
    for torneo, child_run, child in entregas:
        for line in (child_run / "partidos.jsonl").read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            records[f"{torneo.slug}:{row['source_game_id']}"] = row
        for line in (child_run / "cuarentena.jsonl").read_text(encoding='utf-8').splitlines():
            quarantine.append({"codigo_liga": torneo.slug, **json.loads(line)})
        for line in (child_run / "pendientes.jsonl").read_text(encoding='utf-8').splitlines():
            item = {"codigo_liga": torneo.slug, **json.loads(line)}
            pending[item["url"]] = item
        refs.extend(child["observaciones_fuente"])
    terminados = len(entregas) == len(torneos)
    completos = terminados and all(r[2]["recorrido_completo"] for r in entregas)
    codes = [r[2]["exit_code"] for r in entregas]
    code = 130 if 130 in codes else 4 if 4 in codes else 3 if not terminados or 3 in codes else 2 if 2 in codes else 0
    estados = {0: "COMPLETO_EN_VENTANA_ESPN", 2: "COMPLETO_CON_INCIDENCIAS", 3: "INCOMPLETO", 4: "ERROR_INTERNO", 130: "INTERRUMPIDO"}
    contadores = {k: sum(r[2]["contadores_http"][k] for r in entregas) for k in ("requests", "cache_hits", "bytes_red", "reintentos")}
    filas = list(records.values())
    esperadas = {(t.slug, w) for t in torneos for w in plan(args.desde, args.hasta, args.zona, t)["ventanas_espn"]}
    verificadas = {(t.slug, w) for t, _, child in entregas for w in child["ventanas_verificadas"]}
    report = {
        "pais": pais, "version_scraper": VERSION, "contrato": "espn_latam_v1",
        "desde": args.desde.isoformat(), "hasta": args.hasta.isoformat(), "zona": args.zona,
        "modo": "OFFLINE" if args.offline else "HTTP", "estadisticas_solicitadas": args.estadisticas,
        "actualizado_utc": datetime.now(timezone.utc).isoformat(),
        "estado": estados[code], "exit_code": code, "recorrido_completo": completos,
        "partidos_exportados": len(filas), "finales_completos": sum(r["final_completo"] for r in filas),
        "finales_con_estadisticas_completas": sum(r["estadisticas_completas"] for r in filas),
        "no_finales": sum(not r["final_completo"] for r in filas),
        "incidencias_cuarentena": len(quarantine), "consultas_pendientes": len(pending),
        "ventanas_previstas": len(esperadas), "ventanas_completadas": len(verificadas),
        "ventanas_pendientes": [{"liga": t, "mes": m} for t, m in sorted(esperadas - verificadas)],
        "torneos_pendientes": [t.slug for t in torneos if t not in [e[0] for e in entregas]],
        "contadores_http": contadores, "observaciones_fuente": refs,
        "torneos": [{"slug": t.slug, "reporte": str(p / "reporte.json"), "estado": r["estado"], "partidos": r["partidos_exportados"], "cobertura_por_temporada": r["cobertura_por_temporada"]} for t,p,r in entregas],
        "escribe_bd": False, "entrena": False, "cobertura_historica_certificada": False,
        "limite_cobertura": "Feeds ESPN de los torneos enumerados. No certifica calendario independiente ni datos ausentes. Copas nacionales, selecciones y otras divisiones quedan fuera.",
        "error": next((r[2]["error"] for r in entregas if r[2]["error"]), None),
    }
    # Un mismo event_id en dos feeds requiere revisar procedencia antes de ingerir.
    por_id = {}
    for row in filas:
        por_id.setdefault(row["source_game_id"], set()).add(row["codigo_liga"])
    report["ids_compartidos_entre_torneos"] = {k: sorted(v) for k,v in por_id.items() if len(v)>1}
    if report["ids_compartidos_entre_torneos"] and code == 0:
        report.update(estado=estados[2], exit_code=2)
        code = 2
    if not terminados and not report["error"]:
        report["error"] = "Quedan torneos sin recorrer en esta ejecución"
    for name in ("checkpoint.jsonl", "incidencias.jsonl"):
        atomico(run / name, b"".join((p / name).read_bytes() for _,p,_ in entregas))
    exportar(run, records, quarantine, pending, report)
    return report, code


def main(pais, argv=None):
    p = parser(pais)
    args = p.parse_args(argv)
    torneos = POR_PAIS[pais] if args.torneos == "todos" else POR_PAIS[pais][:1]
    try:
        planes = [plan(args.desde, args.hasta, args.zona, t) for t in torneos]
        if (args.refresh or args.reintentar_pendientes) and not args.fetch:
            p.error("--refresh/--reintentar-pendientes requieren --fetch")
        if not args.fetch and not args.offline:
            print(json.dumps({"modo": "PLAN_SIN_RED", "pais": pais, "torneos": planes, "ventanas_previstas": sum(x["ventanas_previstas"] for x in planes)},ensure_ascii=False,indent=2))
            return 0
        if args.salida is None:
            p.error("--fetch/--offline requieren --salida")
        root = args.salida.expanduser().resolve()
        control = (args.control_red.expanduser().resolve() if args.control_red else root.parent / ".control_red_espn_latam")
        if any(x == REPO or REPO in x.parents for x in (root, control)):
            p.error("La salida y el control de red deben estar fuera del repositorio")
        # Validate every network/work limit before creating a run or making a request.
        import math
        if not math.isfinite(args.intervalo) or args.intervalo < 3 or not 1 <= args.max_requests <= 20000 or not 1 <= args.intentos_http <= 8:
            p.error("Intervalo >=3, presupuesto 1..20000 e intentos 1..8")
        if not 1 <= args.rondas <= 10 or not 1 <= args.checkpoint_cada <= 1000 or not math.isfinite(args.espera_rondas) or not 0 <= args.espera_rondas <= 60:
            p.error("Rondas 1..10, checkpoint 1..1000 y espera 0..60 s")
        with bloqueo(root), guardar_al_terminar():
            identidad = {"contrato": "espn_latam_v1", "pais": pais}
            identity_file = root / "identidad.json"
            if identity_file.exists():
                if json.loads(identity_file.read_bytes()) != identidad:
                    raise ArchivoError("La carpeta pertenece a otro país o contrato")
            else:
                if any((root / n).exists() for n in ("ultima_ejecucion.json", "raw", "torneos")):
                    raise ArchivoError("Carpeta previa sin identidad LATAM: usar otra salida")
                guardar_json(identity_file, identidad)
            run = root / "ejecuciones" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12])
            run.mkdir(parents=True, mode=0o700)
            entregas = []
            remaining = args.max_requests
            for torneo in torneos:
                if remaining < 1:
                    break
                child_root = root / "torneos" / torneo.slug
                child_root.mkdir(parents=True, exist_ok=True, mode=0o700)
                client = ClienteESPN(Archivo(child_root), torneo=torneo, control_red=ControlRed(control), offline=args.offline, refresh=args.refresh, intervalo=args.intervalo, max_requests=remaining, intentos=args.intentos_http)
                try:
                    if args.reintentar_pendientes:
                        client.refrescar_urls = pendientes_previos(child_root, torneo)
                    child_run, child, child_code = ejecutar(client, desde=args.desde, hasta=args.hasta, zona=args.zona, con_estadisticas=args.estadisticas, rondas=args.rondas, espera_rondas=args.espera_rondas, checkpoint_cada=args.checkpoint_cada, progreso=lambda x: print(json.dumps({"liga": torneo.slug, **x},ensure_ascii=False),file=sys.stderr,flush=True))
                finally:
                    client.close()
                remaining -= child["contadores_http"]["requests"]
                entregas.append((torneo, child_run, child))
                report, code = consolidar(root, run, pais, args, torneos, entregas)
                if child_code in (4,130) or (child_code == 3 and child["error"] != "Faltan ventanas o resultados; consultar pendientes.jsonl"):
                    break
            report, code = consolidar(root, run, pais, args, torneos, entregas)
        print(json.dumps({**{k:report[k] for k in ("estado","partidos_exportados","finales_completos","finales_con_estadisticas_completas","no_finales","recorrido_completo","consultas_pendientes","torneos_pendientes","error","exit_code")},"csv":str(run / "partidos.csv"),"csv_completos":str(run / "partidos_completos.csv"),"reporte":str(run / "reporte.json")},ensure_ascii=False,indent=2))
        return code
    except (ValueError, ZoneInfoNotFoundError, ArchivoError, OSError) as exc:
        print(f"{pais.title()}: {exc}",file=sys.stderr)
        return 3
