"""Experimento offline aislado. No importado por rutas ni publicadores de modelos.

Solo modifica el diseño de predicción: identidad contraída hacia el prior de liga.
Los coeficientes se ajustan con TRAIN; CAL selección decide diseño/recencia y una
CAL distinta estima dispersión RAW. No sustituye gates ni cohortes de serving.
"""
from collections import Counter
from datetime import date, datetime
import math
from zoneinfo import ZoneInfo

import numpy as np

from motor.wnba import (ALPHA, FORMATO, MERCADOS, ajustar, conocido, covarianza,
                        exigir, huella, medias, probabilidades)


def validar_publicacion(p):
    contenido = {k: v for k, v in p.items() if k not in ("version", "publicado_utc")}
    exigir(p.get("formato") == FORMATO and p.get("dominio") == "wnba"
           and p.get("version") == "wnba-v1-" + huella(contenido)[:24]
           and p.get("dataset_sha256") == huella(p["datos"]), "Publicación WNBA no íntegra")
    ids = [r["id"] for r in p["datos"]]
    exigir(date.fromisoformat(p["corte_publicacion_exclusivo"]) <= datetime.now(ZoneInfo("America/Bogota")).date(),
           "Corte de publicación futuro")
    exigir(len(ids) == len(set(ids)), "IDs duplicados en snapshot WNBA")
    exigir(all(len(r["y"]) == 8 and all(type(v) is int and v >= 0 for v in r["y"])
               and r["fecha"] < p["corte_publicacion_exclusivo"] for r in p["datos"]),
           "Targets o corte inválidos")


def medias_contraidas(modelo, rows, k):
    """No consulta targets, fechas de EVAL ni estado actualizado del equipo."""
    exigir(math.isfinite(k) and k >= 0, "Contracción inválida")
    entidades = modelo["entidades"]
    n = len(entidades)
    x = np.zeros((2 * len(rows), 2 * n + 2))
    for i, r in enumerate(rows):
        x[2 * i:2 * i + 2, 0] = 1
        x[2 * i, 1] = 1
        for lado, fila_ataque, fila_defensa in (("local_id", 2 * i, 2 * i + 1),
                                                ("visitante_id", 2 * i + 1, 2 * i)):
            tid = r[lado]
            if tid not in entidades:
                continue  # Prior de liga explícito, no identidad ni historial imputados.
            efectivo = modelo["efectivos"][tid]
            peso = efectivo / (efectivo + k) if k else 1.0
            j = entidades[tid]
            x[fila_ataque, 2 + j] = peso
            x[fila_defensa, 2 + n + j] = peso
    y = x @ np.asarray(modelo["coeficientes"])
    return np.concatenate((y[::2], y[1::2]), axis=1)


def seleccionar(train, seleccion, politica):
    variantes = []
    real = np.asarray([sum(r["y"]) for r in seleccion])
    exigir(len(seleccion) >= 10, "CAL selección insuficiente")
    modelos = {}
    for half in politica["variantes"]["semivida_dias"]:
        modelo = ajustar(train, half)
        modelos[half] = modelo
        for k in politica["variantes"]["k_contraccion"]:
            pred = medias_contraidas(modelo, seleccion, k).sum(axis=1)
            variantes.append({"semivida_dias": half, "k": k, "n": len(seleccion),
                              "mae_total": float(np.abs(pred - real).mean())})
    elegida = min(variantes, key=lambda v: v["mae_total"])
    return modelos[elegida["semivida_dias"]], elegida, variantes


def metricas(rows, pred, cov, lineas):
    salida = {}
    for mercado, ix in MERCADOS.items():
        y = np.asarray([sum(r["y"][i] for i in ix) for r in rows])
        mu = pred[:, ix].sum(axis=1)
        var = float(cov[np.ix_(ix, ix)].sum())
        linea = lineas[mercado]
        probs = np.asarray([probabilidades(float(m), var, linea)["over"] for m in mu])
        target = (y > linea).astype(float)
        loss = -(target * np.log(np.clip(probs, 1e-12, 1)) +
                 (1 - target) * np.log(np.clip(1 - probs, 1e-12, 1)))
        salida[mercado] = {"n": len(rows), "mae": float(np.abs(mu - y).mean()),
            "brier_binario": float(((probs - target) ** 2).mean()), "log_loss": float(loss.mean()),
            "linea_fija_train": linea, "varianza_raw": var,
            "cobertura_intervalo80_raw": float((np.abs(mu - y) <= 1.2815515655 * math.sqrt(var)).mean())}
    return salida


def delta_emparejado(rows, pred, ref):
    """IC por clusters de día, no por cuartos ni filas de equipo duplicadas."""
    rng = np.random.default_rng(20261030)
    dias = sorted({r["fecha"] for r in rows})
    grupos = [np.asarray([i for i, r in enumerate(rows) if r["fecha"] == dia]) for dia in dias]
    counts = np.asarray([len(ix) for ix in grupos])
    indices = rng.integers(0, len(dias), size=(1000, len(dias)))
    salida = {}
    for key, ix in MERCADOS.items():
        y = np.asarray([sum(r["y"][i] for i in ix) for r in rows])
        delta = np.abs(pred[:, ix].sum(axis=1) - y) - np.abs(ref[:, ix].sum(axis=1) - y)
        sumas = np.asarray([delta[g].sum() for g in grupos])
        replicas = sumas[indices].sum(axis=1) / counts[indices].sum(axis=1)
        salida[key] = {"n": len(rows), "dias": len(dias), "delta_mae": float(delta.mean()),
                       "ic95_dias": np.quantile(replicas, [.025, .975]).tolist(),
                       "interpretacion": "Negativo favorece experimento; retrospectiva exploratoria, no test intacto"}
    return salida


def ejecutar(publicacion, politica):
    validar_publicacion(publicacion)
    exigir(politica["id"] == "wnba-contraccion-exploratoria-v1-20261030" and ALPHA == 5.0,
           "Política o implementación no compatibles")
    exigir(politica["variantes"]["semivida_dias"] == [None, 365, 730]
           and politica["variantes"]["k_contraccion"] == [0, 8, 24], "Grilla alterada")
    exigir(politica["ventanas"] == {"train_fin_exclusivo": "2024-01-01",
        "seleccion_fin_exclusivo": "2024-07-15", "dispersion_fin_exclusivo": "2025-01-01",
        "eval_fin_exclusivo": "corte_publicacion_exclusivo"}, "Ventanas alteradas")
    rows = sorted([r for r in publicacion["datos"] if r["fase"] == "REG"], key=lambda r: (r["fecha"], r["id"]))
    train = [r for r in rows if r["fecha"] < "2024-01-01"]
    sel = [r for r in rows if "2024-01-01" <= r["fecha"] < "2024-07-15"]
    disp = [r for r in rows if "2024-07-15" <= r["fecha"] < "2025-01-01"]
    test = [r for r in rows if r["fecha"] >= "2025-01-01"]
    exigir(bool(test), "Sin EVAL")
    modelo, elegida, variantes = seleccionar(train, sel, politica)
    resid = np.asarray([r["y"] for r in disp]) - medias_contraidas(modelo, disp, elegida["k"])
    cov = covarianza(resid)
    candidato = {"ridge_train": modelo, "k": elegida["k"], "covarianza": cov.tolist(),
                 "origen_dispersion": "CAL dispersión separada; no calibración probabilística",
                 "orden_features": ["intercepto", "localia"] +
                    [f"{tipo}:{tid}" for tipo in ("ataque", "defensa") for tid, _ in sorted(modelo["entidades"].items(), key=lambda kv: kv[1])]}
    original = publicacion["validacion"]["candidato"]
    mapa = {r["id"]: r for r in rows}
    cohorte = publicacion["validacion"]["cohorte"]
    reproducidas = medias(original, [mapa[r["id"]] for r in cohorte])
    diferencia = float(np.max(np.abs(reproducidas - np.asarray([r["proyeccion"] for r in cohorte]))))
    exigir(diferencia <= 1e-10, "Cohorte original no reproducida")
    baseline = np.mean([r["y"] for r in train], axis=0)
    bcov = covarianza(np.asarray([r["y"] for r in disp]) - baseline)
    lineas = {key: math.floor(float(baseline[ix].sum())) + .5 for key, ix in MERCADOS.items()}
    todas = medias_contraidas(modelo, test, elegida["k"])
    k0 = medias_contraidas(modelo, test, 0)
    validos = np.isfinite(todas).all(axis=1) & (todas >= 0).all(axis=1)
    originales_validos = np.asarray([conocido(original, r) for r in test])
    comun = validos & originales_validos
    exigir(comun.any(), "Sin soporte común para comparación")
    comunes = [r for r, ok in zip(test, comun) if ok]
    ref = medias(original, comunes)
    filtradas = [r for r, ok in zip(test, validos) if ok]
    etiquetas = ["sin_historial_train" if any(t not in modelo["entidades"] for t in (r["local_id"], r["visitante_id"]))
                 else "muestra_baja_train" if not conocido(modelo, r) else "soportado_train" for r in test]
    por_soporte = {}
    for tag in sorted(set(etiquetas)):
        mask = validos & np.asarray([t == tag for t in etiquetas])
        por_soporte[tag] = {"elegibles": etiquetas.count(tag), "predichos": int(mask.sum()),
            "metricas": metricas([r for r, ok in zip(test, mask) if ok], todas[mask], cov, lineas) if mask.any() else None}
    salida = {
        "formato": "experimento-wnba-contraccion-v1", "politica": politica, "politica_sha256": huella(politica),
        "snapshot": {"publicacion": publicacion["version"], "dataset_sha256": publicacion["dataset_sha256"],
                     "corte_exclusivo": publicacion["corte_publicacion_exclusivo"]},
        "ventanas": {nombre: {"n": len(filas), "desde": filas[0]["fecha"], "hasta": filas[-1]["fecha"],
                              "ids_sha256": huella([r["id"] for r in filas])}
                     for nombre, filas in (("train", train), ("seleccion", sel), ("dispersion", disp), ("eval", test))},
        "seleccion": {"elegida": elegida, "variantes": variantes}, "candidato": candidato,
        "reproduccion_original": {"version": original["version"], "n": len(cohorte), "max_delta": diferencia, "sin_refit": True},
        "cobertura": {"denominador": len(test), "experimento": int(validos.sum()), "original": int(originales_validos.sum()),
                      "comunes": int(comun.sum()), "grupos": dict(Counter(etiquetas))},
        "tabla_comun": {"experimento": metricas(comunes, todas[comun], cov, lineas),
                        "original": metricas(comunes, ref, np.asarray(original["covarianza"]), lineas),
                        "media_liga": metricas(comunes, np.tile(baseline, (len(comunes), 1)), bcov, lineas),
                        "delta_original_ic95": delta_emparejado(comunes, todas[comun], ref)},
        "tabla_ampliada": {"experimento": metricas(filtradas, todas[validos], cov, lineas),
                           "media_liga": metricas(filtradas, np.tile(baseline, (len(filtradas), 1)), bcov, lineas),
                           "por_soporte": por_soporte},
        "cohorte_exploratoria": [{"id": r["id"], "fecha": r["fecha"], "local_id": r["local_id"], "visitante_id": r["visitante_id"],
            "observado": r["y"], "grupo": tag, "proyeccion": mu.tolist() if ok else None,
            "motivo_abstencion": None if ok else "Proyección fuera de soporte", "k0_diagnostico": diag.tolist(),
            "original_elegible": bool(orig)} for r, tag, mu, ok, diag, orig in zip(test, etiquetas, todas, validos, k0, originales_validos)],
        "refit_final": None, "activado": False, "calibrador": None, "prospectivos": 0,
        "limitacion": politica["limitacion"],
    }
    salida["experimento_sha256"] = huella(salida)
    return salida
