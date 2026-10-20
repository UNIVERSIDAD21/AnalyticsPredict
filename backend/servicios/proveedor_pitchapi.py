"""Cliente de solo lectura para la API oficial de PitchAPI.

No sigue redirecciones, no imita navegadores y no reintenta respuestas 401/403.
La clave se recibe por argumento para que el llamador decida el almacén protegido;
este módulo nunca la registra ni la incluye en excepciones.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, Callable
import requests


BASE_URL = "https://api.pitchapi.dev"
_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*_[A-Za-z0-9]{6}$")
_PATH_RE = re.compile(r"^/v1/[A-Za-z0-9_./-]+$")


class ErrorProveedorPitchAPI(RuntimeError):
    """Fallo sanitizado del proveedor; nunca contiene headers ni cuerpos HTTP."""


class AccesoDenegadoPitchAPI(ErrorProveedorPitchAPI):
    """La API devolvió 401/403. No se renueva ni sortea el acceso."""

    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"PitchAPI rechazó el acceso (HTTP {status_code})")


class LimitePitchAPI(ErrorProveedorPitchAPI):
    """La API devolvió 429; el llamador debe respetar Retry-After."""

    def __init__(self, retry_after: str | None):
        self.retry_after = retry_after
        super().__init__("PitchAPI aplicó su límite de ráfaga (HTTP 429)")


class ContratoPitchAPI(ErrorProveedorPitchAPI):
    """La respuesta no coincide con el contrato JSON publicado."""


class ClientePitchAPI:
    """Cliente GET de bajo ritmo con host fijo y errores sin datos sensibles."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: tuple[float, float] = (5.0, 20.0),
        intervalo_minimo: float = 1.0,
        session: requests.Session | None = None,
        dormir: Callable[[float], None] = time.sleep,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Se requiere PITCHAPI_API_KEY")
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "AnalyticsPredict/1.0",
                "X-API-KEY": api_key.strip(),
            }
        )
        self._timeout = timeout
        self._intervalo_minimo = max(float(intervalo_minimo), 0.0)
        self._dormir = dormir
        self._reloj = reloj
        self._ultima_peticion: float | None = None

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "ClientePitchAPI":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _validar_path(path: str) -> str:
        if not isinstance(path, str) or not _PATH_RE.fullmatch(path):
            raise ValueError("Ruta PitchAPI inválida")
        if ".." in path.split("/"):
            raise ValueError("Ruta PitchAPI inválida")
        return path

    @staticmethod
    def validar_id(resource_id: str) -> str:
        if not isinstance(resource_id, str) or not _ID_RE.fullmatch(resource_id):
            raise ValueError("ID PitchAPI inválido")
        return resource_id

    def _esperar_intervalo(self) -> None:
        ahora = self._reloj()
        if self._ultima_peticion is not None:
            restante = self._intervalo_minimo - (ahora - self._ultima_peticion)
            if restante > 0:
                self._dormir(restante)
        self._ultima_peticion = self._reloj()

    def get_data(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        path = self._validar_path(path)
        self._esperar_intervalo()
        try:
            response = self._session.get(
                f"{BASE_URL}{path}",
                params=params,
                timeout=self._timeout,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            # No publicar str(exc): algunas implementaciones incluyen URL/contexto.
            raise ErrorProveedorPitchAPI(
                f"Fallo de red al consultar PitchAPI ({type(exc).__name__})"
            ) from None

        status = int(response.status_code)
        if status in (401, 403):
            raise AccesoDenegadoPitchAPI(status)
        if status == 429:
            raise LimitePitchAPI(response.headers.get("Retry-After"))
        if 300 <= status < 400:
            raise ErrorProveedorPitchAPI("PitchAPI devolvió una redirección no permitida")
        if status < 200 or status >= 300:
            raise ErrorProveedorPitchAPI(f"PitchAPI devolvió HTTP {status}")
        try:
            payload = response.json()
        except (ValueError, requests.JSONDecodeError):
            raise ContratoPitchAPI("PitchAPI devolvió JSON inválido") from None
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            raise ContratoPitchAPI("PitchAPI devolvió un sobre JSON inválido")
        return payload["data"]

    def listar_ligas(self) -> list[dict[str, Any]]:
        data = self.get_data("/v1/leagues")
        leagues = data.get("leagues")
        if not isinstance(leagues, list) or any(not isinstance(x, dict) for x in leagues):
            raise ContratoPitchAPI("Catálogo de ligas PitchAPI inválido")
        return leagues

    def listar_partidos_liga(
        self, league_id: str, *, season: str, status: str = "played"
    ) -> list[dict[str, Any]]:
        league_id = self.validar_id(league_id)
        if not isinstance(season, str) or not season.strip():
            raise ValueError("Temporada PitchAPI obligatoria")
        if status not in {"played", "upcoming", "all"}:
            raise ValueError("Estado PitchAPI inválido")
        data = self.get_data(
            f"/v1/leagues/{league_id}/matches",
            params={"season": season, "status": status},
        )
        matches = data.get("matches")
        if not isinstance(matches, list) or any(not isinstance(x, dict) for x in matches):
            raise ContratoPitchAPI("Lista de partidos PitchAPI inválida")
        return matches

    def obtener_partido(self, match_id: str) -> dict[str, Any]:
        match_id = self.validar_id(match_id)
        return self.get_data(f"/v1/matches/{match_id}")

    def obtener_estadisticas(self, match_id: str) -> dict[str, Any]:
        match_id = self.validar_id(match_id)
        return self.get_data(f"/v1/matches/{match_id}/stats")


def interpretar_partido_liga_pitchapi(league_id: str, match: dict[str, Any]):
    """Convierte una fila documentada de league-matches a identidad tipada.

    Las llaves de país/nombre no se usan para enlazar equipos. El caller aún debe
    aportar mapeos explícitos de liga y de ambos IDs de equipo al catálogo local.
    """
    from servicios.resolucion_multifuente_futbol import PartidoProveedor

    ClientePitchAPI.validar_id(league_id)
    if not isinstance(match, dict):
        raise ContratoPitchAPI("Fila de partido PitchAPI inválida")
    try:
        event_id = ClientePitchAPI.validar_id(match.get("id"))
    except ValueError:
        raise ContratoPitchAPI("ID de partido PitchAPI inválido") from None
    home = match.get("home_team")
    away = match.get("away_team")
    if not isinstance(home, dict) or not isinstance(away, dict):
        raise ContratoPitchAPI("Identidad de equipos PitchAPI ausente")
    try:
        home_id = ClientePitchAPI.validar_id(home.get("id"))
        away_id = ClientePitchAPI.validar_id(away.get("id"))
    except ValueError:
        raise ContratoPitchAPI("ID de equipo PitchAPI inválido") from None
    if home_id == away_id:
        raise ContratoPitchAPI("Partido PitchAPI con equipos duplicados")
    kickoff = match.get("time_utc")
    if not isinstance(kickoff, str):
        raise ContratoPitchAPI("Inicio UTC PitchAPI ausente")
    try:
        inicio_utc = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
    except ValueError:
        raise ContratoPitchAPI("Inicio UTC PitchAPI inválido") from None
    if inicio_utc.tzinfo is None or inicio_utc.utcoffset() is None:
        raise ContratoPitchAPI("Inicio PitchAPI sin zona horaria")

    def marcador(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ContratoPitchAPI("Marcador PitchAPI inválido")
        return value

    score_home = marcador(match.get("score_home"))
    score_away = marcador(match.get("score_away"))
    if (score_home is None) != (score_away is None):
        raise ContratoPitchAPI("Marcador PitchAPI parcialmente ausente")
    try:
        return PartidoProveedor(
            fuente="PITCHAPI",
            evento_id=event_id,
            competicion_id=league_id,
            equipo_local_id=home_id,
            equipo_visitante_id=away_id,
            inicio_utc=inicio_utc,
            estado=match.get("status") if isinstance(match.get("status"), str) else "",
            goles_local=score_home,
            goles_visitante=score_away,
        )
    except TypeError:
        raise ContratoPitchAPI("Estado de partido PitchAPI inválido") from None
