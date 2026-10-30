"""Datos/journal Euroliga. PostgreSQL siempre READ ONLY; sin registro NBA."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4

from psycopg.rows import dict_row
from psycopg.pq import TransactionStatus

from db import obtener_pool
from motor.euroliga import escribir_nuevo, final_valido, normalizar_nombre, preparar_filas, ruta_activa


@contextmanager
def _conexion_lectura(pool=None):
    with (pool or obtener_pool()).connection() as conn:
        # GET/HEAD ya entra en una transacción READ ONLY de PoolAplicacion.
        # Psycopg no permite volver a asignar read_only mientras esté abierta.
        if conn.info.transaction_status != TransactionStatus.IDLE:
            if not conn.read_only or conn.execute('SHOW transaction_read_only').fetchone()[0] != 'on':
                raise RuntimeError('La transacción heredada debe ser READ ONLY')
            conn.execute("SET LOCAL statement_timeout='10s'")
            yield conn
            return
        anterior = conn.read_only
        conn.read_only = True
        try:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                conn.execute("SET LOCAL statement_timeout='10s'")
                yield conn
        finally:
            conn.read_only = anterior


@contextmanager
def conexion_lectura(pool=None):
    # POST de análisis también lee con PoolAplicacion en READ ONLY desde el
    # inicio, antes de que el pool ejecute sus SET LOCAL de límites HTTP.
    from lecturas_http import solo_lectura_http
    token = solo_lectura_http.set(True)
    try:
        with _conexion_lectura(pool) as conn:
            yield conn
    finally:
        solo_lectura_http.reset(token)


def leer_datos(pool=None) -> list[dict]:
    with conexion_lectura(pool) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""SELECT p.*,el.nombre AS local,ev.nombre AS visitante,
            t.nombre AS temporada_nombre,cb.codigo AS competicion_codigo
            FROM partidos_baloncesto p
            JOIN competiciones_baloncesto cb ON cb.id=p.competicion_id
            JOIN equipos el ON el.id=p.equipo_local_id
            JOIN equipos ev ON ev.id=p.equipo_visitante_id
            JOIN temporadas_baloncesto t ON t.id=p.temporada_id
            WHERE cb.codigo='euroleague' ORDER BY p.fecha_partido,p.id""")
        return json.loads(json.dumps(cur.fetchall(), default=str))


def resumir_fixture(r: dict) -> dict:
    return {"id": str(r["id"]), "fecha_partido": str(r["fecha_partido"])[:10],
            "tipo_partido": r["tipo_partido"], "equipo_local_id": str(r["equipo_local_id"]),
            "equipo_visitante_id": str(r["equipo_visitante_id"]), "equipo_local_nombre": r["local"],
            "equipo_visitante_nombre": r["visitante"], "temporada_id": str(r["temporada_id"]),
            "temporada_nombre": "Euroliga " + r["temporada_nombre"],
            "competicion_codigo": "euroleague", "local_total": r["local_total"],
            "visitante_total": r["visitante_total"], "finalizado": final_valido(r)}


def _resumen_equipo_temporada(partidos: list[dict], nombre: str) -> dict:
    """Resumen de regulación por temporada/sede; los empates no se convierten en victorias."""
    partidos_lado = []
    for r in partidos:
        lado = "local" if normalizar_nombre(r["local"]) == nombre else "visitante"
        otro = "visitante" if lado == "local" else "local"
        partidos_lado.append({
            "como_local": lado == "local",
            "pf": sum(r[f"{lado}_q{i}"] for i in range(1, 5)),
            "pc": sum(r[f"{otro}_q{i}"] for i in range(1, 5)),
        })

    def resumir(muestra: list[dict]) -> dict:
        victorias = sum(p["pf"] > p["pc"] for p in muestra)
        empates = sum(p["pf"] == p["pc"] for p in muestra)
        derrotas = sum(p["pf"] < p["pc"] for p in muestra)
        n = len(muestra)
        return {
            "partidos": n, "victorias_regulacion": victorias, "empates_regulacion": empates,
            "derrotas_regulacion": derrotas,
            "promedio_favor_regulacion": sum(p["pf"] for p in muestra) / n if n else None,
            "promedio_contra_regulacion": sum(p["pc"] for p in muestra) / n if n else None,
            "balance_regulacion": (sum(p["pf"] - p["pc"] for p in muestra) / n) if n else None,
        }

    return {"total": resumir(partidos_lado),
            "como_local": resumir([p for p in partidos_lado if p["como_local"]]),
            "como_visitante": resumir([p for p in partidos_lado if not p["como_local"]])}


def contexto(filas: list[dict], local: str, visitante: str, fecha: str,
             temporada_reciente: str | None = None) -> dict:
    datos = preparar_filas(filas, fecha)
    local, visitante = normalizar_nombre(local), normalizar_nombre(visitante)
    equipos = {}
    for nombre in (local, visitante):
        propios = [r for r in datos if nombre in (normalizar_nombre(r["local"]), normalizar_nombre(r["visitante"]))]
        recientes = propios[-50:]
        detalle = []
        for r in reversed(recientes):
            casa = normalizar_nombre(r["local"]) == nombre
            lado, otro = ("local", "visitante") if casa else ("visitante", "local")
            puntos_regulacion = sum(r[f"{lado}_q{i}"] for i in range(1, 5))
            puntos_rival_regulacion = sum(r[f"{otro}_q{i}"] for i in range(1, 5))
            diferencia = puntos_regulacion - puntos_rival_regulacion
            detalle.append({"id": r["id"], "fecha": r["fecha_partido"], "rival": r[otro], "como_local": casa,
                            "puntos_regulacion": puntos_regulacion,
                            "puntos_rival_regulacion": puntos_rival_regulacion,
                            "resultado_regulacion": "V" if diferencia > 0 else "D" if diferencia < 0 else "E",
                            "cuartos": [{"equipo": r[f"{lado}_q{i}"], "rival": r[f"{otro}_q{i}"]} for i in range(1, 5)],
                            "puntos_ot": r[f"{lado}_ot"], "puntos_rival_ot": r[f"{otro}_ot"],
                            "puntos_finales": r[f"{lado}_total"], "puntos_rival_finales": r[f"{otro}_total"]})
        temporada = temporada_reciente or (datos[-1]["temporada_nombre"] if datos else None)
        partidos_temporada = [r for r in propios if r["temporada_nombre"] == temporada]
        equipos[nombre] = {"n_historico": len(propios), "ventana": "últimos 50 finales previos al fixture",
                           "temporada_resumen": {"nombre": temporada,
                               **_resumen_equipo_temporada(partidos_temporada, nombre)},
                           "recientes": detalle,
                           "media_regulacion": sum(x["puntos_regulacion"] for x in detalle) / len(detalle) if detalle else None}
    h2h = [r for r in datos if {normalizar_nombre(r["local"]), normalizar_nombre(r["visitante"])} == {local, visitante}][-10:]
    return {"corte_exclusivo": fecha, "equipos": equipos, "h2h": [{"fecha": r["fecha_partido"], "local": r["local"],
             "visitante": r["visitante"], "local_total": r["local_total"], "visitante_total": r["visitante_total"]} for r in reversed(h2h)],
             "uso": "Contexto descriptivo Euroliga; últimos 50 finales previos al corte, regulación separada de prórroga y final. No altera Ridge ni constituye otra probabilidad."}


def ruta_journal() -> Path:
    return Path(os.getenv("ANALYTICSPREDICT_EUROLIGA_JOURNAL", str(ruta_activa().parent / "analisis"))).expanduser()


def registrar(resultado: dict, fixture: dict | None, directorio: Path | None = None) -> dict:
    ahora = datetime.now(timezone.utc)
    identificador = str(uuid4())
    fecha = str(fixture["fecha_partido"])[:10] if fixture else None
    # El catálogo no conserva hora de inicio. No acreditar una captura del mismo
    # día como anterior al kickoff; tampoco acreditar una condicionada live.
    from servicios.horarios_agenda import requiere_reconstruccion
    prospectiva = bool(fixture and not requiere_reconstruccion(fecha,fixture.get('horario'),ahora)
                       and resultado["modo"] == "PREPARTIDO")
    resultado.update({"analisis_id": identificador, "partido_id": str(fixture["id"]) if fixture else None,
                      "fecha_partido": fecha, "prospectiva_acreditada_por_fecha": prospectiva,
                      "limite_temporal": "Anterioridad sólo con inicio UTC verificado; una fecha canónica sin hora no la acredita."})
    escribir_nuevo((directorio or ruta_journal()) / (identificador + ".json"), resultado)
    return resultado


def historial(limite: int = 50) -> list[dict]:
    ruta = ruta_journal()
    if not ruta.is_dir():
        return []
    archivos = sorted(ruta.glob("*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True)[:limite]
    return [json.loads(p.read_text(encoding="utf-8")) for p in archivos]
