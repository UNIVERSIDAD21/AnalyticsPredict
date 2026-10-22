"""Ridge Euroliga aislado: cuartos de 10 minutos, solo regulación, sin apuestas.

Comparte las funciones Ridge con NBA, nunca sus pesos, calibradores ni escalas.
Entrenar es explícito/offline; cargar y predecir no acceden a PostgreSQL.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

import numpy as np

from motor_autoentrenamiento.entrenador_bd import ajustar_ridge, construir_matriz_diseno, normalizar_nombre

DOMINIO = "euroleague"
FORMATO = "euroliga_ridge_regulacion_v1"
MERCADOS = ("Q1", "Q2", "Q3", "Q4", "COMPLETO")
MIN_EQUIPO = 6
ALPHA = 5.0  # Fijado antes de esta evaluación; sin búsqueda sobre EVAL.
SHRINKAGE = 0.1


def json_bytes(valor: Any) -> bytes:
    return json.dumps(valor, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def ruta_activa() -> Path:
    return Path(os.getenv("ANALYTICSPREDICT_MODELO_EUROLIGA_ACTIVO", str(
        Path.home() / ".local/share/analyticspredict/euroliga/activo.json"))).expanduser()


def final_valido(r: dict) -> bool:
    if r.get("competicion_codigo") != DOMINIO or r.get("valido") is not True or r.get("tipo_partido") not in ("REG", "POST"):
        return False
    if r.get("equipo_local_id") == r.get("equipo_visitante_id"):
        return False
    for lado in ("local", "visitante"):
        valores = [r.get(f"{lado}_q{i}") for i in range(1, 5)]
        ot, total = r.get(f"{lado}_ot"), r.get(f"{lado}_total")
        if any(type(v) is not int or v < 0 for v in valores + [ot, total]):
            return False
        if total <= 0 or sum(valores) <= 0 or sum(valores) + ot != total:
            return False
    return r["local_total"] != r["visitante_total"]


def preparar_filas(filas: list[dict], corte: str) -> list[dict]:
    """Snapshot explícito; excluye futuros y no inventa periodos/OT."""
    date.fromisoformat(corte)
    salida, vistos = [], set()
    campos = ("id", "equipo_local_id", "equipo_visitante_id", "local", "visitante", "temporada_id", "temporada_nombre", "tipo_partido")
    for fila in filas:
        fecha = str(fila["fecha_partido"])[:10]
        if fecha >= corte or not final_valido(fila):
            continue
        r = {k: str(fila[k]) for k in campos}
        r["fecha_partido"] = fecha
        for lado in ("local", "visitante"):
            for periodo in ("q1", "q2", "q3", "q4", "ot", "total"):
                r[f"{lado}_{periodo}"] = fila[f"{lado}_{periodo}"]
        # El hash incluye identidad, nombres y targets; no timestamps de mantenimiento.
        llave = (fecha, r["equipo_local_id"], r["equipo_visitante_id"], r["tipo_partido"])
        if llave in vistos:
            raise ValueError("Snapshot con partido Euroliga duplicado")
        vistos.add(llave)
        salida.append(r)
    return sorted(salida, key=lambda r: (r["fecha_partido"], r["id"]))


def _targets(filas: list[dict]) -> np.ndarray:
    return np.array([[r[f"{lado}_q{i}"] for lado in ("local", "visitante") for i in range(1, 5)] for r in filas], dtype=float)


def _ajustar(filas: list[dict]) -> dict:
    if len(filas) < 100:
        raise ValueError("Se requieren al menos 100 finales Euroliga para ajustar Ridge")
    entidades = sorted({normalizar_nombre(r[lado]) for r in filas for lado in ("local", "visitante")})
    indices = {nombre: i for i, nombre in enumerate(entidades)}
    nombres, rivales, localias, ye, yr = [], [], [], [], []
    y = _targets(filas)
    for r, targets in zip(filas, y):
        nombres.extend((r["local"], r["visitante"]))
        rivales.extend((r["visitante"], r["local"]))
        localias.extend((1, 0))
        ye.extend((targets[:4], targets[4:]))
        yr.extend((targets[4:], targets[:4]))
    x = construir_matriz_diseno(nombres, rivales, localias, indices)
    we, _ = ajustar_ridge(x, np.array(ye), ALPHA)
    wr, _ = ajustar_ridge(x, np.array(yr), ALPHA)
    conteos = Counter(normalizar_nombre(r[lado]) for r in filas for lado in ("local", "visitante"))
    return {"entidades": indices, "pesos_equipo": we.tolist(), "pesos_rival": wr.tolist(), "muestras_equipo": dict(conteos)}


def _conocido(modelo: dict, r: dict) -> bool:
    return all(modelo["muestras_equipo"].get(normalizar_nombre(r[k]), 0) >= MIN_EQUIPO for k in ("local", "visitante"))


def _medias(modelo: dict, filas: list[dict]) -> np.ndarray:
    x = construir_matriz_diseno([r["local"] for r in filas], [r["visitante"] for r in filas], [1] * len(filas), modelo["entidades"])
    return np.concatenate((x @ np.array(modelo["pesos_equipo"]), x @ np.array(modelo["pesos_rival"])), axis=1)


def _cdf(z: float) -> float:
    return (1.0 + math.erf(z / math.sqrt(2))) / 2


def probabilidades(media: float, varianza: float, linea: float) -> dict:
    """Normal discretizada: líneas enteras conservan masa de empate/push."""
    if varianza <= 1e-10:
        return {"over": float(media > linea), "under": float(media < linea), "push": float(media == linea)}
    sigma = math.sqrt(varianza)
    over = 1 - _cdf((math.floor(linea) + 0.5 - media) / sigma)
    under = _cdf((math.ceil(linea) - 0.5 - media) / sigma)
    if not float(linea).is_integer():
        return {"over": over, "under": 1 - over, "push": 0.0}
    return {"over": over, "under": under, "push": max(0.0, 1 - over - under)}


def _evaluar(modelo: dict, cov: np.ndarray, train: list[dict], test: list[dict]) -> dict:
    vistos = [r for r in test if _conocido(modelo, r)]
    salida = {"partidos": len(test), "evaluados": len(vistos), "abstenciones": len(test) - len(vistos),
              "cobertura": len(vistos) / len(test) if test else None, "mercados": {}}
    if not vistos:
        return salida
    mu, y = _medias(modelo, vistos), _targets(vistos)
    baseline = _targets(train).mean(axis=0)
    for mercado in MERCADOS:
        ix = list(range(8)) if mercado == "COMPLETO" else [int(mercado[1]) - 1, int(mercado[1]) + 3]
        pred, real = mu[:, ix].sum(axis=1), y[:, ix].sum(axis=1)
        base = float(baseline[ix].sum())
        # Línea fija de referencia derivada exclusivamente de TRAIN, no de EVAL/mercado.
        linea = math.floor(base) + 0.5
        var = float(cov[np.ix_(ix, ix)].sum())
        probs = np.array([probabilidades(float(m), var, linea)["over"] for m in pred])
        eventos = (real > linea).astype(float)
        salida["mercados"][mercado] = {
            "mae": float(np.abs(pred - real).mean()), "mae_media_liga": float(np.abs(base - real).mean()),
            "linea_referencia_train": linea, "brier_raw": float(((probs - eventos) ** 2).mean()),
            "brier_referencia_50": 0.25, "n": len(vistos),
            "cobertura_intervalo_80": float((np.abs(pred - real) <= 1.2815515655 * math.sqrt(var)).mean()),
        }
    return salida


def entrenar(filas: list[dict], corte: str, inicio_cal: str = "2024-09-01", inicio_eval: str = "2025-09-01") -> dict:
    """TRAIN/CAL/EVAL cronológicos fijados. Refit final separado de su evaluación.

    CAL estima covarianza de errores fuera de muestra, NO calibra probabilidades.
    La covarianza se transfiere al refit como aproximación explícita sin certificarlo.
    """
    if not inicio_cal < inicio_eval < corte:
        raise ValueError("Se requiere TRAIN < CAL < EVAL < corte")
    inicio = datetime.now(timezone.utc).isoformat()
    datos = preparar_filas(filas, corte)
    train = [r for r in datos if r["fecha_partido"] < inicio_cal]
    cal = [r for r in datos if inicio_cal <= r["fecha_partido"] < inicio_eval]
    test = [r for r in datos if r["fecha_partido"] >= inicio_eval]
    desarrollo = _ajustar(train)
    cal_validos = [r for r in cal if _conocido(desarrollo, r)]
    if len(cal_validos) < 100 or len(test) < 100:
        raise ValueError("CAL y EVAL necesitan al menos 100 finales (CAL con equipos conocidos)")
    errores = _targets(cal_validos) - _medias(desarrollo, cal_validos)
    # Segundo momento, incluye sesgo sin corregir la media tras observar CAL.
    cov = errores.T @ errores / len(errores)
    cov = (1 - SHRINKAGE) * cov + SHRINKAGE * np.diag(np.diag(cov)) + np.eye(8) * 1e-6
    validacion = {
        "tipo": "retrospectiva_exploratoria_no_prospectiva", "alpha_fijo": ALPHA,
        "train_fin_exclusivo": inicio_cal, "cal_fin_exclusivo": inicio_eval,
        "train_n": len(train), "cal_n": len(cal), "cal_util_n": len(cal_validos),
        "dataset_desarrollo_sha256": sha256(json_bytes(train + cal)).hexdigest(),
        "evaluacion": _evaluar(desarrollo, cov, train, test),
        "por_temporada": {s: _evaluar(desarrollo, cov, train, [r for r in test if r["temporada_id"] == s]) for s in sorted({r["temporada_id"] for r in test})},
        "calibrador_probabilistico": None, "prospectiva_n": 0,
        "limitacion": "EVAL mide el candidato TRAIN, no el refit final. CAL estima dispersión; no demuestra calibración ni independencia de fuente.",
    }
    modelo = _ajustar(datos)
    temporada_reciente = datos[-1]["temporada_id"]
    muestras_temporada = Counter(normalizar_nombre(r[lado]) for r in datos if r["temporada_id"] == temporada_reciente for lado in ("local", "visitante"))
    catalogo = {normalizar_nombre(r[lado]): {"id": r[f"equipo_{lado}_id"], "nombre": r[lado]} for r in datos for lado in ("local", "visitante")}
    modelo.update({"formato": FORMATO, "dominio": DOMINIO, "alpha": ALPHA, "min_partidos_equipo": MIN_EQUIPO,
                   "duracion_cuarto_minutos": 10, "incluye_ot": False,
                   "dataset_sha256": sha256(json_bytes(datos)).hexdigest(), "partidos_entrenamiento": len(datos),
                   "training_ids": [r["id"] for r in datos], "corte_exclusivo": corte,
                   "fecha_min": datos[0]["fecha_partido"], "fecha_max": datos[-1]["fecha_partido"],
                   "fit_started_at": inicio, "fit_completed_at": datetime.now(timezone.utc).isoformat(),
                   "covarianza": cov.tolist(), "origen_dispersion": "errores_CAL_temporal_del_candidato_TRAIN_transferidos_al_refit",
                   "catalogo": catalogo, "muestras_equipo_temporada": dict(muestras_temporada),
                   "temporada_reciente": datos[-1]["temporada_nombre"],
                   "validacion": validacion, "certificacion": "NO_CERTIFICADO"})
    modelo["version"] = "euro-" + sha256(json_bytes(modelo)).hexdigest()[:20]
    return modelo


def validar_modelo(modelo: dict) -> None:
    if modelo.get("formato") != FORMATO or modelo.get("dominio") != DOMINIO or modelo.get("incluye_ot") is not False:
        raise ValueError("Artefacto incompatible: se requiere Euroliga regulación v1")
    contenido = {k: v for k, v in modelo.items() if k != "version"}
    if modelo.get("version") != "euro-" + sha256(json_bytes(contenido)).hexdigest()[:20]:
        raise ValueError("Identidad/hash del modelo Euroliga no coincide")
    entidades = modelo["entidades"]
    k = len(entidades)
    if sorted(entidades.values()) != list(range(k)):
        raise ValueError("Índices de entidades inválidos")
    for campo in ("pesos_equipo", "pesos_rival"):
        matriz = np.array(modelo[campo])
        if matriz.shape != (2 * k + 2, 4) or not np.isfinite(matriz).all():
            raise ValueError("Pesos Euroliga incompatibles")
    cov = np.array(modelo["covarianza"])
    if cov.shape != (8, 8) or not np.isfinite(cov).all() or not np.allclose(cov, cov.T) or np.linalg.eigvalsh(cov).min() <= 0:
        raise ValueError("Covarianza Euroliga inválida")
    if set(entidades) != set(modelo["catalogo"]) or set(entidades) != set(modelo["muestras_equipo"]):
        raise ValueError("Catálogo/muestras incompletos")


def escribir_nuevo(ruta: Path, valor: dict) -> None:
    """Creación exclusiva y atómica; ningún lector ve JSON parcialmente escrito."""
    ruta.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    contenido = json_bytes(valor)
    fd, temporal = tempfile.mkstemp(prefix=".captura-", suffix=".tmp", dir=ruta.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(contenido)
            f.flush()
            os.fsync(f.fileno())
        # link publica completo y falla si otro escritor ya creó el destino.
        os.link(temporal, ruta)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)


def publicar(modelo: dict, destino: Path | None = None) -> Path:
    validar_modelo(modelo)
    destino = destino or ruta_activa()
    destino.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    versionada = destino.parent / "versiones" / (modelo["version"] + ".json")
    if not versionada.exists():
        escribir_nuevo(versionada, modelo)
    elif versionada.read_bytes() != json_bytes(modelo):
        raise ValueError("Versión existente con contenido distinto")
    fd, temporal = tempfile.mkstemp(prefix=".euro-", dir=destino.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(json_bytes(modelo))
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, destino)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)
    return destino


def cargar(ruta: Path | None = None) -> dict:
    origen = ruta or ruta_activa()
    if not origen.is_file():
        raise RuntimeError("No hay modelo Euroliga publicado; requiere entrenamiento explícito offline")
    modelo = json.loads(origen.read_text())
    validar_modelo(modelo)
    return modelo


def predecir(modelo: dict, local: str, visitante: str, mercado: str, linea: float,
             parciales: list[list[int]] | None = None) -> dict:
    if mercado not in MERCADOS or not math.isfinite(linea) or not 0 < linea <= 600:
        raise ValueError("Mercado/línea inválidos")
    local, visitante = normalizar_nombre(local), normalizar_nombre(visitante)
    if local == visitante:
        raise ValueError("Los equipos deben ser distintos")
    r = {"local": local, "visitante": visitante}
    if not _conocido(modelo, r):
        raise ValueError(f"Abstención: ambos equipos necesitan al menos {MIN_EQUIPO} finales Euroliga; no se usan equipos NBA")
    parciales = parciales or []
    if len(parciales) > 3 or any(len(q) != 2 or any(type(p) is not int or not 0 <= p <= 100 for p in q) for q in parciales):
        raise ValueError("Solo se aceptan cuartos completos consecutivos Q1–Q3, local/visitante enteros 0–100")
    mu = _medias(modelo, [r])[0]
    cov = np.array(modelo["covarianza"])
    if parciales:
        obs = [i for i in range(len(parciales))] + [i + 4 for i in range(len(parciales))]
        futuro = [i for i in range(8) if i not in obs]
        valores = np.array([q[0] for q in parciales] + [q[1] for q in parciales])
        cobs = cov[np.ix_(obs, obs)]
        cruz = cov[np.ix_(futuro, obs)]
        mu[futuro] += cruz @ np.linalg.solve(cobs, valores - mu[obs])
        condicionada = cov[np.ix_(futuro, futuro)] - cruz @ np.linalg.solve(cobs, cruz.T)
        mu[obs] = valores
        cov[:] = 0
        cov[np.ix_(futuro, futuro)] = condicionada
    if (mu < 0).any():
        raise ValueError("Abstención: estado fuera de soporte, proyección negativa")
    predicciones = {}
    for m in MERCADOS:
        indices = list(range(8)) if m == "COMPLETO" else [int(m[1]) - 1, int(m[1]) + 3]
        ih, ia = [i for i in indices if i < 4], [i for i in indices if i >= 4]
        media = float(mu[indices].sum())
        var = max(0., float(cov[np.ix_(indices, indices)].sum()))
        predicciones[m] = {"media_local": float(mu[ih].sum()), "media_visitante": float(mu[ia].sum()),
                           "media_total": media, "desviacion_total": math.sqrt(var),
                           "intervalo_predictivo_80_raw": [media - 1.2815515655 * math.sqrt(var), media + 1.2815515655 * math.sqrt(var)],
                           "observado": m != "COMPLETO" and int(m[1]) <= len(parciales)}
    elegida = predicciones[mercado]
    proba = probabilidades(elegida["media_total"], elegida["desviacion_total"] ** 2, linea)
    contraste = np.array([1.] * 4 + [-1.] * 4)
    sd_diff = math.sqrt(max(1e-9, float(contraste @ cov @ contraste)))
    p_local = _cdf(float(contraste @ mu) / sd_diff)
    n_local, n_visitante = (modelo["muestras_equipo"][k] for k in (local, visitante))
    n_temporada = {lado: modelo["muestras_equipo_temporada"].get(nombre, 0) for lado, nombre in (("local", local), ("visitante", visitante))}
    advertencias = ["Probabilidades RAW no calibradas. Eficacia NO CERTIFICADA.",
                    "Solo 40 minutos de regulación; no incluye prórroga ni equivale a un mercado con OT.",
                    "No incorpora lesiones, alineaciones ni información en vivo no suministrada."]
    if min(n_local, n_visitante) < 20:
        advertencias.append("Muestra pequeña: al menos un equipo tiene menos de 20 finales; incertidumbre adicional no cuantificada.")
    if min(n_temporada.values()) < 10:
        advertencias.append("Menos de 10 finales por equipo en la temporada reciente; el histórico no acredita la forma actual de la plantilla.")
    if parciales:
        advertencias.append(f"Condicionado al cierre de Q{len(parciales)}; no incorpora reloj ni marcador parcial del cuarto siguiente.")
    return {"dominio": DOMINIO, "modelo_version": modelo["version"], "dataset_sha256": modelo["dataset_sha256"],
            "fecha_analisis": datetime.now(timezone.utc).isoformat(), "corte_datos": modelo["fecha_max"],
            "fit_completed_at": modelo["fit_completed_at"], "certificacion": "NO_CERTIFICADO", "calibrador_id": None,
            "modo": "CIERRE_Q" + str(len(parciales)) if parciales else "PREPARTIDO",
            "equipo_local": modelo["catalogo"][local]["nombre"], "equipo_visitante": modelo["catalogo"][visitante]["nombre"],
            "mercado": mercado, "linea": linea, "incluye_ot": False, "parciales": parciales,
            "muestras": {"local": n_local, "visitante": n_visitante}, "muestras_temporada": n_temporada,
            "temporada_reciente": modelo["temporada_reciente"], "predicciones": predicciones,
            "probabilidades": proba, "ventaja_regulacion": {"local": p_local, "visitante": 1 - p_local,
              "definicion": "Aproximación continua de diferencia de puntos en regulación; no moneyline con OT."},
            "origen_dispersion": modelo["origen_dispersion"], "advertencias": advertencias,
            "politica": {"no_picks": True, "no_stakes": True, "no_recommendations": True}}
