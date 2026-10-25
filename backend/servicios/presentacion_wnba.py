"""Datos descriptivos WNBA para las vistas comunes; sin pesos de otras ligas."""
from statistics import mean

from motor.wnba import exigir


def historial_equipo(rows, tid, *, limite=5000, temporada=None, como_local=None, regulacion=False):
    propios = [r for r in rows if tid in (r["local_id"], r["visitante_id"])]
    exigir(bool(propios), "Equipo WNBA sin histórico elegible")
    nombre = next(r["local"] if r["local_id"] == tid else r["visitante"] for r in propios)
    temporadas = {r["temporada_id"]: r["temporada"] for r in propios}
    salida = []
    for r in reversed(propios):
        casa = r["local_id"] == tid
        if temporada and r["temporada_id"] != temporada:
            continue
        if como_local is not None and casa != como_local:
            continue
        def puntos(home):
            q = r["y"][:4] if home else r["y"][4:]
            lado = "local" if home else "visitante"
            return {**{f"q{i+1}": x for i, x in enumerate(q)}, "ot": r[lado+"_ot"],
                    "total": sum(q) if regulacion else r[lado+"_total"]}
        pf, pc = puntos(casa), puntos(not casa)
        salida.append({"id": r["id"], "fecha": r["fecha"], "temporada": r["temporada"],
                       "equipo_local": r["local"], "equipo_visitante": r["visitante"],
                       "local_abr": r["local"], "visitante_abr": r["visitante"],
                       "ubicacion_equipo": "LOCAL" if casa else "VISITANTE",
                       "puntos_equipo": pf, "puntos_rival": pc,
                       "resultado": "VICTORIA" if pf["total"] > pc["total"] else "EMPATE" if pf["total"] == pc["total"] else "DERROTA"})
    return {"exito": True, "equipo": {"id": tid, "nombre": nombre, "abreviatura": "WNBA"},
            "partidos": salida[:limite], "total_partidos": len(salida),
            "filtros_disponibles": {"temporadas": [{"id": k, "nombre": v} for k, v in sorted(temporadas.items(), key=lambda kv: kv[1])]},
            "convencion": "regulacion40" if regulacion else "final_con_ot"}


def estadisticas(rows, temporada=None):
    temporadas = {r["temporada_id"]: r["temporada"] for r in rows}
    seleccion = [r for r in rows if not temporada or r["temporada_id"] == temporada]
    exigir(bool(seleccion), "Temporada WNBA sin finales elegibles")
    umbrales = [mean(r["y"][i] + r["y"][i+4] for r in seleccion) for i in range(4)]
    umbral_total = mean(r["local_total"] + r["visitante_total"] for r in seleccion)
    equipos = []
    for tid in sorted({r[k] for r in seleccion for k in ("local_id", "visitante_id")}):
        hs = historial_equipo(seleccion, tid)["partidos"]
        def balance(ls):
            return {"victorias": sum(r["resultado"] == "VICTORIA" for r in ls),
                    "derrotas": sum(r["resultado"] == "DERROTA" for r in ls),
                    "ppg": mean(r["puntos_equipo"]["total"] for r in ls) if ls else None}
        def promedios(lado):
            return {k: mean(r[lado][k] for r in hs) for k in ("q1", "q2", "q3", "q4", "total")}
        record = balance(hs)
        nombre = hs[0]["equipo_local"] if hs[0]["ubicacion_equipo"] == "LOCAL" else hs[0]["equipo_visitante"]
        equipos.append({"nombre": nombre, "abreviatura": "WNBA", "conferencia": "N/D",
            "record": {k: record[k] for k in ("victorias", "derrotas")},
            "record_conferencia": {"victorias": None, "derrotas": None}, "posicion": None,
            "racha": ["W" if r["resultado"] == "VICTORIA" else "L" for r in hs[:5]],
            "promedios": {"anotados": promedios("puntos_equipo"), "recibidos": promedios("puntos_rival")},
            "local": balance([r for r in hs if r["ubicacion_equipo"] == "LOCAL"]),
            "visitante": balance([r for r in hs if r["ubicacion_equipo"] == "VISITANTE"]),
            "tendencias_over": {**{f"q{i+1}": mean(r["puntos_equipo"][f"q{i+1}"] + r["puntos_rival"][f"q{i+1}"] > umbrales[i] for r in hs) for i in range(4)},
                                "total": mean(r["puntos_equipo"]["total"] + r["puntos_rival"]["total"] > umbral_total for r in hs)},
            "linea_promedio": umbral_total})
    return {"exito": True, "equipos": equipos, "fecha_actualizacion": max(r["fecha"] for r in seleccion),
            "temporadas_disponibles": [{"id": k, "nombre": v} for k, v in sorted(temporadas.items(), key=lambda kv: kv[1])],
            "temporada_actual": temporada,
            "metodo": "Finales WNBA REG/POST válidos anteriores al día local; PPG final con OT. Over descriptivo frente a media de liga del alcance, no cuotas. Conferencia/posición N/D: no publicadas en el lote."}
