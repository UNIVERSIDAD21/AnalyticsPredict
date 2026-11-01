"""Turnos HTTP entre procesos LATAM y pausa compartida ante límites de fuente.

No coordina clientes ajenos (incluido el MLS ya iniciado). No evade bloqueos.
El lock se libera incluso con SIGKILL; cada reserva se escribe antes del GET.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
from servicios.locks_archivo import adquirir

from .archivo import ArchivoError, guardar_json


class PausaRed(ArchivoError):
    pass


class ControlRed:
    def __init__(self, root, *, dormir=time.sleep, reloj=time.time):
        self.root = Path(root)
        self.dormir, self.reloj = dormir, reloj
        self.estado = None

    @contextmanager
    def turno(self, intervalo):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.root / "turno.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            while True:
                try:
                    adquirir(fd)
                    break
                except BlockingIOError:
                    self.dormir(0.25)
            path = self.root / "estado.json"
            try:
                estado = json.loads(path.read_bytes()) if path.exists() else {}
                if not isinstance(estado, dict):
                    raise ValueError("objeto")
                for k in ("proximo_inicio", "pausa_hasta"):
                    value = estado.get(k, 0)
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                        raise ValueError(k)
            except (ValueError, TypeError, OSError) as exc:
                raise ArchivoError("Control de red alterado; conservar e investigar") from exc
            self.estado = estado
            if estado.get("pausa_hasta", 0) > self.reloj():
                fecha = datetime.fromtimestamp(estado["pausa_hasta"], timezone.utc).isoformat()
                raise PausaRed(f"Fuente en pausa compartida hasta {fecha}: {estado.get('motivo')}")
            self.dormir(max(0, estado.get("proximo_inicio", 0) - self.reloj()))
            estado["proximo_inicio"] = self.reloj() + intervalo
            guardar_json(path, estado)
            yield
        finally:
            self.estado = None
            os.close(fd)

    def pausar(self, segundos, motivo):
        if self.estado is None:
            raise RuntimeError("La pausa debe registrarse dentro del turno HTTP")
        self.estado.update(pausa_hasta=max(self.estado.get("pausa_hasta", 0), self.reloj() + segundos), motivo=motivo)
        guardar_json(self.root / "estado.json", self.estado)
