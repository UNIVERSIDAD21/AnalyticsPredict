"""Ingesta local, verificable y sin HTTP de exportaciones MLS/LATAM.

El plan y su revisión son de solo lectura. Aplicar exige una transacción externa:
no confirma, no borra y no entrena. Identidad ESPN exacta, nunca fuzzy matching.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

VERSION = "futbol-americas-local-v1"
ZONA = ZoneInfo("America/Bogota")
PAISES = {
    "USA": ("Estados Unidos", "United States", "America/New_York"),
    "CAN": ("Canadá", "Canada", "America/Toronto"),
    "ARG": ("Argentina", "Argentina", "America/Argentina/Buenos_Aires"),
    "COL": ("Colombia", "Colombia", "America/Bogota"),
    "BRA": ("Brasil", "Brazil", "America/Sao_Paulo"),
}
# Feed y competición no son sinónimos: algunos feeds contienen otra copa.
COMPETICIONES = {
    "USA_MLS": ("MLS", "USA", "LIGA", "usa.1"),
    "USA_MLS_BACK": ("MLS is Back — eliminatorias 2020", "USA", "COPA_NACIONAL", "usa.1"),
    "ARG_PRIMERA": ("Primera División Argentina", "ARG", "LIGA", "arg.1"),
    "ARG_MARADONA": ("Copa Diego Armando Maradona", "ARG", "COPA_NACIONAL", "arg.1"),
    "ARG_COPA_LPF": ("Copa de la Liga Profesional", "ARG", "COPA_NACIONAL", "arg.copa_lpf"),
    "ARG_SUPERLIGA": ("Copa de la Superliga", "ARG", "COPA_NACIONAL", "arg.copa_de_la_superliga"),
    "COL_PRIMERAA": ("Categoría Primera A", "COL", "LIGA", "col.1"),
    "BRA_SERIEA": ("Brasileirão Série A", "BRA", "LIGA", "bra.1"),
}
POR_FEED = {"usa.1": "USA_MLS", "arg.1": "ARG_PRIMERA", "arg.copa_lpf": "ARG_COPA_LPF",
            "arg.copa_de_la_superliga": "ARG_SUPERLIGA", "col.1": "COL_PRIMERAA", "bra.1": "BRA_SERIEA"}
NUMERICOS = ("goles", "goles_1t", "goles_2t", "goles_90", "goles_et", "penales", "corners",
             "tiros_al_arco", "tiros_totales", "amarillas", "rojas", "faltas", "atajes")
ESTADISTICAS = ("corners", "tiros_al_arco", "tiros_totales")
MAPA_CAMPOS = {"goles": "goles_total", "goles_1t": "goles_1t", "goles_2t": "goles_2t",
               "goles_et": "goles_et", "penales": "penales", "corners": "corners_total",
               "tiros_al_arco": "disparos_arco", "tiros_totales": "disparos_total",
               "amarillas": "tarjetas_amarillas", "rojas": "tarjetas_rojas", "faltas": "faltas"}


def uid(clave):
    return str(uuid5(NAMESPACE_URL, f"analyticspredict:{clave}"))


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def instante(texto):
    dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Fecha sin zona horaria")
    return dt.astimezone(timezone.utc)


def competicion_fila(row):
    feed, fase = row["codigo_liga"], row["fase_fuente"].lower()
    if feed not in POR_FEED:
        raise ValueError("Feed no autorizado")
    if "all-star" in fase:
        return None
    if feed == "arg.1" and "copa-diego-armando-maradona" in fase:
        return "ARG_MARADONA"
    if feed == "usa.1" and fase.startswith("mls-is-back---"):
        return "USA_MLS_BACK"
    return POR_FEED[feed]


def temporada_fila(row, codigo):
    anio = row["temporada"]
    if type(anio) is not int or not 1900 <= anio <= 2100:
        raise ValueError("Temporada fuente inválida")
    # No se deduce la temporada del kickoff: Brasil 2020 se jugó también en 2021.
    text = (row.get("temporada_nombre_fuente") or "") + " " + row["fase_fuente"]
    cruzada = codigo in {"ARG_PRIMERA", "ARG_MARADONA"} and bool(
        re.search(rf"{anio}[-–](?:{anio + 1}|{str(anio + 1)[2:]})\b", text))
    fin = anio + int(cruzada)
    return (f"{anio}-{fin}" if cruzada else str(anio), anio, fin)


def validar_fila(row):
    if row.get("contrato") not in {"espn_mls_v1", "espn_latam_v1"} or row.get("fuente") != "ESPN":
        raise ValueError("Contrato/proveedor desconocido")
    for campo in ("source_game_id", "local_id_fuente", "visitante_id_fuente"):
        if not isinstance(row.get(campo), str) or not row[campo].isdigit():
            raise ValueError(f"Identidad inválida: {campo}")
    if row["local_id_fuente"] == row["visitante_id_fuente"]:
        raise ValueError("Mismo equipo en ambos lados")
    if not row.get("local_nombre") or not row.get("visitante_nombre"):
        raise ValueError("Nombre ausente")
    if not isinstance(row.get("fase_fuente"), str) or not row["fase_fuente"] or not str(row.get("season_type_fuente", "")).isdigit():
        raise ValueError("Fase fuente ausente o inválida")
    instante(row["inicio_utc"])
    if instante(row["inicio_colombia"]) != instante(row["inicio_utc"]):
        raise ValueError("Fechas UTC/Colombia no concilian")
    codigo = competicion_fila(row)
    temporada_fila(row, codigo)
    for lado in ("local", "visitante"):
        for campo in NUMERICOS:
            v = row.get(f"{lado}_{campo}")
            if v is not None and (type(v) is not int or v < 0):
                raise ValueError(f"Valor inválido: {lado}_{campo}")
        tiros, arco = row.get(lado + "_tiros_totales"), row.get(lado + "_tiros_al_arco")
        if tiros is not None and arco is not None and arco > tiros:
            raise ValueError("Tiros al arco mayores que tiros totales")
    final = row.get("final_completo")
    if type(final) is not bool or final != (row["estado"] == "FINALIZADO"):
        raise ValueError("Estado/final contradictorios")
    suficientes = bool(final and all(row.get(l + "_" + f) is not None
                                      for l in ("local", "visitante") for f in ESTADISTICAS))
    if type(row.get("estadisticas_completas")) is not bool or row["estadisticas_completas"] != suficientes:
        raise ValueError("Bandera de estadísticas completas no concilia con los seis campos requeridos")
    if final:
        for lado in ("local", "visitante"):
            ft, reg, et = (row.get(f"{lado}_goles{s}") for s in ("", "_90", "_et"))
            if ft is None:
                raise ValueError("Final sin marcador")
            if reg is not None and et is not None and reg + et != ft:
                raise ValueError("Regulación + ET no concilia")
            a, b = row.get(lado + "_goles_1t"), row.get(lado + "_goles_2t")
            if a is not None and b is not None and reg is not None and a + b != reg:
                raise ValueError("Mitades no concilian")
        if row.get("hubo_penales") is True:
            a, b = row.get("local_penales"), row.get("visitante_penales")
            if a is None or b is None or a == b:
                raise ValueError("Tanda sin ganador acreditado")
    elif any(row.get(f"{l}_{f}") is not None for l in ("local", "visitante") for f in NUMERICOS):
        raise ValueError("No final con resultado/estadística; no importar como fixture")
    return codigo


def _celda(v):
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + v
    return str(v)


def cargar_lote(reporte):
    """Verifica manifiesto, CSV completos contra JSONL y censo íntegro del lote."""
    path = Path(reporte).resolve()
    report = json.loads(path.read_bytes())
    if report["estado"] in {"EN_CURSO", "INTERRUMPIDO", "ERROR_INTERNO"}:
        raise ValueError("No ingerir ejecución mutable/interrumpida")
    hashes = report.get("sha256_archivos", {})
    if not {"partidos.csv", "partidos_finales.csv", "partidos_completos.csv", "partidos.jsonl"} <= hashes.keys():
        raise ValueError("Manifiesto de entrada incompleto")
    for nombre, esperado in hashes.items():
        if Path(nombre).name != nombre or sha(path.parent / nombre) != esperado:
            raise ValueError(f"Archivo alterado: {nombre}")
    rows = [json.loads(x) for x in (path.parent / "partidos.jsonl").read_text().splitlines()]
    if len(rows) != report["partidos_exportados"]:
        raise ValueError("Conteo exportado no concilia")
    counts = Counter((r["codigo_liga"], r["source_game_id"]) for r in rows)
    if any(n > 1 for n in counts.values()):
        raise ValueError("IDs duplicados en el lote")
    por_id = {(r["codigo_liga"], r["source_game_id"]): r for r in rows}
    for nombre, predicado in [("partidos.csv", lambda r: True), ("partidos_finales.csv", lambda r: r["final_completo"]),
                               ("partidos_completos.csv", lambda r: r["estadisticas_completas"])]:
        with (path.parent / nombre).open(newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ValueError("Encabezados CSV ambiguos")
            if rows and set(reader.fieldnames) != set(rows[0]):
                raise ValueError("Encabezados CSV no concilian con el contrato JSONL")
            vistos = set()
            for item in reader:
                key = (item["codigo_liga"], item["source_game_id"])
                row = por_id.get(key)
                if row is None or key in vistos or not predicado(row):
                    raise ValueError("CSV no concilia con exportación JSONL")
                vistos.add(key)
                if any(v != _celda(row.get(k)) for k, v in item.items()):
                    raise ValueError(f"Campo CSV contradictorio: {key}")
            if len(vistos) != sum(bool(predicado(r)) for r in rows):
                raise ValueError("Subconjunto CSV incompleto")
    if sum(r["final_completo"] for r in rows) != report["finales_completos"]:
        raise ValueError("Censo de finales contradictorio")
    if sum(r["estadisticas_completas"] for r in rows) != report["finales_con_estadisticas_completas"]:
        raise ValueError("Censo estadístico contradictorio")
    return {"reporte": str(path), "sha256": sha(path), "resumen": report, "filas": rows}


def preparar(lotes, *, desde_fixtures, hasta_fixtures):
    filas, apartados, vistos = [], [], {}
    grupos = defaultdict(Counter)
    for lote in lotes:
        for row in lote["filas"]:
            key = (row["codigo_liga"], row["source_game_id"])
            if key in vistos:
                if digest(row) != vistos[key]:
                    raise ValueError(f"Versiones contradictorias entre lotes: {key}")
                grupos[(row["codigo_liga"], str(row["temporada"]))]["duplicados_identicos"] += 1
                continue
            vistos[key] = digest(row)
            g = grupos[(row["codigo_liga"], str(row["temporada"]))]
            g["exportados"] += 1
            try:
                codigo = validar_fila(row)
                dt = instante(row["inicio_utc"])
                final = row["final_completo"]
                if codigo is None:
                    motivo = "ALL_STAR_FUERA_DE_COMPETICION"
                elif final:
                    motivo = None
                elif row["estado"] == "PROGRAMADO" and desde_fixtures <= dt < hasta_fixtures:
                    motivo = None
                else:
                    motivo = "NO_FINAL_FUERA_DE_VENTANA_O_NO_PROGRAMADO"
                if motivo:
                    apartados.append({"clave": key, "motivo": motivo, "fila": row})
                    g["apartados"] += 1
                    continue
                if final and dt >= desde_fixtures:
                    # Descargas históricas cortadas antes del día de integración.
                    # Los resultados nuevos requieren la evidencia final, no reloj asumido.
                    if dt > datetime.now(timezone.utc):
                        raise ValueError("Final fechado en el futuro")
                g["finales_validos" if final else "fixtures"] += 1
                g["estadisticas_suficientes"] += bool(final and row["estadisticas_completas"])
                g["parciales_estadisticos"] += bool(final and not row["estadisticas_completas"])
                filas.append({"codigo": codigo, "temporada": temporada_fila(row, codigo),
                              "row": row, "sha256": digest(row), "lote_sha256": lote["sha256"]})
            except (ValueError, KeyError, TypeError) as exc:
                apartados.append({"clave": key, "motivo": str(exc), "fila": row})
                g["invalidos"] += 1
    naturales = Counter((x["codigo"], x["row"]["local_id_fuente"], x["row"]["visitante_id_fuente"],
                         instante(x["row"]["inicio_utc"]).astimezone(ZONA).date()) for x in filas)
    por_evento = defaultdict(set)
    for x in filas:
        por_evento[x["row"]["source_game_id"]].add(x["row"]["codigo_liga"])
    aceptadas = []
    for x in filas:
        r = x["row"]
        natural = (x["codigo"], r["local_id_fuente"], r["visitante_id_fuente"], instante(r["inicio_utc"]).astimezone(ZONA).date())
        if naturales[natural] > 1 or len(por_evento[r["source_game_id"]]) > 1:
            apartados.append({"clave": (r["codigo_liga"], r["source_game_id"]),
                               "motivo": "IDENTIDAD_DUPLICADA_ENTRE_EVENTOS_O_FEEDS", "fila": r})
            g = grupos[(r["codigo_liga"], str(r["temporada"]))]
            g["apartados"] += 1
            g["finales_validos" if r["final_completo"] else "fixtures"] -= 1
            g["estadisticas_suficientes"] -= bool(r["final_completo"] and r["estadisticas_completas"])
            g["parciales_estadisticos"] -= bool(r["final_completo"] and not r["estadisticas_completas"])
        else:
            aceptadas.append(x)
    return {"version": VERSION, "filas": aceptadas, "apartados": apartados,
            "conteos": [{"feed": k[0], "temporada_fuente": k[1], **v} for k, v in sorted(grupos.items())],
            "lotes": [{"reporte": l["reporte"], "sha256": l["sha256"]} for l in lotes]}


def planificar(conn, plan):
    """Identidades y diferencias exactas; no ejecuta DDL/DML."""
    with conn.cursor(row_factory=dict_row) as c:
        comps = {r["codigo"]: r for r in c.execute("SELECT * FROM competiciones_futbol")}
        paises = {r["codigo_iso"]: r for r in c.execute("SELECT * FROM paises")}
        clubs = {str(r["id"]): r for r in c.execute("SELECT * FROM equipos_futbol")}
        links = {r["id_fuente"]: str(r["equipo_id"]) for r in c.execute("SELECT * FROM equipos_fuente_espn_futbol")}
        seasons = {(str(r["competicion_id"]), r["nombre"]): r for r in c.execute("SELECT * FROM temporadas_futbol")}
        matches = {(r["liga"], r["id_fuente"]): r for r in c.execute("SELECT * FROM partidos_fuente_espn_futbol")}
        partidos = {str(r["id"]): r for r in c.execute("SELECT * FROM partidos_futbol")}
        por_pareja = defaultdict(list)
        for p in partidos.values():
            por_pareja[(str(p["competicion_id"]), str(p["equipo_local_id"]), str(p["equipo_visitante_id"]))].append(p)
        teams = {}
        for item in plan["filas"]:
            row, codigo = item["row"], item["codigo"]
            for lado in ("local", "visitante"):
                ident, nombre = row[lado + "_id_fuente"], row[lado + "_nombre"]
                canonical = links.get(ident, uid("espn:soccer:team:" + ident))
                if ident not in teams:
                    # Nombres iguales en el país requieren revisión, nunca una unión automática.
                    iso = COMPETICIONES[codigo][1]
                    if row["codigo_liga"] == "usa.1":
                        # IDs observados en las exportaciones; no fuzzy matching.
                        iso = "CAN" if ident in {"7318", "9727", "9720"} else "USA"
                    pais_id = str(paises[iso]["id"]) if iso in paises else uid("pais:" + iso)
                    if ident not in links and any(x["nombre"].casefold() == nombre.casefold()
                                                  and str(x["pais_id"]) == pais_id for x in clubs.values()):
                        raise ValueError(f"Club sin enlace con nombre coincidente: {ident}/{nombre}")
                    teams[ident] = {"id": canonical, "nombre": nombre, "pais_id": pais_id,
                                    "iso": iso, "codigo": POR_FEED[row["codigo_liga"]], "nombres_fuente": set()}
                teams[ident]["nombres_fuente"].add(nombre)
        comp_ids = {k: str(comps[k]["id"]) if k in comps else uid("competicion:" + k) for k in {x["codigo"] for x in plan["filas"]}}
        season_ids = {}
        for item in plan["filas"]:
            key = (comp_ids[item["codigo"]], item["temporada"][0])
            season_ids[key] = str(seasons[key]["id"]) if key in seasons else uid("temporada:" + ":".join(key))
        acciones = []
        for item in plan["filas"]:
            row = item["row"]
            key = (row["codigo_liga"], row["source_game_id"])
            comp_id = comp_ids[item["codigo"]]
            local, visitante = teams[row["local_id_fuente"]]["id"], teams[row["visitante_id_fuente"]]["id"]
            link = matches.get(key)
            pid = str(link["partido_id"]) if link else str(uuid5(NAMESPACE_URL, f"espn:soccer:{key[0]}:{key[1]}"))
            anterior = partidos.get(pid)
            if link:
                if not anterior or (str(anterior["competicion_id"]), str(anterior["equipo_local_id"]), str(anterior["equipo_visitante_id"])) != (comp_id, local, visitante):
                    raise ValueError(f"Identidad canónica contradictoria: {key}")
                if link["sha256_evento"].strip() == item["sha256"]:
                    accion = "EXISTENTE"
                else:
                    # Un lote posterior no autoriza reemplazar finales ni perder estadísticas.
                    if anterior["estado"] == "FINALIZADO":
                        raise ValueError(f"Final existente requiere conciliación explícita: {key}")
                    accion = "ACTUALIZAR_FIXTURE"
            else:
                if anterior:
                    raise ValueError(f"UUID ocupado sin enlace: {key}")
                dt = instante(row["inicio_utc"])
                if any(abs((p["fecha_partido"] - dt).total_seconds()) <= 172800
                       for p in por_pareja[(comp_id, local, visitante)]):
                    raise ValueError(f"Posible duplicado sin enlace: {key}")
                accion = "INSERTAR"
            acciones.append({**item, "id": pid, "competicion_id": comp_id, "local_id": local,
                             "visitante_id": visitante, "temporada_id": season_ids[(comp_id, item["temporada"][0])],
                             "accion": accion, "huella_antes": digest(anterior) if anterior else None})
        for e in teams.values():
            e["nombres_fuente"] = sorted(e["nombres_fuente"])
        return {**plan, "codigo_sha256": sha(__file__), "acciones": acciones, "equipos": teams, "competiciones": comp_ids,
                "temporadas": {"|".join(k): v for k,v in season_ids.items()},
                "resumen_acciones": dict(Counter(a["accion"] for a in acciones))}


def aplicar(conn, plan):
    """Aplica el plan bajo lock, revalida antes-imágenes; el caller confirma o revierte."""
    with conn.cursor(row_factory=dict_row) as c:
        if plan["version"] != VERSION or plan["codigo_sha256"] != sha(__file__) or any(digest(a["row"]) != a["sha256"] for a in plan["acciones"]):
            raise ValueError("Plan o fuente alterados")
        c.execute("SELECT pg_advisory_xact_lock(hashtext('analyticspredict_espn_futbol_canonico'))")
        sin_cambios = all(a["accion"] == "EXISTENTE" for a in plan["acciones"])
        previos = {str(r["id"]): r for r in c.execute("SELECT * FROM partidos_futbol WHERE id=ANY(%s::uuid[])" + ("" if sin_cambios else " FOR UPDATE"),
                                                     ([a["id"] for a in plan["acciones"]],))}
        for a in plan["acciones"]:
            previo = previos.get(a["id"])
            if (digest(previo) if previo else None) != a["huella_antes"]:
                raise ValueError("Antes-imagen cambió; volver a planificar")
        if sin_cambios:
            return {"insertados": 0, "actualizados": 0, "existentes": len(plan["acciones"])}
        # Catálogo acotado, no actualiza filas ajenas existentes.
        for iso in {e["iso"] for e in plan["equipos"].values()} | {COMPETICIONES[k][1] for k in plan["competiciones"]}:
            nombre, ingles, zona = PAISES[iso]
            c.execute("INSERT INTO paises(id,codigo_iso,nombre,nombre_ingles,zona_horaria) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(codigo_iso) DO NOTHING",
                      (uid("pais:" + iso), iso, nombre, ingles, zona))
        paises = {r["codigo_iso"]: r["id"] for r in c.execute("SELECT id,codigo_iso FROM paises")}
        for codigo, cid in plan["competiciones"].items():
            nombre, iso, tipo, _ = COMPETICIONES[codigo]
            c.execute("INSERT INTO competiciones_futbol(id,codigo,nombre,nombre_corto,pais_id,tipo,prioridad) VALUES(%s,%s,%s,%s,%s,%s,110) ON CONFLICT(codigo) DO NOTHING",
                      (cid, codigo, nombre, nombre[:50], paises[iso], tipo))
        temporadas = {}
        for a in plan["acciones"]:
            temporadas[a["temporada_id"]] = a
        for tid, a in temporadas.items():
            nombre, inicio, fin = a["temporada"]
            c.execute("INSERT INTO temporadas_futbol(id,competicion_id,nombre,anio_inicio,anio_fin,activa,finalizada) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                      (tid, a["competicion_id"], nombre, inicio, fin, fin >= 2026, fin < 2026))
            # La clave existente admite un único feed/año: copas embebidas se
            # acreditan en evidencia del evento, no se fuerza un vínculo falso.
            if a["codigo"] not in {"ARG_MARADONA", "USA_MLS_BACK"}:
                c.execute("INSERT INTO temporadas_fuente_espn_futbol(liga,anio,temporada_id,evidencia) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                          (a["row"]["codigo_liga"], inicio, tid, Jsonb({"contrato": VERSION, "nombre": nombre})))
        for source_id, e in plan["equipos"].items():
            cid = plan["competiciones"].get(e["codigo"])
            c.execute("INSERT INTO equipos_futbol(id,nombre,nombre_corto,pais_id,competicion_principal_id) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                      (e["id"], e["nombre"], e["nombre"][:50], paises[e["iso"]], cid))
            c.execute("INSERT INTO equipos_fuente_espn_futbol(id_fuente,equipo_id,evidencia) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                      (source_id, e["id"], Jsonb({"contrato": VERSION, "nombres_fuente": sorted(e["nombres_fuente"]), "metodo": "ID_ESPN_EXACTO"})))
        counts = Counter()
        # Pipelining reduce latencia; los errores revierten toda la transacción.
        with conn.pipeline():
            for a in plan["acciones"]:
                if a["accion"] == "EXISTENTE":
                    counts["existentes"] += 1
                    continue
                row = a["row"]
                final = row["final_completo"]
                fecha_local = instante(row["inicio_utc"]).astimezone(ZONA)
                ronda = row["fase_fuente"]
                if len(ronda) > 50:
                    # No ensanchar un contrato ajeno ni cortar el sufijo que
                    # distingue final/semifinal. El texto completo queda en JSONB.
                    ronda = f"{row['fase']} · ESPN:{row['season_type_fuente']}"
                vals = {"id": a["id"], "competicion_id": a["competicion_id"], "temporada_id": a["temporada_id"],
                        "equipo_local_id": a["local_id"], "equipo_visitante_id": a["visitante_id"],
                        "fecha_partido": instante(row["inicio_utc"]), "fecha_partido_local": fecha_local.date(),
                        "hora_local": fecha_local.time().replace(tzinfo=None), "estado": row["estado"],
                        "ronda": ronda, "fuente_datos": "ESPN_SOCCER", "url_referencia": row["url_fuente"],
                        "hubo_tiempo_extra": row.get("hubo_prorroga"), "hubo_penales": row.get("hubo_penales"),
                        # Respetar trigger legacy: datos_completos acredita FT de
                        # goles; corners completos exige las cuatro mitades.
                        # La cobertura útil se mide por campos/elegibilidad.
                        "valido": True, "datos_completos": final, "datos_corners_completos": False,
                        "datos_disparos_completos": final and all(row.get(l + "_" + f) is not None for l in ("local", "visitante") for f in ("tiros_totales", "tiros_al_arco"))}
                for lado in ("local", "visitante"):
                    for fuente, destino in MAPA_CAMPOS.items():
                        vals[lado + "_" + destino] = row.get(lado + "_" + fuente) if final else None
                gl, gv = row.get("local_goles"), row.get("visitante_goles")
                vals.update(ganador_id=(a["local_id"] if gl > gv else a["visitante_id"] if gv > gl else None) if final else None,
                            diferencia_goles=abs(gl - gv) if final else None, resultado_final=f"{gl}-{gv}" if final else None)
                if a["accion"] == "INSERTAR":
                    c.execute("INSERT INTO partidos_futbol(" + ",".join(vals) + ") VALUES(" + ",".join(["%s"] * len(vals)) + ")", list(vals.values()))
                    counts["insertados"] += 1
                else:
                    campos = {k: v for k, v in vals.items() if k != "id"}
                    c.execute("UPDATE partidos_futbol SET " + ",".join(k + "=%s" for k in campos) + ",actualizado_en=now() WHERE id=%s", [*campos.values(), a["id"]])
                    counts["actualizados"] += 1
                observado = max(instante(x["observado_utc"]) for x in row["evidencia"])
                c.execute("INSERT INTO partidos_fuente_espn_futbol(liga,id_fuente,partido_id,sha256_evento,observado_en,evidencia) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(liga,id_fuente) DO UPDATE SET sha256_evento=EXCLUDED.sha256_evento,observado_en=EXCLUDED.observado_en,evidencia=EXCLUDED.evidencia",
                          (row["codigo_liga"], row["source_game_id"], a["id"], a["sha256"], observado,
                           Jsonb({"contrato_ingesta": VERSION, "codigo_canonico": a["codigo"], "lote_sha256": a["lote_sha256"], "original": row})))
        return dict(counts)
