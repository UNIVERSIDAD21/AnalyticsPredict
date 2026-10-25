"""Ridge WNBA puro y separado: regulación, selección temporal y probabilidades RAW."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from hashlib import sha256
import json
import math
from zoneinfo import ZoneInfo

import numpy as np

FORMATO = "wnba_ridge_regulacion_v1"
MERCADOS = {
    "Q1": [0, 4],
    "Q2": [1, 5],
    "Q3": [2, 6],
    "Q4": [3, 7],
    "COMPLETO": list(range(8)),
}
ALPHA = 5.0
MIN_EQUIPO = 8
MIN_EFECTIVOS = 6
RECENCIAS = (None, 365, 730)
BOGOTA = ZoneInfo("America/Bogota")


def exigir(ok, mensaje):
    if not ok:
        raise ValueError(mensaje)


def huella(value):
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def normalizar(filas):
    salida, vistos = [], set()
    for r in filas:
        if (
            r.get("competicion_codigo") != "wnba"
            or r.get("estado") != "FINALIZADO"
            or r.get("valido") is not True
        ):
            continue
        if r.get("fase") not in ("REG", "POST") or r.get("tipo_partido") != r.get(
            "fase"
        ):
            continue
        original = r.get("registro", {})
        if (
            original.get("competicion") != "wnba"
            or original.get("fuente") != "ESPN"
            or original.get("final_completo") is not True
        ):
            continue
        puntos = [
            r.get(f"{lado}_q{i}")
            for lado in ("local", "visitante")
            for i in range(1, 5)
        ]
        if any(type(x) is not int or x < 0 for x in puntos):
            continue
        valido = True
        for lado in ("local", "visitante"):
            ot, total = r.get(lado + "_ot"), r.get(lado + "_total")
            if type(ot) is not int or type(total) is not int or total <= 0 or ot < 0:
                valido = False
                break
            if sum(r[f"{lado}_q{i}"] for i in range(1, 5)) + ot != total:
                valido = False
                break
            if any(
                original.get(f"{lado}_{k}") != r.get(f"{lado}_{k}")
                for k in ("q1", "q2", "q3", "q4", "ot", "total")
            ):
                valido = False
                break
        if not valido or r["local_total"] == r["visitante_total"]:
            continue
        local, visita = str(r["equipo_local_id"]), str(r["equipo_visitante_id"])
        if local == visita or not r.get("partido_id"):
            continue
        inicio = datetime.fromisoformat(str(r["inicio_utc"]).replace("Z", "+00:00"))
        exigir(inicio.tzinfo is not None, "Inicio WNBA sin zona")
        fecha = inicio.astimezone(BOGOTA).date().isoformat()
        exigir(r["temporada_nombre"] == fecha[:4], "Temporada WNBA no anual")
        eid = str(r["source_game_id"])
        exigir(eid not in vistos, "ID WNBA duplicado")
        vistos.add(eid)
        salida.append(
            {
                "id": str(r["partido_id"]),
                "source_game_id": eid,
                "fecha": fecha,
                "inicio_utc": inicio.isoformat(),
                "temporada_id": str(r["temporada_id"]),
                "temporada": r["temporada_nombre"],
                "fase": r["fase"],
                "local_id": local,
                "visitante_id": visita,
                "local": r["local"],
                "visitante": r["visitante"],
                "y": puntos,
                "local_ot": r["local_ot"],
                "visitante_ot": r["visitante_ot"],
                "local_total": r["local_total"],
                "visitante_total": r["visitante_total"],
            }
        )
    return sorted(salida, key=lambda r: (r["inicio_utc"], r["id"]))


def alcance(datos, temporadas, corte, fases=("REG",)):
    date.fromisoformat(corte)
    exigir(
        bool(temporadas) and len(set(temporadas)) == len(temporadas),
        "Selecciona temporadas WNBA sin duplicados",
    )
    exigir(
        set(temporadas) <= {r["temporada_id"] for r in datos},
        "Temporada ajena o sin resultados elegibles WNBA",
    )
    exigir(
        bool(fases)
        and "REG" in fases
        and set(fases) <= {"REG", "POST"}
        and len(set(fases)) == len(fases),
        "REG es base; POST optativo. COPA/PRE/exhibiciones no soportadas",
    )
    return [
        r
        for r in datos
        if r["fecha"] < corte and r["temporada_id"] in temporadas and r["fase"] in fases
    ]


def _pesos(rows, semivida):
    if semivida is None:
        return np.ones(len(rows))
    maxfecha = date.fromisoformat(rows[-1]["fecha"])
    w = np.array(
        [
            2 ** (-((maxfecha - date.fromisoformat(r["fecha"])).days) / semivida)
            for r in rows
        ]
    )
    return w / w.mean()


def _x(rows, entidades):
    k = len(entidades)
    x = np.zeros((2 * len(rows), 2 * k + 2))
    for i, r in enumerate(rows):
        h, a = entidades[r["local_id"]], entidades[r["visitante_id"]]
        x[2 * i, [0, 1, 2 + h, 2 + k + a]] = 1
        x[2 * i + 1, [0, 2 + a, 2 + k + h]] = 1
    return x


def ajustar(rows, semivida):
    exigir(
        len(rows) >= 60,
        "Muestra insuficiente: requiere 60 partidos para el ajuste inicial",
    )
    entidades = {
        key: i
        for i, key in enumerate(
            sorted({r[s] for r in rows for s in ("local_id", "visitante_id")})
        )
    }
    x = _x(rows, entidades)
    y = np.array([q for r in rows for q in (r["y"][:4], r["y"][4:])], float)
    w = _pesos(rows, semivida)
    wr = np.repeat(w, 2)
    p = np.eye(x.shape[1]) * ALPHA
    p[0, 0] = 0
    coef = np.linalg.solve(x.T @ (x * wr[:, None]) + p, x.T @ (y * wr[:, None]))
    samples = Counter()
    sw = Counter()
    sw2 = Counter()
    for r, weight in zip(rows, w):
        for s in ("local_id", "visitante_id"):
            samples[r[s]] += 1
            sw[r[s]] += float(weight)
            sw2[r[s]] += float(weight**2)
    return {
        "entidades": entidades,
        "coeficientes": coef.tolist(),
        "muestras": dict(samples),
        "efectivos": {k: sw[k] ** 2 / sw2[k] for k in sw},
        "semivida_dias": semivida,
        "fecha_min": rows[0]["fecha"],
        "fecha_max": rows[-1]["fecha"],
        "n": len(rows),
    }


def conocido(m, r):
    return all(
        m["muestras"].get(r[s], 0) >= MIN_EQUIPO
        and m["efectivos"].get(r[s], 0) >= MIN_EFECTIVOS
        for s in ("local_id", "visitante_id")
    )


def medias(m, rows):
    y = _x(rows, m["entidades"]) @ np.array(m["coeficientes"])
    return np.concatenate((y[::2], y[1::2]), axis=1)


def covarianza(errores):
    exigir(
        len(errores) >= 40,
        "Muestra insuficiente: requiere 40 residuos temporales válidos para dispersión",
    )
    e = np.array(errores, float)
    cov = e.T @ e / len(e)
    return 0.9 * cov + 0.1 * np.diag(np.diag(cov)) + np.eye(8) * 1e-6


def elegir_recencia(train, cal):
    models = [ajustar(train, h) for h in RECENCIAS]
    iguales = [r for r in cal if all(conocido(m, r) for m in models)]
    if len(iguales) < 10:
        return None, {
            "n": len(iguales),
            "motivo": "Selección temporal insuficiente: política uniforme predefinida",
            "variantes": [],
        }
    real = np.array([sum(r["y"]) for r in iguales])
    scores = []
    for m in models:
        scores.append(
            {
                "semivida_dias": m["semivida_dias"],
                "mae_total": float(
                    np.abs(medias(m, iguales).sum(axis=1) - real).mean()
                ),
            }
        )
    chosen = min(range(len(scores)), key=lambda i: scores[i]["mae_total"])
    return RECENCIAS[chosen], {
        "n": len(iguales),
        "motivo": "Menor MAE total solo en CAL selección; empate favorece uniforme",
        "variantes": scores,
    }


def ajustar_alcance(rows):
    exigir(
        len(rows) >= 120,
        "Muestra insuficiente: mínimo 120 finales elegibles en temporadas/corte seleccionados",
    )
    # Grupos por día: ningún evento simultáneo se divide entre entrenamiento/CAL.
    ndisp = min(200, max(40, math.ceil(len(rows) * 0.2)))
    corte_disp = rows[-ndisp]["fecha"]
    disp = [r for r in rows if r["fecha"] >= corte_disp]
    prev = [r for r in rows if r["fecha"] < corte_disp]
    nsel = min(200, max(20, math.ceil(len(prev) * 0.2)))
    exigir(
        len(prev) > nsel + 59,
        "Muestra temporal insuficiente para separar ajuste y dispersión",
    )
    corte_sel = prev[-nsel]["fecha"]
    train = [r for r in prev if r["fecha"] < corte_sel]
    sel = [r for r in prev if r["fecha"] >= corte_sel]
    half, selection = elegir_recencia(train, sel)
    candidato = ajustar(prev, half)
    validos = [r for r in disp if conocido(candidato, r)]
    errores = (
        np.array([r["y"] for r in validos]) - medias(candidato, validos)
        if validos
        else []
    )
    cov = covarianza(errores)
    m = ajustar(rows, half)
    m.update(
        covarianza=cov.tolist(),
        dataset_sha256=huella(rows),
        version="wnba-ajuste-"
        + huella({"datos": huella(rows), "half": half, "alpha": ALPHA})[:20],
        dispersion={
            "origen": "residuos temporales del candidato previo al refit; no calibración probabilística",
            "train_n": len(train),
            "seleccion_n": len(sel),
            "dispersión_n": len(validos),
            "dispersion_candidatos": len(disp),
            "desde": corte_disp,
            "seleccion_recencia": selection,
        },
    )
    return m


def probabilidades(mu, var, linea):
    exigir(
        all(math.isfinite(v) for v in (mu, var, linea))
        and mu >= 0
        and var > 0
        and linea >= 0,
        "Distribución/línea no válida",
    )
    sd = math.sqrt(var)
    cdf = lambda x: 0.5 * (1 + math.erf((x - mu) / sd / math.sqrt(2)))
    over = 1 - cdf(math.floor(linea) + 0.5)
    under = 0.0 if linea == 0 else cdf(math.ceil(linea) - 0.5)
    push = max(0.0, 1 - over - under) if float(linea).is_integer() else 0.0
    if not float(linea).is_integer():
        under = 1 - over
    vals = np.clip([over, under, push], 0, 1)
    vals /= vals.sum()
    return {k: float(v) for k, v in zip(("over", "under", "push"), vals)}


def predecir(m, local, visitante, mercado, linea):
    exigir(
        mercado in MERCADOS and math.isfinite(linea) and 0 <= linea <= 600,
        "Mercado/línea inválido",
    )
    exigir(local != visitante, "Selecciona equipos distintos")
    row = {"local_id": local, "visitante_id": visitante}
    exigir(
        conocido(m, row),
        f"Abstención: cada equipo requiere {MIN_EQUIPO} partidos y {MIN_EFECTIVOS} efectivos en el alcance elegido",
    )
    mu = medias(m, [row])[0]
    cov = np.array(m["covarianza"])
    exigir(
        np.isfinite(mu).all() and (mu >= 0).all(),
        "Abstención: proyección fuera de soporte",
    )
    predictions = {}
    for key, ix in MERCADOS.items():
        h = [i for i in ix if i < 4]
        a = [i for i in ix if i >= 4]
        var = float(cov[np.ix_(ix, ix)].sum())
        sd = math.sqrt(var)
        predictions[key] = {
            "media_local": float(mu[h].sum()),
            "media_visitante": float(mu[a].sum()),
            "media_total": float(mu[ix].sum()),
            "desviacion_total": sd,
            "varianza_total": var,
            "intervalo_80_raw": [
                max(0, float(mu[ix].sum()) - 1.2815515655 * sd),
                float(mu[ix].sum()) + 1.2815515655 * sd,
            ],
        }
    selected = predictions[mercado]
    p = probabilidades(selected["media_total"], selected["varianza_total"], linea)
    d = np.array([1] * 4 + [-1] * 4)
    mean = float(d @ mu)
    sd = math.sqrt(float(d @ cov @ d))
    cdf = lambda x: 0.5 * (1 + math.erf((x - mean) / sd / math.sqrt(2)))
    winner = {
        "local": 1 - cdf(0.5),
        "empate": cdf(0.5) - cdf(-0.5),
        "visitante": cdf(-0.5),
    }
    return {
        "predicciones": predictions,
        "probabilidades": p,
        "ganador_regulacion": winner,
    }


def evaluar_congelado(datos):
    rows = [r for r in datos if r["fase"] == "REG"]
    train = [r for r in rows if r["fecha"] < "2024-01-01"]
    select = [r for r in rows if "2024-01-01" <= r["fecha"] < "2024-07-15"]
    disp = [r for r in rows if "2024-07-15" <= r["fecha"] < "2025-01-01"]
    test = [r for r in rows if r["fecha"] >= "2025-01-01"]
    half, selection = elegir_recencia(train, select)
    model = ajustar(train, half)
    cal = [r for r in disp if conocido(model, r)]
    cov = covarianza(np.array([r["y"] for r in cal]) - medias(model, cal))
    model["covarianza"] = cov.tolist()
    version = "wnba-candidato-" + huella(model)[:20]
    model["version"] = version
    validos = [r for r in test if conocido(model, r)]
    exigir(bool(validos), "No hay evaluación temporal WNBA utilizable")
    preds = medias(model, validos)
    truth = np.array([r["y"] for r in validos])
    baseline = np.array([r["y"] for r in train]).mean(axis=0)
    bcov = covarianza(np.array([r["y"] for r in cal]) - baseline)
    metrics = {}
    cohort = []
    for key, ix in MERCADOS.items():
        y = truth[:, ix].sum(axis=1)
        yhat = preds[:, ix].sum(axis=1)
        base = float(baseline[ix].sum())
        var = float(cov[np.ix_(ix, ix)].sum())
        bvar = float(bcov[np.ix_(ix, ix)].sum())
        line = math.floor(base) + 0.5
        integer = round(base)
        probs = np.array(
            [list(probabilidades(float(v), var, line).values()) for v in yhat]
        )
        bprobs = np.array([list(probabilidades(base, bvar, line).values())] * len(y))
        target = np.array(
            [[float(v > line), float(v < line), float(v == line)] for v in y]
        )
        pushprobs = np.array(
            [list(probabilidades(float(v), var, integer).values()) for v in yhat]
        )
        pushtarget = np.array(
            [[float(v > integer), float(v < integer), float(v == integer)] for v in y]
        )
        bins = []
        for i in range(10):
            mask = (probs[:, 0] >= i / 10) & (
                (probs[:, 0] < (i + 1) / 10) if i < 9 else (probs[:, 0] <= 1)
            )
            bins.append(
                {
                    "desde": i / 10,
                    "hasta": (i + 1) / 10,
                    "n": int(mask.sum()),
                    "probabilidad_media": (
                        float(probs[mask, 0].mean()) if mask.any() else None
                    ),
                    "frecuencia_observada": (
                        float(target[mask, 0].mean()) if mask.any() else None
                    ),
                }
            )
        metrics[key] = {
            "n": len(y),
            "mae": float(np.abs(yhat - y).mean()),
            "mae_referencia": float(np.abs(base - y).mean()),
            "linea": line,
            "brier_multiclase": float(((probs - target) ** 2).sum(axis=1).mean()),
            "brier_referencia": float(((bprobs - target) ** 2).sum(axis=1).mean()),
            "log_loss": float(
                -(target * np.log(np.maximum(probs, 1e-12))).sum(axis=1).mean()
            ),
            "linea_entera": integer,
            "brier_con_push": float(((pushprobs - pushtarget) ** 2).sum(axis=1).mean()),
            "push_observados": int((y == integer).sum()),
            "calibracion_bins": bins,
            "cobertura_intervalo80": float(
                (np.abs(yhat - y) <= 1.2815515655 * math.sqrt(var)).mean()
            ),
        }
    for r, mu in zip(validos, preds):
        cohort.append(
            {
                "id": r["id"],
                "fecha": r["fecha"],
                "observado": r["y"],
                "proyeccion": mu.tolist(),
            }
        )
    return {
        "tipo": "retrospectiva exploratoria de candidato congelado; no prospectiva",
        "candidato_version": version,
        "candidato": model,
        "train": {
            "n": len(train),
            "desde": train[0]["fecha"],
            "hasta": train[-1]["fecha"],
        },
        "cal_seleccion": {
            "n": len(select),
            "desde": "2024-01-01",
            "fin_exclusivo": "2024-07-15",
            "resultado": selection,
        },
        "cal_dispersion": {
            "n": len(cal),
            "desde": "2024-07-15",
            "fin_exclusivo": "2025-01-01",
        },
        "evaluacion": {
            "partidos": len(test),
            "analizados": len(validos),
            "abstenciones": len(test) - len(validos),
            "cobertura": len(validos) / len(test),
            "desde": test[0]["fecha"],
            "hasta": test[-1]["fecha"],
            "mercados": metrics,
        },
        "cohorte": cohort,
        "rechazados": [
            {
                "id": r["id"],
                "motivo": "Equipo nuevo o muestra insuficiente para el candidato TRAIN",
            }
            for r in test
            if not conocido(model, r)
        ],
        "calibrador": None,
        "prospectivos": 0,
        "limitacion": "Estas métricas corresponden solo al candidato identificado, no al refit final ni a otras selecciones de temporadas.",
    }
