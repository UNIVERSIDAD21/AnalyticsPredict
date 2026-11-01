"""Documento personal SQLite: sin PostgreSQL, fitting ni lecturas de perfiles."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Literal
from urllib.parse import quote
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from servicios.archivos_privados import proteger_privado


def serializar(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


class Estricto(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Entrada(Estricto):
    id: str = Field(min_length=1, max_length=300)
    titulo: str = Field(max_length=1000)
    liga: Literal['nba', 'wnba', 'euroliga', 'futbol']
    guardadoEn: str
    tipo: Literal['base', 'resultado']
    snapshot: Any
    notas: str = Field(max_length=5000)
    etiquetas: list[str] = Field(max_length=12)
    favorito: bool

    @model_validator(mode='after')
    def coherencia(self):
        datetime.fromisoformat(self.guardadoEn.replace('Z', '+00:00'))
        if any(len(getattr(self,k).encode('utf-16-le'))//2 > limit for k,limit in (('id',300),('titulo',1000),('notas',5000))):
            raise ValueError('Texto demasiado largo')
        if any(len(t.encode('utf-16-le'))//2 > 300 for t in self.etiquetas):
            raise ValueError('Etiqueta demasiado larga')
        return self


class Favorito(Estricto):
    tipo: Literal['liga', 'equipo', 'competicion']
    liga: Literal['nba', 'wnba', 'euroliga', 'futbol']
    id: str = Field(min_length=1, max_length=300)
    nombre: str = Field(min_length=1, max_length=200)

    @model_validator(mode='after')
    def longitudes(self):
        if len(self.id.encode('utf-16-le'))//2 > 300 or len(self.nombre.encode('utf-16-le'))//2 > 200:
            raise ValueError('Texto demasiado largo')
        return self


class Apariencia(Estricto):
    tema: Literal['oscuro', 'claro']
    densidad: Literal['comoda', 'compacta']
    texto: Literal['normal', 'grande']


class Datos(Estricto):
    cuaderno: list[Entrada] = Field(max_length=100)
    favoritos: list[Favorito] = Field(max_length=200)
    apariencia: Apariencia | None

    @model_validator(mode='after')
    def coherencia(self):
        if len({e.id for e in self.cuaderno}) != len(self.cuaderno):
            raise ValueError('IDs duplicados')
        if len({(f.liga, f.tipo, f.id) for f in self.favoritos}) != len(self.favoritos):
            raise ValueError('Favoritos duplicados')
        if any(f.tipo == 'liga' and f.id != f.liga for f in self.favoritos):
            raise ValueError('Liga incoherente')
        doc = self.model_dump()
        text = serializar(doc['cuaderno'])
        text.encode('utf-8')
        if len(text.encode('utf-16-le'))//2 > 4_000_000:
            raise ValueError('Capacidad de consultas excedida')
        pending = [(doc, 0)]
        while pending:
            value, depth = pending.pop()
            if depth > 60:
                raise ValueError('Estructura demasiado profunda')
            if isinstance(value, (list, dict)):
                pending.extend((v, depth+1) for v in (value.values() if isinstance(value, dict) else value))
        return self


class Cambio(Estricto):
    revision: int = Field(ge=0)
    operacion: str
    datos: Datos

    @model_validator(mode='after')
    def identidad(self):
        UUID(self.operacion)
        return self


class Conflicto(ValueError):
    pass


def ruta():
    directory = Path(os.environ.get('ANALYTICSPREDICT_DATOS_PERSONALES', str(
        Path.home() / 'AnalyticsPredict/Datos privados locales/personal'))).expanduser()
    if directory.is_symlink() or (directory / 'mis_analisis.sqlite3').is_symlink():
        raise ValueError('El almacén no admite enlaces simbólicos')
    return directory / 'mis_analisis.sqlite3'


def conectar(path, escritura=False):
    if escritura:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        proteger_privado(path.parent)
    conn = sqlite3.connect(str(path) if escritura else 'file:'+quote(str(path.resolve()), safe='/:')+'?mode=ro',
                           uri=not escritura, timeout=2, isolation_level=None)
    try:
        conn.execute('PRAGMA busy_timeout=2000')
        if escritura:
            proteger_privado(path)
            conn.execute('PRAGMA synchronous=FULL')
        else:
            conn.execute('PRAGMA query_only=ON')
    except BaseException:
        conn.close()
        raise
    return conn


def vacio():
    return dict(formato='almacen-personal-v1', existe=False, revision=0, sha256=None, actualizadoEn=None,
                datos=dict(cuaderno=[], favoritos=[], apariencia=None))


def leer_conn(conn):
    version=conn.execute('PRAGMA user_version').fetchone()[0]
    if version == 0 and not conn.execute("SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1").fetchone():
        return vacio()  # Primer intento revertido: no inventar datos ni bloquear el siguiente guardado.
    if version != 1:
        raise ValueError('Versión de almacén no compatible')
    row = conn.execute('SELECT revision,documento,sha256,actualizado FROM personal WHERE id=1').fetchone()
    if row is None:
        return vacio()
    if hashlib.sha256(row[1].encode()).hexdigest() != row[2]:
        raise ValueError('Contenido del almacén no íntegro')
    data = json.loads(row[1])
    Datos.model_validate(data)
    return dict(formato='almacen-personal-v1', existe=True, revision=row[0], datos=data, sha256=row[2], actualizadoEn=row[3])


def leer():
    path = ruta()
    if not path.exists():
        return vacio()
    conn = conectar(path)
    try:
        return leer_conn(conn)
    finally:
        conn.close()


def guardar(cambio: Cambio):
    doc = cambio.datos.model_dump()
    text = serializar(doc)
    digest = hashlib.sha256(text.encode()).hexdigest()
    operation_digest = hashlib.sha256(serializar(dict(revision=cambio.revision, datos=doc)).encode()).hexdigest()
    conn = conectar(ruta(), escritura=True)
    try:
        conn.execute('BEGIN IMMEDIATE')
        version = conn.execute('PRAGMA user_version').fetchone()[0]
        if version == 0:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1").fetchone():
                raise ValueError('Almacén no reconocido; no se añade esquema a una BD ajena')
            conn.execute('CREATE TABLE personal(id INTEGER PRIMARY KEY CHECK(id=1),revision INTEGER NOT NULL,documento TEXT NOT NULL,sha256 TEXT NOT NULL,actualizado TEXT NOT NULL)')
            conn.execute('CREATE TABLE operaciones(id TEXT PRIMARY KEY,hash TEXT NOT NULL,revision INTEGER NOT NULL)')
            conn.execute('PRAGMA user_version=1')
        elif version != 1:
            raise ValueError('Versión de almacén no compatible')
        previous = conn.execute('SELECT hash,revision FROM operaciones WHERE id=?', (cambio.operacion,)).fetchone()
        if previous:
            if previous[0] != operation_digest:
                raise Conflicto('La operación ya tiene otro contenido; no se sobrescribió')
            conn.rollback()
            return dict(repetida=True, revision_guardada=previous[1], estado=leer_conn(conn))
        current = leer_conn(conn)
        if cambio.revision != current['revision']:
            raise Conflicto('Tus datos cambiaron en otra pestaña. Recarga antes de guardar')
        old = {e['id']:e for e in current['datos']['cuaderno']}
        for e in doc['cuaderno']:
            if e['id'] in old and any(serializar(e[k]) != serializar(old[e['id']][k]) for k in ('snapshot','guardadoEn','liga','tipo','titulo')):
                raise Conflicto('La consulta original es inmutable; conserva otro ID al importar una copia distinta')
        revision = current['revision']+1
        now = datetime.now(timezone.utc).isoformat()
        conn.execute('INSERT INTO personal VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,documento=excluded.documento,sha256=excluded.sha256,actualizado=excluded.actualizado', (revision,text,digest,now))
        conn.execute('INSERT INTO operaciones VALUES(?,?,?)', (cambio.operacion,operation_digest,revision))
        conn.execute('DELETE FROM operaciones WHERE revision<?', (max(0,revision-500),))
        conn.commit()
        return dict(repetida=False, revision_guardada=revision, estado=leer_conn(conn))
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def recuperar():
    if not ruta().exists():
        raise ValueError('No hay almacén para recuperar')
    conn = conectar(ruta(), escritura=True)
    try:
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('El almacén requiere restaurar un respaldo verificado')
        return leer_conn(conn)
    finally:
        conn.close()


def copiar_consistente(origen: Path, destino: Path):
    if destino.exists() or destino.resolve() == origen.resolve():
        raise FileExistsError('El destino debe ser nuevo')
    parent=destino.parent.resolve()
    private_root=(Path.home()/'AnalyticsPredict/Datos privados locales').resolve()
    if parent.exists() and not (parent.is_relative_to(ruta().parent.resolve()) or parent.is_relative_to(private_root)):
        raise ValueError('Usa un directorio privado nuevo para no modificar permisos de carpetas generales')
    destino.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    proteger_privado(destino.parent)
    src = conectar(origen)
    dst = None
    try:
        dst = sqlite3.connect(destino)
        proteger_privado(destino)
        src.backup(dst)
        assert dst.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        state = leer_conn(dst)
        return dict(revision=state['revision'],documento_sha256=state['sha256'],archivo_sha256=hashlib.sha256(destino.read_bytes()).hexdigest())
    finally:
        if dst is not None:dst.close()
        src.close()


def respaldar():
    if not leer()['existe']:raise ValueError('Guarda una consulta antes de crear el respaldo del almacén')
    now = datetime.now(timezone.utc)
    dest = ruta().parent / 'respaldos' / ('mis_analisis_'+now.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex+'.sqlite3')
    return dict(creadoEn=now.isoformat(), **copiar_consistente(ruta(),dest))
