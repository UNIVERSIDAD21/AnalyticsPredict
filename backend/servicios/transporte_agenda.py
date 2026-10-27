"""Transporte público compartido por las agendas, sin acceso a BD ni modelos.

Complementa los normalizadores existentes; no ejecuta scrapers por render.
La caché y el turno entre procesos se conservan fuera del repositorio.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.parse import urlencode, urlsplit

import requests

HOSTS = {"site.api.espn.com", "api-live.euroleague.net", "live.euroleague.net"}
MAX_BYTES = 8 * 1024 * 1024


def atomico(path, contenido):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporal = path.with_name(path.name + f".{os.getpid()}.tmp")
    fd = os.open(temporal, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(contenido)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporal, path)


def guardar(path, objeto):
    atomico(path, json.dumps(objeto, ensure_ascii=False, indent=2, default=str).encode())


class FuenteNoDisponible(RuntimeError):
    pass


class ClienteAgenda:
    def __init__(self, cache, *, intervalo=5, max_requests=400, session=None,
                 reloj=time.time, dormir=time.sleep):
        if intervalo < 3 or not 1 <= max_requests <= 1000:
            raise ValueError("Frecuencia/presupuesto fuera del contrato")
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.intervalo, self.presupuesto = intervalo, max_requests
        self.session = session or requests.Session()
        self.reloj, self.dormir = reloj, dormir
        self.http = 0
        self.hits = 0
        self.bloqueados = set()

    @contextmanager
    def turno(self):
        fd = os.open(self.cache / "red.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            plazo = self.reloj() + 30
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if self.reloj() >= plazo:
                        raise FuenteNoDisponible("Turno HTTP ocupado; reanudar en próximo ciclo")
                    self.dormir(0.2)
            estado_path = self.cache / "red.json"
            estado = json.loads(estado_path.read_text()) if estado_path.exists() else {}
            if estado.get("pausa_hasta", 0) > self.reloj():
                raise FuenteNoDisponible("Fuente en pausa por 429; no se elude el límite")
            self.dormir(max(0, estado.get("siguiente", 0) - self.reloj()))
            estado["siguiente"] = self.reloj() + self.intervalo
            guardar(estado_path, estado)
            yield estado
        finally:
            os.close(fd)

    def obtener(self, url, params=None, *, ttl=21600):
        u = urlsplit(url)
        if u.scheme != "https" or u.hostname not in HOSTS or u.username or u.password:
            raise ValueError("Origen público no permitido")
        direccion = url + (("&" if u.query else "?") + urlencode(params) if params else "")
        clave = hashlib.sha256(direccion.encode()).hexdigest()
        raw, meta = self.cache / (clave + ".raw"), self.cache / (clave + ".json")
        if meta.exists() and raw.exists():
            anterior = json.loads(meta.read_text())
            contenido = raw.read_bytes()
            if hashlib.sha256(contenido).hexdigest() != anterior["sha256"]:
                raise FuenteNoDisponible("Caché alterada: conservar e investigar")
            if self.reloj() - anterior["observado_epoch"] <= ttl:
                self.hits += 1
                return contenido, {**anterior, "cache": True}
        if u.hostname in self.bloqueados:
            raise FuenteNoDisponible("Origen bloqueado en este ciclo; no se reintenta")
        for intento in range(2):
            if self.http >= self.presupuesto:
                raise FuenteNoDisponible("Presupuesto HTTP agotado")
            with self.turno() as estado:
                self.http += 1
                try:
                    r = self.session.get(direccion, timeout=(5, 20), allow_redirects=False,
                                         headers={"User-Agent": "AnalyticsPredict-Agenda/1.0", "Accept": "application/json, application/xml"})
                except requests.RequestException as exc:
                    if intento == 1:
                        raise FuenteNoDisponible(type(exc).__name__) from exc
                    continue
                if r.status_code in (401, 403) or 300 <= r.status_code < 400:
                    self.bloqueados.add(u.hostname)
                    raise FuenteNoDisponible(f"HTTP {r.status_code}; origen detenido sin evasión")
                if r.status_code == 429:
                    espera = r.headers.get("Retry-After", "60")
                    try:
                        segundos = max(0, float(espera))
                    except ValueError:
                        segundos = max(0, parsedate_to_datetime(espera).timestamp() - self.reloj())
                    estado["pausa_hasta"] = self.reloj() + max(60, segundos)
                    guardar(self.cache / "red.json", estado)
                    raise FuenteNoDisponible("HTTP 429: pausa persistida; datos previos conservados")
                if r.status_code >= 500 and intento == 0:
                    continue
                if r.status_code != 200:
                    raise FuenteNoDisponible(f"HTTP {r.status_code}")
                contenido = r.content
                if len(contenido) > MAX_BYTES:
                    raise FuenteNoDisponible("Respuesta supera el límite de tamaño")
                info = {"url": direccion, "http": 200,
                        "observado_en": datetime.fromtimestamp(self.reloj(), timezone.utc).isoformat(),
                        "observado_epoch": self.reloj(), "sha256": hashlib.sha256(contenido).hexdigest(),
                        "archivo": str(raw), "bytes": len(contenido), "cache": False}
                # Una revisión posterior de la misma URL no destruye su prueba.
                blob = self.cache / 'blobs' / (info['sha256']+'.raw')
                if not blob.exists():
                    atomico(blob,contenido)
                info['archivo'] = str(blob)
                atomico(raw, contenido)
                guardar(meta, info)
                return contenido, info
        raise FuenteNoDisponible("Reintentos HTTP agotados")

    def json(self, url, params=None, **kw):
        raw, info = self.obtener(url, params, **kw)
        return json.loads(raw), info
