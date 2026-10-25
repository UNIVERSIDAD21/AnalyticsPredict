"""Catálogo WNBA READ ONLY; artefacto y journal locales independientes."""

from datetime import date, datetime, timezone
from functools import lru_cache
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from psycopg.rows import dict_row
from motor.wnba import (
    FORMATO,
    MIN_EQUIPO,
    BOGOTA,
    ajustar_alcance,
    alcance,
    evaluar_congelado,
    exigir,
    huella,
    normalizar,
    predecir,
)
from servicios.predictor_euroliga import (
    conexion_lectura,
)  # Solo infraestructura SQL READ ONLY.


def ruta_activa():
    return Path(
        os.getenv(
            "ANALYTICSPREDICT_MODELO_WNBA_ACTIVO",
            str(Path.home() / ".local/share/analyticspredict/wnba/activo.json"),
        )
    )


def leer_datos(pool=None):
    with conexion_lectura(pool) as c, c.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT f.*,e.nombre local,v.nombre visitante,t.nombre temporada_nombre,
          c.codigo competicion_codigo,p.valido,p.tipo_partido,
          p.local_q1,p.local_q2,p.local_q3,p.local_q4,p.local_ot,p.local_total,
          p.visitante_q1,p.visitante_q2,p.visitante_q3,p.visitante_q4,p.visitante_ot,p.visitante_total
          FROM partidos_fuente_wnba f JOIN competiciones_baloncesto c ON c.id=f.competicion_id
          JOIN temporadas_baloncesto t ON t.id=f.temporada_id AND t.competicion_id=c.id
          JOIN equipos e ON e.id=f.equipo_local_id AND e.competicion_principal_id=c.id
          JOIN equipos v ON v.id=f.equipo_visitante_id AND v.competicion_principal_id=c.id
          LEFT JOIN partidos_baloncesto p ON p.id=f.partido_id AND p.competicion_id=c.id
          WHERE c.codigo='wnba' ORDER BY f.inicio_utc,f.source_game_id"""
        )
        return json.loads(json.dumps(cur.fetchall(), default=str))


def escribir(path, value, reemplazar=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(prefix=".wnba-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(value, f, ensure_ascii=False, sort_keys=True, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        if reemplazar:
            os.replace(tmp, path)
        else:
            os.link(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def identidad_modelo(m):
    return (
        "wnba-v1-"
        + huella({k: v for k, v in m.items() if k not in ("version", "publicado_utc")})[
            :24
        ]
    )


def construir(filas, corte):
    exigir(
        date.fromisoformat(corte) <= datetime.now(BOGOTA).date(),
        "Corte de publicación futuro no soportado",
    )
    datos = [r for r in normalizar(filas) if r["fecha"] < corte]
    evaluation = evaluar_congelado(datos)
    regular = [r for r in datos if r["fase"] == "REG"]
    refit = ajustar_alcance(regular)
    m = {
        "formato": FORMATO,
        "dominio": "wnba",
        "incluye_ot": False,
        "duracion_regulacion": 40,
        "datos": datos,
        "dataset_sha256": huella(datos),
        "corte_publicacion_exclusivo": corte,
        "politica": {
            "fases_base": ["REG"],
            "playoffs": "POST optativo, ajuste independiente sin validación específica",
            "copa": "excluida; no duplicar REG",
            "pretemporada": "excluida, incluidos invitados",
            "min_partidos_equipo": MIN_EQUIPO,
            "min_efectivos": 6,
            "min_partidos_modelo": 120,
            "recencia": "Uniforme/365/730 seleccionada solo con el pasado del alcance solicitado",
            "corte": "día local exclusivo America/Bogota; no se conoce hora de publicación FT",
            "calibracion": "SIN_CALIBRAR",
            "live": "NO_SOPORTADO",
        },
        "ajuste_final": refit,
        "validacion": evaluation,
        "limite_validacion": "EVAL corresponde al candidato guardado, no al refit final ni a otros alcances.",
        "publicado_utc": datetime.now(timezone.utc).isoformat(),
    }
    m["version"] = identidad_modelo(m)
    return m


def publicar(m, destino=None):
    exigir(
        m.get("formato") == FORMATO
        and m.get("dominio") == "wnba"
        and m["version"] == identidad_modelo(m),
        "Artefacto WNBA incompatible",
    )
    dest = Path(destino) if destino else ruta_activa()
    versionada = dest.parent / "versiones" / (m["version"] + ".json")
    if not versionada.exists():
        escribir(versionada, m)
    escribir(dest, m, reemplazar=True)
    return dest


def cargar():
    path = ruta_activa()
    if not path.is_file():
        raise RuntimeError(
            "Modelo WNBA no publicado. Ejecutar gestionar_predictor_wnba.py; no se utiliza NBA/Euroliga."
        )
    m = json.loads(path.read_text())
    exigir(
        m.get("formato") == FORMATO
        and m.get("dominio") == "wnba"
        and m.get("incluye_ot") is False
        and m.get("version") == identidad_modelo(m)
        and m.get("dataset_sha256") == huella(m["datos"]),
        "Modelo WNBA dañado o incompatible",
    )
    return m


def cargar_publicacion(version):
    import re
    actual=cargar()
    if version==actual['version']:
        return actual
    exigir(bool(re.fullmatch(r'wnba-v1-[0-9a-f]{24}',str(version))), 'Identidad de publicación WNBA inválida')
    m=json.loads((ruta_activa().parent/'versiones'/(version+'.json')).read_text())
    exigir(m.get('version')==version and m.get('dominio')=='wnba' and m.get('formato')==FORMATO
           and identidad_modelo(m)==version and huella(m['datos'])==m['dataset_sha256'],'Publicación WNBA no íntegra')
    return m


@lru_cache(maxsize=16)
def ajuste_cache(version, dataset_hash, temporadas, corte, fases, rows_json):
    # Todos los alcances forman parte de la clave; el ajuste nunca se modifica.
    return ajustar_alcance(json.loads(rows_json))


def contexto(rows, local, visita):
    result = {}
    for tid in (local, visita):
        team = []
        for r in rows:
            if tid not in (r["local_id"], r["visitante_id"]):
                continue
            home = r["local_id"] == tid
            own = r["y"][:4] if home else r["y"][4:]
            opp = r["y"][4:] if home else r["y"][:4]
            a, b = sum(own), sum(opp)
            team.append(
                {
                    "id": r["id"],
                    "fecha": r["fecha"],
                    "rival": r["visitante"] if home else r["local"],
                    "como_local": home,
                    "cuartos": own,
                    "cuartos_rival": opp,
                    "regulacion": a,
                    "regulacion_rival": b,
                    "ot": r["local_ot"] if home else r["visitante_ot"],
                    "final": r["local_total"] if home else r["visitante_total"],
                    "final_rival": r["visitante_total"] if home else r["local_total"],
                    "ot_rival": r["visitante_ot"] if home else r["local_ot"],
                    "temporada": r["temporada"],
                    "resultado": "V" if a > b else "D" if a < b else "E",
                }
            )
        result[tid] = {
            "n": len(team),
            "media_regulacion": (
                sum(x["regulacion"] for x in team) / len(team) if team else None
            ),
            "recientes": list(reversed(team[-50:])),
        }
        ultima_temporada = max((r["temporada"] for r in rows if tid in (r["local_id"],r["visitante_id"])),default=None)
        actuales = [r for r in rows if r["temporada"]==ultima_temporada and tid in (r["local_id"],r["visitante_id"])]
        if actuales:
            objetivos = []
            for r in actuales:
                casa=r["local_id"]==tid
                q=r["y"][:4] if casa else r["y"][4:]
                objetivos.append(q+[r["local_total"] if casa else r["visitante_total"]])
            result[tid]["temporada_resumen"]={"nombre":ultima_temporada,"n":len(actuales),
                "medias_favor":{k:sum(x[i] for x in objetivos)/len(objetivos) for i,k in enumerate(("Q1","Q2","Q3","Q4","COMPLETO"))},
                "media_regulacion":sum(sum(x[:4]) for x in objetivos)/len(objetivos)}
    h2h = [r for r in rows if {r["local_id"], r["visitante_id"]} == {local, visita}][
        -10:
    ]
    return {
        "equipos": result,
        "h2h": list(reversed(h2h)),
        "uso": "Descriptivo del mismo alcance previo; no otra probabilidad ni ajuste oculto.",
    }


def analizar(
    m,
    filas,
    local,
    visita,
    temporadas,
    corte,
    fases,
    mercado,
    linea,
    partido_id=None,
    es_prueba=False,
    cuota_over=None,
    cuota_under=None,
    parciales=None,
    ampliar=False,
):
    catalogo = {
        r[k]: r[n]
        for r in m["datos"]
        for k, n in (("local_id", "local"), ("visitante_id", "visitante"))
    }
    exigir(
        local in catalogo and visita in catalogo,
        "Equipo ajeno/invitado o sin histórico WNBA elegible",
    )
    fixture = None
    if partido_id:
        fixture = next(
            (
                r
                for r in filas
                if str(r.get("fixture_id")) == partido_id
                or str(r.get("partido_id")) == partido_id
                or "espn-" + r["source_game_id"] == partido_id
            ),
            None,
        )
        exigir(
            fixture is not None
            and fixture["competicion_codigo"] == "wnba"
            and (fixture["fase"] in fases or (ampliar and fixture["fase"] == "POST"))
            and (fixture["estado"] in ("FINALIZADO", "PROGRAMADO") or
                 (ampliar and parciales and fixture["estado"] in ("EN_VIVO", "DEMORADO"))),
            "Partido no pertenece a WNBA/fases/estados elegibles",
        )
        exigir(
            str(fixture["equipo_local_id"]) == local
            and str(fixture["equipo_visitante_id"]) == visita,
            "Equipos/localía distintos del fixture WNBA",
        )
        exigir(not (ampliar and parciales and datetime.fromisoformat(fixture['inicio_utc'])>datetime.now(timezone.utc))
               or es_prueba, 'Fixture futuro con cuartos observados contradictorios; solo admitirlo como prueba explícita')
        if ampliar and fixture["fase"] == "POST" and "POST" not in fases:
            fases = ["REG", "POST"]
        fecha = (
            datetime.fromisoformat(fixture["inicio_utc"])
            .astimezone(BOGOTA)
            .date()
            .isoformat()
        )
        corte = corte or min(fecha, datetime.now(BOGOTA).date().isoformat())
        exigir(corte <= fecha, "Corte posterior al inicio del partido histórico")
    corte = corte or (datetime.now(BOGOTA).date().isoformat() if ampliar else None)
    exigir(corte is not None, "Análisis manual requiere corte explícito")
    exigir(
        corte <= datetime.now(BOGOTA).date().isoformat(), "Corte futuro no soportado"
    )
    rows = alcance(m["datos"], temporadas, corte, fases)
    rows_json = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    model = ajuste_cache(
        m["version"],
        m["dataset_sha256"],
        tuple(sorted(temporadas)),
        corte,
        tuple(sorted(fases)),
        rows_json,
    )
    parciales = [] if parciales is None else parciales
    if ampliar:
        from motor.wnba_ampliado import ajustar_ot, predecir_ampliado, POLITICA_MUESTRAS
        ot = ajustar_ot(rows)
        result = predecir_ampliado(model, local, visita, mercado, linea, parciales, ot)
        if not parciales and mercado in result['predicciones']:
            neutral = {**model, "coeficientes": [model["coeficientes"][0]] + [[0.0]*4 for _ in model["coeficientes"][1:]]}
            base = predecir_ampliado(neutral, local, visita, mercado, linea, [], ot)
            result["base_descompuesta"] = {"prediccion":base["predicciones"][mercado],"probabilidades":base["probabilidades"],
                "definicion":"Intercepto común del mismo Ridge WNBA, antes de identidad de ataque/defensa y localía nominal. No otro modelo ni ajuste adicional duplicado."}
        version_calculo = "wnba-v2-" + huella({"ridge":model,"ot":ot,"algoritmo":"wnba-condicional-ot-v2","sobol":32768,"politica_muestras":POLITICA_MUESTRAS})[:24]
    else:
        result = predecir(model, local, visita, mercado, linea)
    now = datetime.now(timezone.utc)
    modo = (
        "MANUAL"
        if not fixture
        else (
            "HISTORICO"
            if datetime.fromisoformat(fixture["inicio_utc"]) <= now
            else "PREPARTIDO"
        )
    )
    incluye_ot = result.get("incluye_ot", False)
    warnings = [
        "Probabilidades estimadas SIN CALIBRAR; eficacia no certificada.",
        ("Juego completo incluye prórroga, condicionada al empate a 40 minutos; cuartos sin OT."
         if incluye_ot else "40 minutos de regulación; sin OT; ganador de regulación incluye empate."),
        "La dispersión viene de errores temporales previos al refit; no tiene calibrador probabilístico.",
        "Las métricas del candidato congelado no acreditan este ajuste final por temporadas.",
        "No incorpora lesiones, alineaciones, posesiones ni reloj en vivo.",
        "Localía nominal del fixture; no modela sedes neutrales, viajes ni burbuja 2020.",
        "Histórico reconstruido con datos actuales; no acredita disponibilidad original de cada dato.",
    ]
    if ampliar:
        warnings += ["Contrato WNBA condicional/OT v2: las métricas v1 NO validan esta ampliación.",
                     "Integración numérica Sobol discreta determinista; incertidumbre y probabilidades SIN CALIBRAR."]
        warnings += list(result.get('mercados_no_disponibles',{}).values())
    if parciales:
        warnings.append("Corte entre cuartos completos, no análisis con reloj/posesiones. Solo consulta; sin apuestas ni predicciones prepartido.")
        modo = f"CIERRE_Q{len(parciales)}"
    actuales = normalizar(filas)
    latest = max((r["fecha"] for r in actuales), default=None)
    if huella(actuales) != m["dataset_sha256"]:
        warnings.append(
            "La BD difiere del snapshot publicado (resultados nuevos o corregidos); actualizar modelo WNBA explícitamente."
        )
    if (
        datetime.now(BOGOTA).date() - datetime.fromisoformat(model["fecha_max"]).date()
    ).days > 30:
        warnings.append(
            "Último dato utilizado hace más de 30 días; revisar corte y frescura, sin inferir partidos faltantes."
        )
    requested = {r["temporada_id"]: r["temporada"] for r in m["datos"]}
    result.update(
        {
            "dominio": "wnba",
            "equipo_local": catalogo[local],
            "equipo_visitante": catalogo[visita],
            "equipo_local_id": local,
            "equipo_visitante_id": visita,
            "partido_id": (
                str(fixture.get("fixture_id") or fixture["partido_id"])
                if fixture and (fixture.get("fixture_id") or fixture["partido_id"])
                else None
            ),
            "fixture_fuente": fixture["source_game_id"] if fixture else None,
            "fixture_revision_sha256": fixture.get("revision_sha256") if fixture else None,
            "fecha_partido": fixture["inicio_utc"] if fixture else None,
            "modo": modo,
            "es_prueba": es_prueba,
            "incluye_ot": incluye_ot,
            "contrato_prediccion": "wnba-condicional-ot-v2" if ampliar else "wnba-regulacion-v1",
            "calibracion": "SIN_CALIBRAR",
            "confianza": None,
            "modelo_version": version_calculo if ampliar else model["version"],
            "publicacion_version": m["version"],
            "dataset_sha256": model["dataset_sha256"],
            "dataset_publicado_sha256": m["dataset_sha256"],
            "fecha_analisis": now.isoformat(),
            "corte_exclusivo": corte,
            "politica_corte": m["politica"]["corte"],
            "temporadas_solicitadas": [
                {"id": s, "nombre": requested[s]} for s in temporadas
            ],
            "temporadas_utilizadas": sorted({r["temporada"] for r in rows}),
            "fases_solicitadas": list(fases),
            "fases_utilizadas": sorted({r["fase"] for r in rows}),
            "muestras": {
                "local": model["muestras"][local],
                "visitante": model["muestras"][visita],
                "efectivas_local": model["efectivos"][local],
                "efectivas_visitante": model["efectivos"][visita],
                "partidos": len(rows),
            },
            "muestras_por_periodo": {
                k: {
                    "local": model["muestras"][local],
                    "visitante": model["muestras"][visita],
                }
                for k in result["predicciones"]
            },
            "semivida_dias": model["semivida_dias"],
            "dispersion": model["dispersion"],
            "ultimo_final_bd": latest,
            "ultimo_dato_utilizado": model["fecha_max"],
            "mercado": mercado,
            "linea": linea,
            "contexto": contexto(rows, local, visita),
            "advertencias": warnings,
            "prospectiva_acreditada": bool(
                fixture and modo == "PREPARTIDO" and not es_prueba and mercado in result['predicciones']
            ),
            "guardar_bitacora_habilitado": bool(
                fixture
                and (fixture.get("fixture_id") or fixture["partido_id"])
                and modo == "PREPARTIDO"
                and not es_prueba
                and mercado in result['predicciones']
            ),
            "motivo_bitacora": result.get('mercados_no_disponibles',{}).get(mercado) or "Solo selección explícita de fixture oficial previo con ID canónico; manuales/históricos/pruebas no son apuestas oficiales.",
        }
    )
    probs = result["probabilidades"]
    result["valor"] = {}
    for lado, cuota in (("over", cuota_over), ("under", cuota_under)):
        result["valor"][lado] = {
            "cuota": cuota,
            "ev_sin_calibrar": (
                probs[lado] * (cuota - 1) - probs["under" if lado == "over" else "over"]
                if cuota is not None and probs[lado] is not None
                else None
            ),
        }
    return result


def journal():
    return ruta_activa().parent / "analisis"


def registrar(result):
    result["analisis_id"] = str(uuid4())
    escribir(journal() / (result["analisis_id"] + ".json"), result)
    return result


def historial(limite=20):
    paths = sorted(
        journal().glob("*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True
    )[:limite]
    return [json.loads(p.read_text()) for p in paths]


def historial_para_vista(limite=20):
    """Enriquece descriptivos archivados sin reescribir ni recalcular predicciones."""
    salida=historial(limite)
    for r in salida:
        if all('temporada_resumen' in t for t in r.get('contexto',{}).get('equipos',{}).values()):
            continue
        try:
            m=cargar_publicacion(r['publicacion_version'])
            rows=alcance(m['datos'],[s['id'] for s in r['temporadas_solicitadas']],r['corte_exclusivo'],r['fases_solicitadas'])
            r['contexto']=contexto(rows,r['equipo_local_id'],r['equipo_visitante_id'])
            r['advertencias']=[*r['advertencias'],'Contexto descriptivo de temporada enriquecido en memoria desde el snapshot original; predicciones/archivo original intactos.']
        except (ValueError, RuntimeError, OSError, KeyError):
            r['advertencias']=[*r['advertencias'],'Resumen adicional de temporada N/D: publicación original no disponible; se conserva intacta la captura archivada.']
    return salida


def validar_guardado(p):
    """Solo una acción manual sobre un análisis oficial previo; nunca simulaciones."""
    from uuid import UUID

    evidencias = [r for r in p.razones if r.get("tipo") == "trazabilidad_wnba"]
    exigir(len(evidencias) == 1, "Falta la trazabilidad del análisis WNBA")
    aid = str(UUID(evidencias[0].get("analisis_id", "")))
    try:
        r = json.loads((journal() / (aid + ".json")).read_text())
    except (OSError, ValueError) as e:
        raise ValueError("Análisis WNBA no encontrado") from e
    exigir(
        r.get("dominio") == "wnba"
        and r.get("guardar_bitacora_habilitado") is True
        and not r.get("es_prueba")
        and r.get("modo") == "PREPARTIDO"
        and datetime.fromisoformat(r["fecha_partido"]) > datetime.now(timezone.utc),
        "Solo un análisis oficial WNBA previo vigente permite guardado; no pruebas, manuales ni históricos",
    )
    exigir(
        p.partido_id == r["partido_id"]
        and p.equipo_local == r["equipo_local"]
        and p.equipo_visitante == r["equipo_visitante"]
        and p.mercado == r["mercado"]
        and float(p.linea) == r["linea"],
        "La selección no coincide con el análisis WNBA",
    )
    exigir(evidencias[0].get("incluye_ot", False) == r["incluye_ot"], "Convención OT distinta del análisis WNBA")
    esperado = r["probabilidades"][p.lado.lower()]
    exigir(esperado is not None, "Mercado WNBA N/D: no permite guardar una probabilidad ausente")
    exigir(
        p.probabilidad_sistema is not None
        and abs(float(p.probabilidad_sistema) - esperado) < 1e-9
        and p.confianza_sistema is None,
        "Probabilidad RAW WNBA alterada o confianza no acreditada",
    )
