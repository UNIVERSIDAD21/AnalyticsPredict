"""Consultas de publicaciones congeladas: sin ajuste, BD ni journal."""
from datetime import datetime, timezone
from uuid import uuid4

from motor import euroliga, wnba


def identidad(modelo, liga):
    ajuste = modelo if liga == "euroliga" else modelo["ajuste_final"]
    return {
        "modelo_version": modelo["version"],
        "ajuste_version": ajuste.get("version"),
        "dataset_hash": ajuste["dataset_sha256"],
        "publicacion_dataset_hash": modelo["dataset_sha256"],
        "corte_modelo": ajuste["fecha_max"],
        "modelo_generado_en": modelo.get("fit_completed_at") or modelo.get("publicado_utc"),
        "muestra_entrenamiento": ajuste.get("partidos_entrenamiento", ajuste.get("n")),
        "eficacia_certificada": False, "incluye_ot": False, "minutos_regulacion": 40,
        "alcance": "publicacion_completa" if liga == "euroliga" else "REG_publicacion_congelada",
    }


def equipos(modelo, liga):
    if liga == "euroliga":
        return sorted([{
            "clave": clave, "nombre": valor["nombre"], "id": str(valor["id"]),
            "muestra": modelo["muestras_equipo"].get(clave, 0),
            "disponible": modelo["muestras_equipo"].get(clave, 0) >= euroliga.MIN_EQUIPO,
        } for clave, valor in modelo["catalogo"].items()], key=lambda r: r["nombre"])
    ajuste = modelo["ajuste_final"]
    # Nombres del último registro embebido, nunca del catálogo SQL ni de otra liga.
    nombres = {r[lado + "_id"]: r[lado] for r in modelo["datos"] for lado in ("local", "visitante")}
    return sorted([{
        "clave": clave, "id": clave, "nombre": nombres.get(clave, clave),
        "muestra": ajuste["muestras"].get(clave, 0),
        "muestra_efectiva": ajuste["efectivos"].get(clave, 0),
        "disponible": wnba.conocido(ajuste, {"local_id": clave, "visitante_id": clave}),
    } for clave in ajuste["entidades"]], key=lambda r: r["nombre"])


def catalogo(modelo, liga):
    return {"equipos": equipos(modelo, liga), "metadata": identidad(modelo, liga)}


def consultar(modelo, liga, local, visitante, periodo, linea):
    mercado = "COMPLETO" if periodo == "TOTAL" else periodo
    catalogo_por_clave = {e["clave"]: e for e in equipos(modelo, liga)}
    if local not in catalogo_por_clave or visitante not in catalogo_por_clave:
        raise ValueError("Selecciona equipos presentes en esta publicación")
    a, b = catalogo_por_clave[local], catalogo_por_clave[visitante]
    # Los motores originales validan la muestra, la línea y las identidades.
    if liga == "euroliga":
        salida = euroliga.predecir(modelo, local, visitante, mercado, linea)
    else:
        salida = wnba.predecir(modelo["ajuste_final"], local, visitante, mercado, linea)
    prediccion = salida["predicciones"][mercado]
    probabilidades = salida["probabilidades"]
    advertencias = salida.get("advertencias", []) + [
        "Base RAW de 40 minutos de regulación, sin OT. No verifica fixture ni datos actuales.",
        "Se utiliza el ajuste ya publicado completo; no selecciona temporadas ni vuelve a entrenar.",
        "La evaluación de desarrollo no acredita eficacia del refit publicado. Sin calibración certificada.",
        "No consulta BD, lesiones ni forma reciente; no registra predicciones ni apuestas.",
    ]
    if liga == "wnba":
        advertencias.append("WNBA: solo el ajuste REG congelado. Su muestra y hash difieren del conjunto REG/POST embebido en la publicación.")
    return {
        "formato": "consulta-local-v2", "analisis_id": str(uuid4()), "liga": liga,
        "equipo_local": a["nombre"], "equipo_visitante": b["nombre"],
        "equipo_local_id": a["id"], "equipo_visitante_id": b["id"],
        "periodo": periodo, "linea": linea, "generado_en": datetime.now(timezone.utc).isoformat(),
        "modo": "BASE_LOCAL", "metadata": identidad(modelo, liga),
        "muestras": {"local": a["muestra"], "visitante": b["muestra"]},
        "distribucion": {"familia": "normal_discretizada", "media": prediccion["media_total"],
                         "desviacion": prediccion["desviacion_total"],
                         "origen": "artefacto_publicado", "probabilidad_tipo": "RAW"},
        "probabilidad_over": probabilidades["over"], "probabilidad_under": probabilidades["under"],
        "probabilidad_push": probabilidades["push"], "motivo_nd": None, "advertencias": advertencias,
    }
