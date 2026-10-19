from datetime import datetime, timezone
from uuid import uuid4

from servicios.partidos_guardados import (
    ESTADO_PARTIDO_ARCHIVADO,
    ESTADO_PARTIDO_GUARDADO,
    archivar_partido_futbol_guardado,
    guardar_partido_futbol,
)


class Cursor:
    def __init__(self, resultados):
        self.resultados = list(resultados)
        self.consultas = []
        self.parametros = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, consulta, parametros=None):
        self.consultas.append(consulta)
        self.parametros.append(parametros)

    def fetchone(self):
        return self.resultados.pop(0)


class Conexion:
    def __init__(self, cursor):
        self.cursor_instancia = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def cursor(self, **_kwargs):
        return self.cursor_instancia


class Pool:
    def __init__(self, cursor):
        self.cursor_instancia = cursor

    def connection(self):
        return Conexion(self.cursor_instancia)


def test_guardar_partido_es_neutral_y_no_ejecuta_ddl():
    partido_id = uuid4()
    ahora = datetime(2026, 10, 19, tzinfo=timezone.utc)
    fila_partido = {
        "partido_id": partido_id,
        "competicion": "Liga de prueba",
        "fecha_partido": ahora,
        "estado_partido": "PROGRAMADO",
        "jornada": 5,
        "equipo_local": "Local",
        "equipo_visitante": "Visitante",
        "goles_local": None,
        "goles_visitante": None,
        "creado_en": ahora,
        "actualizado_en": ahora,
    }
    cursor = Cursor([
        {"id": partido_id},
        None,
        {"creado_en": ahora, "actualizado_en": ahora},
        fila_partido,
    ])

    item = guardar_partido_futbol(partido_id, pool=Pool(cursor))

    assert item["estado"] == ESTADO_PARTIDO_GUARDADO
    assert item["partido"]["equipo_local"] == "Local"
    insertar = cursor.consultas[2]
    assert "INSERT INTO apuestas_analizadas" in insertar
    assert "NULL, NULL, NULL, NULL, NULL" in insertar
    assert "payload" not in " ".join(cursor.consultas).lower()
    assert not any("CREATE TABLE" in consulta.upper() or "ALTER TABLE" in consulta.upper() for consulta in cursor.consultas)


def test_archivar_es_update_y_no_delete():
    cursor = Cursor([{"id": 17}])

    assert archivar_partido_futbol_guardado(uuid4(), pool=Pool(cursor)) is True
    consulta = cursor.consultas[0].upper()
    assert "UPDATE APUESTAS_ANALIZADAS" in consulta
    assert "DELETE" not in consulta
    assert cursor.parametros[0][0] == ESTADO_PARTIDO_ARCHIVADO
    assert cursor.parametros[0][2] == ESTADO_PARTIDO_GUARDADO


def test_guardar_de_nuevo_reactiva_registro_existente_sin_insertar():
    partido_id = uuid4()
    ahora = datetime(2026, 10, 19, tzinfo=timezone.utc)
    cursor = Cursor([
        {"id": partido_id},
        {"id": 42},
        {"creado_en": ahora, "actualizado_en": ahora},
        {
            "partido_id": partido_id,
            "competicion": "Liga de prueba",
            "fecha_partido": ahora,
            "estado_partido": "PROGRAMADO",
            "jornada": 5,
            "equipo_local": "Local",
            "equipo_visitante": "Visitante",
            "goles_local": None,
            "goles_visitante": None,
        },
    ])

    item = guardar_partido_futbol(partido_id, pool=Pool(cursor))

    assert item["partido_id"] == str(partido_id)
    assert item["estado"] == ESTADO_PARTIDO_GUARDADO
    assert "UPDATE apuestas_analizadas" in cursor.consultas[2]
    assert not any("INSERT INTO apuestas_analizadas" in consulta for consulta in cursor.consultas)
