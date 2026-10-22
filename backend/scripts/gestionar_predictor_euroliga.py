"""Entrenamiento, snapshot y evaluación Euroliga explícitos, sin DML/cron.

Artefactos/datasets/cohortes fuera del repositorio. --entrenar nunca publica
implícitamente; --publicar solo acepta el artefacto entrenado en esa invocación.
"""
import argparse
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.euroliga import (cargar, entrenar, escribir_nuevo, final_valido, json_bytes,
                            predecir, probabilidades, publicar, validar_modelo)
from servicios.predictor_euroliga import leer_datos


def congelar(modelo: dict, filas: list[dict], destino: Path, dias: int = 30) -> dict:
    """Cohorte inmutable de distribuciones; línea170.5 es referencia, no mercado."""
    validar_modelo(modelo)
    destino.mkdir(parents=True, exist_ok=False, mode=0o700)
    ahora = datetime.now(timezone.utc)
    hoy, fin = ahora.date().isoformat(), (ahora.date() + timedelta(days=dias)).isoformat()
    capturas, abstenciones = [], []
    for r in filas:
        fecha = str(r["fecha_partido"])[:10]
        if r.get("competicion_codigo") != "euroleague" or not hoy <= fecha <= fin or r.get("valido") is not True or final_valido(r):
            continue
        identidad = {"partido_id": str(r["id"]), "equipo_local_id": str(r["equipo_local_id"]),
                     "equipo_visitante_id": str(r["equipo_visitante_id"]), "fecha_partido": fecha}
        try:
            p = predecir(modelo, r["local"], r["visitante"], "COMPLETO", 170.5)
            capturas.append({**identidad, "resultado": p, "prospectiva_acreditada_por_fecha": hoy < fecha})
        except ValueError as exc:
            abstenciones.append({**identidad, "razon": str(exc)})
    cohorte = {"formato": "cohorte_euroliga_v1", "congelado_en": ahora.isoformat(),
               "modelo_version": modelo["version"], "artefacto_sha256": sha256(json_bytes(modelo)).hexdigest(),
               "referencia_linea": "170.5 fija, no cotización observada; se congelan todas las medias y dispersiones",
               "limite_anterioridad": "Sin hora de kickoff: mismo día no acredita prospectiva",
               "capturas": capturas, "abstenciones": abstenciones}
    escribir_nuevo(destino / "MODELO.json", modelo)
    escribir_nuevo(destino / "COHORTE.json", cohorte)
    manifiesto = {p.name: sha256(p.read_bytes()).hexdigest() for p in destino.glob("*.json")}
    escribir_nuevo(destino / "MANIFIESTO.json", manifiesto)
    return {"capturas": len(capturas), "abstenciones": len(abstenciones),
            "anteriores_por_fecha": sum(p["prospectiva_acreditada_por_fecha"] for p in capturas)}


def evaluar_cohorte(directorio: Path, filas: list[dict]) -> dict:
    """Une IDs originales y final canónico. Nunca reentrena/regenera/sobrescribe."""
    manifiesto = json.loads((directorio / "MANIFIESTO.json").read_text())
    for nombre in ("MODELO.json", "COHORTE.json"):
        if sha256((directorio / nombre).read_bytes()).hexdigest() != manifiesto[nombre]:
            raise ValueError("Hash de cohorte/modelo no coincide")
    cohorte = json.loads((directorio / "COHORTE.json").read_text())
    modelo = json.loads((directorio / "MODELO.json").read_text())
    validar_modelo(modelo)
    if cohorte["modelo_version"] != modelo["version"] or cohorte["artefacto_sha256"] != sha256(json_bytes(modelo)).hexdigest():
        raise ValueError("Cohorte de otra versión")
    por_id = {str(r["id"]): r for r in filas}
    evaluados, pendientes, excluidos = [], [], []
    for c in cohorte["capturas"]:
        r = por_id.get(c["partido_id"])
        if not r or not final_valido(r) or str(r["fecha_partido"])[:10] > datetime.now(timezone.utc).date().isoformat():
            pendientes.append(c["partido_id"])
            continue
        if (str(r["equipo_local_id"]) != c["equipo_local_id"] or str(r["equipo_visitante_id"]) != c["equipo_visitante_id"] or str(r["fecha_partido"])[:10] != c["fecha_partido"]):
            raise ValueError("Identidad de outcome no coincide con captura")
        limite = c["fecha_partido"] + "T00:00:00+00:00"
        if not c["prospectiva_acreditada_por_fecha"] or not modelo["fit_completed_at"] < cohorte["congelado_en"] < limite:
            excluidos.append(c["partido_id"])
            continue
        real = sum(r[f"{lado}_q{i}"] for lado in ("local", "visitante") for i in range(1, 5))
        pred = c["resultado"]["predicciones"]["COMPLETO"]
        linea = c["resultado"]["linea"]
        p = probabilidades(pred["media_total"], pred["desviacion_total"] ** 2, linea)
        periodos = {}
        for mercado, proyeccion in c["resultado"]["predicciones"].items():
            indices = range(1, 5) if mercado == "COMPLETO" else [int(mercado[1])]
            valor = sum(r[f"{lado}_q{i}"] for lado in ("local", "visitante") for i in indices)
            intervalo = proyeccion["intervalo_predictivo_80_raw"]
            periodos[mercado] = {"real": valor, "error_absoluto": abs(valor - proyeccion["media_total"]),
                                 "dentro_intervalo_80_nominal": intervalo[0] <= valor <= intervalo[1]}
        evaluados.append({"partido_id": c["partido_id"], "real_regulacion": real,
                          "error_absoluto": abs(real - pred["media_total"]),
                          "brier_raw_linea_referencia": (p["over"] - float(real > linea)) ** 2,
                          "periodos": periodos})
    return {"modelo_version": modelo["version"], "n": len(evaluados), "pares": evaluados,
            "pendientes": pendientes, "excluidos_por_temporalidad": excluidos,
            "mae": sum(x["error_absoluto"] for x in evaluados) / len(evaluados) if evaluados else None,
            "mercados": {m: {"n": len(evaluados),
                "mae": sum(x["periodos"][m]["error_absoluto"] for x in evaluados) / len(evaluados) if evaluados else None,
                "cobertura_intervalo_80_nominal": sum(x["periodos"][m]["dentro_intervalo_80_nominal"] for x in evaluados) / len(evaluados) if evaluados else None}
                for m in ("Q1", "Q2", "Q3", "Q4", "COMPLETO")},
            "fuente_independiente_acreditada": False, "certificacion": "NO_CERTIFICADO"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", type=Path, help="Dataset previamente exportado (offline)")
    p.add_argument("--exportar", type=Path, help="Leer Neon READ ONLY y conservar snapshot nuevo")
    p.add_argument("--entrenar", action="store_true")
    p.add_argument("--publicar", action="store_true")
    p.add_argument("--corte", help="Fecha ISO exclusiva; obligatorio al entrenar")
    p.add_argument("--salida", type=Path, help="Artefacto nuevo fuera del repositorio")
    p.add_argument("--congelar", type=Path, help="Directorio nuevo de cohorte")
    p.add_argument("--evaluar", type=Path, help="Directorio de cohorte existente")
    p.add_argument("--informe", type=Path, help="Evaluación nueva, nunca sobrescribir")
    a = p.parse_args()
    if a.publicar and not a.entrenar:
        p.error("--publicar requiere --entrenar explícito")
    if a.entrenar and not (a.corte and a.salida):
        p.error("--entrenar requiere --corte y --salida")
    if a.snapshot and a.exportar:
        p.error("Usar snapshot offline o exportar, no ambos")
    if not (a.snapshot or a.exportar):
        p.error("Indicar --snapshot o --exportar")
    if a.evaluar and not a.informe:
        p.error("--evaluar requiere --informe nuevo")
    filas = json.loads(a.snapshot.read_text()) if a.snapshot else leer_datos()
    if a.exportar:
        escribir_nuevo(a.exportar, {"observado_en": datetime.now(timezone.utc).isoformat(), "filas": filas})
    if isinstance(filas, dict):
        filas = filas["filas"]
    if a.entrenar:
        modelo = entrenar(filas, a.corte)
        escribir_nuevo(a.salida, modelo)
        if a.publicar:
            publicar(modelo)
        print(json.dumps({"version": modelo["version"], "partidos": modelo["partidos_entrenamiento"], "fecha_max": modelo["fecha_max"], "publicado": a.publicar}))
    else:
        modelo = None
    if a.congelar:
        print(json.dumps(congelar(modelo or cargar(), filas, a.congelar)))
    if a.evaluar:
        resultado = evaluar_cohorte(a.evaluar, filas)
        escribir_nuevo(a.informe, resultado)
        print(json.dumps({"evaluados": resultado["n"], "pendientes": len(resultado["pendientes"])}))


if __name__ == "__main__":
    main()
