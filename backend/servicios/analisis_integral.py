"""Explicación de dominio sin I/O, entrenamiento ni dependencias del motor NBA.

Euroliga conserva la salida Ridge original y añade un escenario contextual RAW.
Fútbol explica el cálculo heurístico/ensemble que ya ejecuta su endpoint.
"""
from copy import deepcopy
from datetime import date
import math



def _numero(valor):
    return float(valor) if isinstance(valor, (int, float)) and math.isfinite(valor) else None


def _cdf(z):
    return (1 + math.erf(z / math.sqrt(2))) / 2


def _comparacion(base, ajustada, pb, pa):
    return {"media_base": base, "media_ajustada": ajustada,
            "probabilidades_base": pb, "probabilidades_ajustadas": pa}


def aplicar_escenario_euroliga(resultado, integral):
    """La respuesta primaria y la UI exponen el mismo escenario; base inmutable aparte."""
    resultado["salida_modelo_base"] = deepcopy({k: resultado[k] for k in ("predicciones", "probabilidades", "ventaja_regulacion")})
    resultado["analisis_integral"] = integral
    for fila in integral["periodos"]:
        p = resultado["predicciones"][fila["periodo"]]
        p.update(media_local=fila["local"], media_visitante=fila["visitante"], media_total=fila["total"])
        p["intervalo_predictivo_80_raw"] = [p["media_total"] + signo * 1.2815515655 * p["desviacion_total"] for signo in (-1, 1)]
    resultado["probabilidades"] = integral["probabilidades"]
    sd = resultado["ventaja_regulacion"].get("desviacion_diferencia")
    if sd and sd > 0:
        p = resultado["predicciones"]["COMPLETO"]
        local = _cdf((p["media_local"] - p["media_visitante"]) / sd)
        resultado["ventaja_regulacion"].update(local=local, visitante=1-local)
    return resultado


def integral_euroliga(r, *, lado="OVER", cuota_over=None, cuota_under=None, aplicar_contexto=True):
    """Heurística explícita y acotada: forma ofensiva/defensiva y días entre fechas.

    No estima bajas, viajes ni OT. El escenario no sustituye el artefacto Ridge.
    Los archivos históricos se enriquecen en memoria con aplicar_contexto=False.
    """
    from motor.euroliga import probabilidades

    base = r["predicciones"]
    proy = deepcopy(base)
    equipos = r.get("contexto", {}).get("equipos", {})
    buscar = lambda nombre: next((v for k, v in equipos.items() if k.casefold() == nombre.casefold()), {})
    locales = buscar(r["equipo_local"]).get("recientes", [])[:10]
    visitas = buscar(r["equipo_visitante"]).get("recientes", [])[:10]
    ajustes = []
    delta = [0., 0.]
    es_pre = r["modo"] == "PREPARTIDO"
    for i, (propios, rival, nombre) in enumerate(((locales, visitas, r["equipo_local"]), (visitas, locales, r["equipo_visitante"]))):
        campo = "media_local" if i == 0 else "media_visitante"
        if propios and rival and es_pre and aplicar_contexto:
            referencia = (sum(x["puntos_regulacion"] for x in propios) / len(propios)
                          + sum(x["puntos_rival_regulacion"] for x in rival) / len(rival)) / 2
            peso = .25 * min(len(propios), len(rival)) / (min(len(propios), len(rival)) + 20)
            cambio = max(-4., min(4., peso * (referencia - base["COMPLETO"][campo])))
            delta[i] += cambio
            ajustes.append({"factor": f"Forma reciente · {nombre}", "delta": cambio, "unidad": "puntos de regulación",
                            "descripcion": f"Media de ataque propio y defensa rival, últimos {len(propios)}/{len(rival)} finales; peso {peso:.4f}, tope ±4 puntos.", "aplicado": True})
        if propios and r.get("fecha_partido") and es_pre and aplicar_contexto:
            dias = (date.fromisoformat(r["fecha_partido"][:10]) - date.fromisoformat(propios[0]["fecha"][:10])).days
            cambio = -.75 if dias == 1 else -.35 if dias == 2 else 0.
            delta[i] += cambio
            ajustes.append({"factor": f"Descanso · {nombre}", "delta": cambio, "unidad": "puntos de regulación",
                            "descripcion": f"{dias} días entre fechas canónicas; −0,75 con 1 día, −0,35 con 2, 0 en otro caso. Sin hora de kickoff.", "aplicado": True})
    for periodo, p in proy.items():
        factor = 1 if periodo == "COMPLETO" else .25
        # Live y archivos anteriores mantienen exactamente su distribución original.
        p["media_local"] = max(0., p["media_local"] + delta[0] * factor)
        p["media_visitante"] = max(0., p["media_visitante"] + delta[1] * factor)
        p["media_total"] = p["media_local"] + p["media_visitante"]
    elegida = proy[r["mercado"]]
    pa = probabilidades(elegida["media_total"], elegida["desviacion_total"] ** 2, r["linea"])
    completo = proy["COMPLETO"]
    diferencia = completo["media_local"] - completo["media_visitante"]
    sd = _numero(r["ventaja_regulacion"].get("desviacion_diferencia"))
    if sd and sd > 0:
        local = 1 - _cdf((.5 - diferencia) / sd)
        visitante = _cdf((-.5 - diferencia) / sd)
        empate = max(0., 1 - local - visitante)
    else:
        # Archivo antiguo: no inventar sigma del margen a partir de sigma del total.
        local, visitante, empate = r["ventaja_regulacion"]["local"], r["ventaja_regulacion"]["visitante"], None
    razones = [f"Ridge Euroliga {r['modelo_version']}; datos hasta {r['corte_datos']}.",
               f"Muestras históricas local/visitante: {r['muestras']['local']}/{r['muestras']['visitante']}.",
               f"{r['mercado']}: base {base[r['mercado']]['media_total']:.2f}, escenario contextual {elegida['media_total']:.2f} puntos.",
               "Forma y descanso son ajustes heurísticos; peso fijo declarado, sigma del modelo sin recalibrar.",
               "Localía ya forma parte de Ridge; no se añade otra ventaja local. No se incorporan lesiones ni alineaciones."]
    if not ajustes:
        razones.append("Sin ajuste contextual adicional: corte condicionado, archivo anterior o historial insuficiente. Se conserva la salida original.")
    return {"version": "integral-v1", "deporte": "euroliga", "metodo": "Ridge + escenario contextual heurístico RAW",
            "unidad": "puntos", "mercado": r["mercado"], "linea": r["linea"], "lado": lado,
            "probabilidades": pa, "cuotas": {"over": cuota_over, "under": cuota_under},
            "ganador": {"local": local, "empate": empate, "visitante": visitante,
                        "marcador": f"{completo['media_local']:.1f} – {completo['media_visitante']:.1f}",
                        "definicion": "Ganador del partido en 40 minutos. Empate conduce a OT, cuyo ganador no se modela. Aproximación gaussiana discreta RAW; no moneyline con OT."},
            "periodos": [{"periodo": m, "local": p["media_local"], "visitante": p["media_visitante"],
                          "total": p["media_total"], "desviacion": p["desviacion_total"], "observado": p.get("observado", False)} for m, p in proy.items()],
            "comparacion": _comparacion(base[r["mercado"]]["media_total"], elegida["media_total"], r["probabilidades"], pa),
            "ajustes": ajustes, "razones": razones, "muestras": r["muestras"],
            "nota_periodos": "Cuartos de 10 min; 40 min sin OT. Ajuste de partido repartido por igual entre cuartos; proyección heurística, no observación."}


def integral_futbol(*, mercados, base, objetivo, ganador, goles_local, goles_visitante, trazas, cuotas, modelo_version):
    mercado, linea = objetivo.mercado, objetivo.linea
    arco = "ARCO" in mercado
    familia = "CORNERS" if mercado.startswith("CORNERS") else "GOLES" if mercado.startswith("GOLES") else "DISPAROS"
    total_familia = familia + ("_ARCO" if arco else "")
    periodos = []
    for periodo in ("1T", "2T", "FT"):
        obtener = lambda suf: mercados.get(f"{familia}{suf}_{periodo}", {})
        sufijo = "_ARCO" if arco else ""
        total = obtener(sufijo)
        periodos.append({"periodo": periodo, "local": _numero(obtener("_LOCAL" + sufijo).get("media")),
                         "visitante": _numero(obtener("_VISITANTE" + sufijo).get("media")),
                         "total": _numero(total.get("media")), "desviacion": _numero(total.get("std")), "observado": False})
    seleccionado = mercados.get(mercado, {})
    anterior = base.get(mercado, {})
    probas = lambda p: {"over": _numero(p.get("over_raw")), "under": _numero(p.get("under_raw")),
                       "push": max(0., 1 - p["over_raw"] - p["under_raw"]) if _numero(p.get("over_raw")) is not None and _numero(p.get("under_raw")) is not None else None}
    buscar_linea = lambda p: next((v for k, v in p.get("lineas", {}).items() if abs(float(k) - linea) < 1e-8), {})
    pb, pa = probas(buscar_linea(anterior)), probas(buscar_linea(seleccionado))
    if float(linea).is_integer():
        # El contrato legacy complementa Over con Under y no registra el push.
        # No declarar push=0 en una línea entera sin masa separada acreditada.
        for prob in (pb, pa):
            if prob["over"] is not None and prob["under"] is not None and abs(prob["over"] + prob["under"] - 1) < 1e-6:
                prob["push"] = None
    ajustes = deepcopy(trazas.get(mercado, []))
    media_base, media_final = _numero(anterior.get("media")), _numero(seleccionado.get("media"))
    if ajustes and media_base is not None:
        media_base -= sum(x["delta"] for x in ajustes)
        # Las trazas de forma/localía son aditivas en media; las probabilidades
        # previas a esos pasos no se conservaron y no se reconstruyen como exactas.
        pb = {"over": None, "under": None, "push": None}
    heuristica = _numero(anterior.get("media"))
    if heuristica is not None and media_final is not None and abs(media_final - heuristica) > 1e-9:
        ajustes.append({"factor": "Ensemble ML/heurístico", "delta": media_final - heuristica,
                        "unidad": objetivo.unidad, "descripcion": "Diferencia exacta entre mercado heurístico y salida del ensemble de esta corrida.", "aplicado": True})
    calidad = objetivo.calidad_datos
    muestras = calidad.muestras.model_dump()
    razones = list(ganador.get("razones", [])) + [
        f"Método {modelo_version}; mercado {mercado}, línea {linea:g}.",
        f"Proyección objetivo: {media_final:.2f} {objetivo.unidad}." if media_final is not None else "Mercado sin media estimable en esta corrida.",
        f"Muestras: H2H {muestras['h2h']}, local en casa {muestras['local_home']}, visitante fuera {muestras['visitante_away']}.",
        "Sede, temporadas y recencia se ponderan en el estimador; no se imputan lesiones, alineaciones ni clima.",
    ]
    if float(linea).is_integer() and pa["push"] is None:
        razones.append("Línea entera: el motor legacy no separa push; el retorno/EV se mantiene no evaluable hasta disponer de esa masa, en vez de tratar empate como fallo.")
    razones.extend(f"Calidad: {x}" for x in calidad.penalizaciones_aplicadas)
    q = {}
    for clave, valores in (cuotas or {}).items():
        codigo, separador, umbral = clave.partition('|')
        try:
            coincide = separador and codigo == mercado and abs(float(umbral) - linea) < 1e-8
        except ValueError:
            coincide = False
        if coincide:
            q = valores
            break
    return {"version": "integral-v1", "deporte": "futbol", "metodo": modelo_version + " · estimación exploratoria RAW",
            "unidad": objetivo.unidad, "mercado": mercado, "linea": linea, "lado": objetivo.lado,
            "probabilidades": pa, "cuotas": {"over": q.get("cuota_over"), "under": q.get("cuota_under")},
            "ganador": {"local": ganador["prob_local"], "empate": ganador["prob_empate"], "visitante": ganador["prob_visitante"],
                        "marcador": f"{goles_local:.2f} – {goles_visitante:.2f}",
                        "definicion": "1X2 por goles a 90 minutos más añadido, sin prórroga ni penales. Dixon-Coles/ensemble RAW; independiente del mercado de córners o disparos seleccionado."},
            "periodos": periodos, "comparacion": _comparacion(media_base, media_final, pb, pa),
            "ajustes": ajustes, "razones": razones, "muestras": muestras,
            "nota_periodos": f"Proyecciones de {total_familia}: 1T, 2T y FT. Estimadores por periodo independientes; FT puede diferir de la suma. Los splits de disparos se estiman con el método temporal del motor, no son observaciones."}
