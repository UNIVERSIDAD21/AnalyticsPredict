"""Distribución WNBA propia: cortes Gaussianos y OT empírico condicionado al empate.

No modifica el candidato v1 ni usa escalas de otra liga. Integración Sobol fija,
discreta y reproducible; probabilidades RAW, no un calibrador.
"""
from functools import lru_cache
import math

import numpy as np
from scipy.special import ndtri
from scipy.stats import qmc

from motor.wnba import MERCADOS, conocido, exigir, huella, medias

VERSION = "wnba-condicional-ot-v2"
MIN_OT = 10
POTENCIA = 15


@lru_cache(maxsize=8)
def integracion(dimension, potencia=POTENCIA):
    u = qmc.Sobol(d=dimension + 1, scramble=True, seed=9128626).random_base2(potencia)
    return ndtri(np.clip(u[:, :dimension], 1e-12, 1 - 1e-12)), u[:, -1]


def ajustar_ot(rows):
    casos = [r for r in rows if sum(r["y"][:4]) == sum(r["y"][4:])
             and r["local_ot"] + r["visitante_ot"] > 0
             and r["local_ot"] != r["visitante_ot"]]
    return {"n": len(casos), "minimo": MIN_OT,
            "incrementos": [[r["local_ot"], r["visitante_ot"]] for r in casos],
            "partidos_sha256": huella([r["id"] for r in casos]),
            "desde": min((r["fecha"] for r in casos), default=None),
            "hasta": max((r["fecha"] for r in casos), default=None),
            "metodo": "bootstrap conjunto de OT completo WNBA, solo tras empate de regulación"}


def condicionar(mu, cov, parciales):
    exigir(isinstance(parciales, list) and len(parciales) <= 3,
           "Solo se admiten Q1, Q2 y Q3 completos y consecutivos")
    exigir(all(isinstance(q, (list, tuple)) and len(q) == 2
               and all(type(x) is int and 0 <= x <= 100 for x in q) for q in parciales),
           "Cada cuarto terminado requiere puntos enteros local/visitante entre 0 y 100, no acumulados")
    observados = [i for i in range(8) if i % 4 < len(parciales)]
    pendientes = [i for i in range(8) if i not in observados]
    valores = np.array([parciales[i % 4][i // 4] for i in observados], float)
    media = mu.copy()
    matriz = np.zeros((8, 8))
    if observados:
        ganancia = np.linalg.solve(cov[np.ix_(observados, observados)],
                                   cov[np.ix_(observados, pendientes)]).T
        media[pendientes] += ganancia @ (valores - mu[observados])
        media[observados] = valores
        posterior = cov[np.ix_(pendientes, pendientes)] - ganancia @ cov[np.ix_(observados, pendientes)]
    else:
        posterior = cov
    exigir(np.isfinite(media).all() and (media[pendientes] >= 0).all(),
           "Abstención: marcadores contradictorios con el soporte del modelo WNBA")
    matriz[np.ix_(pendientes, pendientes)] = (posterior + posterior.T) / 2
    return media, matriz, pendientes


def masa(valores, linea):
    return {"over": float(np.mean(valores > linea)),
            "under": float(np.mean(valores < linea)),
            "push": float(np.mean(valores == linea))}


def ganador(local, visita):
    return {"local": float(np.mean(local > visita)),
            "empate": float(np.mean(local == visita)),
            "visitante": float(np.mean(local < visita))}


def resumen(local, visita, observado=False):
    total = local + visita
    var = float(np.var(total))
    return {"media_local": float(local.mean()), "media_visitante": float(visita.mean()),
            "media_total": float(total.mean()), "desviacion_total": math.sqrt(var),
            "varianza_total": var, "intervalo_80_raw": np.quantile(total, [.1, .9]).tolist(),
            "observado": observado, "ganador": ganador(local, visita)}


def predecir_ampliado(m, local, visita, mercado, linea, parciales, ot, potencia=POTENCIA, lineas=None, devolver_muestras=False):
    exigir(mercado in MERCADOS and math.isfinite(linea) and 0 <= linea <= 600, "Mercado/línea inválido")
    exigir(local != visita and conocido(m, {"local_id": local, "visitante_id": visita}),
           "Abstención: equipos distintos con al menos 8 partidos y 6 efectivos")
    exigir(mercado == "COMPLETO" or int(mercado[1]) > len(parciales),
           "Mercado ya resuelto: elige un periodo posterior al corte")
    mu = medias(m, [{"local_id": local, "visitante_id": visita}])[0]
    cov = np.asarray(m["covarianza"])
    media, posterior, pendientes = condicionar(mu, cov, parciales)
    z, uot = integracion(len(pendientes), potencia)
    valores, vectores = np.linalg.eigh(posterior[np.ix_(pendientes, pendientes)])
    exigir(valores.min() > -1e-7, "Covarianza WNBA inválida")
    muestras = np.tile(media, (len(z), 1))
    muestras[:, pendientes] = np.maximum(0, np.rint(
        media[pendientes] + z @ (vectores * np.sqrt(np.maximum(0, valores))).T))
    h, a = muestras[:, :4].sum(axis=1), muestras[:, 4:].sum(axis=1)
    predictions = {f"Q{i+1}": resumen(muestras[:, i], muestras[:, i+4], i < len(parciales)) for i in range(4)}
    regulacion = resumen(h, a)
    incluye_ot = not parciales
    empate = h == a
    incremento = np.zeros((len(z), 2))
    if incluye_ot:
        exigir(ot["n"] >= MIN_OT, f"Abstención OT: requiere {MIN_OT} empates WNBA con prórroga en el alcance; disponibles {ot['n']}")
        ix = np.minimum((uot * ot["n"]).astype(int), ot["n"] - 1)
        incremento[empate] = np.asarray(ot["incrementos"])[ix[empate]]
    hf, af = h + incremento[:, 0], a + incremento[:, 1]
    predictions["COMPLETO"] = resumen(hf, af)
    if mercado == "COMPLETO":
        objetivos = hf + af
    else:
        i = int(mercado[1]) - 1
        objetivos = muestras[:, i] + muestras[:, i+4]
    evaluacion = {}
    for key, corte_lineas in (lineas or {}).items():
        if key != "COMPLETO" and int(key[1]) <= len(parciales):
            continue
        vals = hf+af if key == "COMPLETO" else muestras[:, int(key[1])-1]+muestras[:, int(key[1])+3]
        evaluacion[key] = {str(l):masa(vals,l) for l in corte_lineas}
    return {"predicciones": predictions, "probabilidades": masa(objetivos, linea),
            **({"_muestras":{**{f"Q{i+1}":muestras[:,i]+muestras[:,i+4] for i in range(4)},"COMPLETO":hf+af}} if devolver_muestras else {}),
            **({"evaluacion_lineas":evaluacion} if lineas else {}),
            "ganador_regulacion": regulacion["ganador"], "regulacion": regulacion,
            "ganador_mercado": predictions[mercado]["ganador"],
            "incluye_ot": incluye_ot, "parciales": parciales,
            "ot": {**{k: v for k, v in ot.items() if k != "incrementos"},
                   "probabilidad_empate_regulacion": float(empate.mean()),
                   "media_local": float(incremento[:, 0].mean()),
                   "media_visitante": float(incremento[:, 1].mean())},
            "condicionamiento": {"version": VERSION, "integracion": "Sobol discreto determinista",
                 "simulaciones": len(z), "calibracion": "SIN_CALIBRAR",
                 "indices_observados": [i for i in range(8) if i not in pendientes],
                 "covarianza_posterior": posterior.tolist(),
                 "media_base": mu.tolist(), "media_condicional": media.tolist(),
                 "metodo": "Normal multivariada WNBA condicionada a cada cuarto terminado; complemento de Schur. Sin reloj/posesiones."}}
