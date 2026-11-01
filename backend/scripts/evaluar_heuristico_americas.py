"""Walk-forward del estimador realmente servido, sobre un clon local congelado.

Sin entrenamiento, calibración, activación, cuotas ni escrituras en la BD. Llama
al mismo analizador histórico y mide sus campos finales, no una reimplementación.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import gzip
import hashlib
import json
import logging
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from api.rutas_analisis_futbol import analizar_partido, VERSION_HEURISTICO_AMERICAS
from api.schemas_futbol import AnalisisRequest
from calidad.elegibilidad_futbol import seleccionar
from db import obtener_database_url, cerrar_pool
from ingesta_futbol_americas import COMPETICIONES, digest, sha

MERCADOS = {
    "GOLES_FT": ("goles_ft", 2.5), "GOLES_1T": ("goles_1t", 1.5), "GOLES_2T": ("goles_2t", 1.5),
    "CORNERS_FT": ("corners_ft", 8.5), "DISPAROS_ARCO_FT": ("disparos_arco_ft", 7.5),
    "CORNERS_1T": ("corners_1t", 4.5), "CORNERS_2T": ("corners_2t", 4.5),
}
PROTOCOLO = {
    "version": "americas-heuristico-walkforward-v1",
    "naturaleza": "AUDITORIA_RETROSPECTIVA_NO_PROSPECTIVA_NO_CALIBRACION",
    "seleccion": "Si hay finales desde 2025: todos los finales 2025–2026 descargados. Si no: último 20% de instantes de kickoff, sin dividir simultáneos.",
    "alcance": "Misma competición; todas sus temporadas disponibles. Kickoff exclusivo. API limita históricos por equipo/localía/liga a 100 y H2H a 10, con política de elegibilidad vigente.",
    "referencia": "Media aritmética y frecuencia empírica Over de finales previos elegibles de la misma competición, ventana 730 días. Mínimo 40 objetivos observados. No se seleccionan parámetros con EVAL.",
    "minimo_referencia": 40,
    "mercados": MERCADOS,
    "abstenciones": "Se informan separadamente objetivo real ausente, predicción no soportada y referencia con menos de 40 casos; nunca se imputan outcomes.",
    "advertencias": ["El histórico fue descargado después de los partidos; no acredita disponibilidad original ni prospectividad.",
                     "Los resultados no certifican selecciones distintas de temporadas ni superioridad futura.",
                     "Mitades de córners ausentes se reportan N/D; tiros al arco por mitad no se evalúan como observados.",
                     "No se entrena ni publica un modelo ML; heuristico-americas::1.0.0 permanece RAW."],
}


def cohorte(rows):
    recientes = [r for r in rows if r["fecha_partido"].year >= 2025]
    if recientes:
        return recientes
    fechas = sorted({r["fecha_partido"] for r in rows})
    if not fechas:
        return []
    corte = fechas[min(len(fechas) - 1, int(len(fechas) * .8))]
    return [r for r in rows if r["fecha_partido"] >= corte]


def metricas(items):
    if not items:
        return {"n": 0, "mae": None, "rmse": None, "sesgo": None, "brier": None, "logloss": None}
    n = len(items)
    return {"n": n, "mae": sum(abs(x["media"] - x["y"]) for x in items) / n,
            "rmse": math.sqrt(sum((x["media"] - x["y"]) ** 2 for x in items) / n),
            "sesgo": sum(x["media"] - x["y"] for x in items) / n,
            "brier": sum((x["p"] - x["binario"]) ** 2 for x in items) / n,
            "logloss": -sum(x["binario"] * math.log(max(1e-12, x["p"])) + (1-x["binario"]) * math.log(max(1e-12, 1-x["p"])) for x in items) / n}


def evaluar(codigo, salida, *, max_casos=None):
    conf = conninfo_to_dict(obtener_database_url())
    if conf.get("host") not in {"127.0.0.1", "localhost"} or conf.get("dbname") == "postgres":
        raise ValueError("Evaluar únicamente sobre un clon local congelado")
    backend = Path(__file__).resolve().parents[1]
    fuentes = [backend / f for f in ["api/rutas_analisis_futbol.py", "api/config_estadistica_futbol.py",
               "calidad/elegibilidad_futbol.py", "servicios/b3_estabilizacion_futbol.py", "servicios/analisis_integral.py", "ingesta_futbol_americas.py"]] + [Path(__file__).resolve()]
    codigo_sha = digest({str(p.relative_to(backend)): sha(p) for p in fuentes})
    salida.mkdir(parents=True, exist_ok=True, mode=0o700)
    protocolo_path = salida / "PROTOCOLO.json"
    if protocolo_path.exists() and json.loads(protocolo_path.read_text()) != json.loads(json.dumps(PROTOCOLO)):
        raise ValueError("No sustituir un protocolo existente")
    protocolo_path.write_text(json.dumps(PROTOCOLO, ensure_ascii=False, indent=2))
    with psycopg.connect(obtener_database_url(), row_factory=dict_row, connect_timeout=5) as c:
        c.read_only = True
        c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY; SET LOCAL timezone='GMT'")
        comp = c.execute("SELECT id FROM competiciones_futbol WHERE codigo=%s", [codigo]).fetchone()
        if not comp:
            raise ValueError("Competición no cargada")
        rows = c.execute("SELECT * FROM partidos_futbol WHERE competicion_id=%s AND valido IS TRUE AND estado='FINALIZADO' ORDER BY fecha_partido,id", [comp["id"]]).fetchall()
        temporadas = [str(t["id"]) for t in c.execute("SELECT id FROM temporadas_futbol WHERE competicion_id=%s ORDER BY nombre", [comp["id"]])]
        elegidos = cohorte(rows)
        if max_casos:
            # Solo banco diagnóstico explícito; no confundir con evaluación completa.
            elegidos = elegidos[:max_casos]
        dataset_hash, cohorte_hash = digest(rows), digest([str(r["id"]) for r in elegidos])
        resumen_path = salida / f"{codigo}_RESUMEN.json"
        identidad = {"codigo_sha256": codigo_sha, "datos_sha256": dataset_hash, "cohorte_sha256": cohorte_hash,
                     "protocolo_sha256": digest(PROTOCOLO), "max_casos": max_casos}
        if resumen_path.exists():
            previo = json.loads(resumen_path.read_text())
            if previo["identidad"] == identidad:
                print(codigo, "Evidencia congelada reutilizada", previo["cohorte_n"], flush=True)
                return previo
            raise ValueError("Evidencia previa de otro cálculo/dataset; usar salida nueva, no sobrescribir")
        (salida / f"{codigo}_COHORTE.json").write_text(json.dumps([{"partido_id": str(r["id"]), "kickoff": r["fecha_partido"].isoformat()} for r in elegidos], indent=2))
        predicciones, referencias = {m: [] for m in MERCADOS}, {m: [] for m in MERCADOS}
        conteos = {m: Counter() for m in MERCADOS}
        registro_path = salida / f"{codigo}_PREDICCIONES.jsonl.gz"
        if registro_path.exists():
            raise ValueError("Ejecución parcial existente; conservar antes de reanudar")
        with gzip.open(registro_path, "wt", encoding="utf-8") as registro:
            for idx, objetivo in enumerate(elegidos):
                fecha = objetivo["fecha_partido"]
                anteriores = [r for r in rows if fecha - timedelta(days=730) <= r["fecha_partido"] < fecha]
                respuesta = analizar_partido(AnalisisRequest(
                    partido_id=objetivo["id"], modo_historico=True, solo_consulta=True,
                    temporadas=temporadas, h2h_limite=10, mercado_objetivo="GOLES_FT", lado_objetivo="OVER", linea_objetivo=2.5,
                    lineas_goles=[1.5, 2.5], lineas_corners=[4.5, 8.5], lineas_disparos=[7.5]))
                assert respuesta.modelo_version == VERSION_HEURISTICO_AMERICAS and not respuesta.recomendaciones and respuesta.calibradores_activos == 0
                assert respuesta.fecha_corte == fecha
                mercados = {**respuesta.mercados_goles, **respuesta.mercados_corners, **respuesta.mercados_disparos}
                for m, (metrica, linea) in MERCADOS.items():
                    contador = conteos[m]
                    contador["cohorte"] += 1
                    real = seleccionar(objetivo, metrica)
                    pred = mercados.get(m)
                    if real.estado != "OBSERVADO":
                        contador["objetivo_no_observado"] += 1
                        continue
                    contador["objetivos_observados"] += 1
                    if pred is None:
                        contador["abstencion_predictor"] += 1
                        continue
                    contador["predicciones"] += 1
                    valores = [d.valor for r in anteriores if (d := seleccionar(r, metrica)).estado == "OBSERVADO"]
                    if len(valores) < 40:
                        contador["referencia_insuficiente"] += 1
                        continue
                    p = pred.lineas[str(linea)].over_raw
                    item = {"partido_id": str(objetivo["id"]), "mercado": m, "corte_exclusivo": fecha.isoformat(),
                            "n_referencia": len(valores), "y": real.valor, "linea": linea, "binario": int(real.valor > linea),
                            "media": pred.media, "std": pred.std, "p": p,
                            "media_referencia": sum(valores) / len(valores),
                            "p_referencia": sum(v > linea for v in valores) / len(valores)}
                    predicciones[m].append(item)
                    referencias[m].append({"media": item["media_referencia"], "p": item["p_referencia"], "y": item["y"], "binario": item["binario"]})
                    registro.write(json.dumps(item, ensure_ascii=False) + "\n")
                if (idx + 1) % 50 == 0:
                    registro.flush()
                    print(codigo, idx + 1, "/", len(elegidos), flush=True)
        resumen = {"codigo": codigo, "identidad": identidad, "cohorte_n": len(elegidos), "historicos_n": len(rows),
                   "primero_eval": elegidos[0]["fecha_partido"].isoformat() if elegidos else None,
                   "ultimo_eval": elegidos[-1]["fecha_partido"].isoformat() if elegidos else None,
                   "version_estimador": "heuristico-americas::1.0.0", "calibracion": "RAW_SIN_CALIBRAR", "ML_activado": False,
                   "mercados": {m: {"conteos": dict(conteos[m]), "predictor": metricas(predicciones[m]), "referencia": metricas(referencias[m])} for m in MERCADOS},
                   "archivo_predicciones_sha256": sha(registro_path)}
        resumen_path.write_text(json.dumps(resumen, ensure_ascii=False, indent=2))
        print(codigo, "terminado", len(elegidos), flush=True)
        c.rollback()
        return resumen


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--codigo", choices=sorted(COMPETICIONES), action="append", required=True)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--max-casos", type=int, help="Solo diagnóstico acotado, no evaluación completa")
    a = p.parse_args()
    if a.max_casos is not None and a.max_casos < 1:
        p.error("max-casos debe ser positivo")
    logging.basicConfig(level=logging.ERROR)
    try:
        for codigo in a.codigo:
            evaluar(codigo, a.salida, max_casos=a.max_casos)
    finally:
        cerrar_pool()
