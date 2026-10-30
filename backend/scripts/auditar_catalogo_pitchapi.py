"""Auditor de solo lectura para catálogo y fixtures PitchAPI.

La API key se obtiene exclusivamente del entorno protegido del proceso. El
script nunca lee .env, imprime la clave ni conecta con PostgreSQL. Ejemplo
(desde `backend/`, con la clave inyectada por el entorno protegido):
  python -m scripts.auditar_catalogo_pitchapi \
      --out /ruta/privada/pitchapi.json --league-season l_4Kd0Wq=2024/2025

No sobrescribe la evidencia de salida. No llama endpoints de estadísticas ni
propone enlaces automáticos; esos requieren validar primero catálogo y mapeos.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from servicios.proveedor_pitchapi import ClientePitchAPI
from servicios.resolucion_multifuente_futbol import sha256_json


def _guardar_sin_sobrescribir(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    contenido = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temporal = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())
        # link() crea el destino de forma exclusiva; no sustituye evidencia previa.
        os.link(temporal, path)
    finally:
        try:
            os.unlink(temporal)
        except FileNotFoundError:
            pass


def _parsear_league_season(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Use ID_LIGA=TEMPORADA")
    league_id, season = value.split("=", 1)
    try:
        ClientePitchAPI.validar_id(league_id)
    except ValueError:
        raise argparse.ArgumentTypeError("ID de liga PitchAPI inválido") from None
    if not season.strip() or len(season) > 16:
        raise argparse.ArgumentTypeError("Temporada PitchAPI inválida")
    return league_id, season


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Destino externo y nuevo para evidencia JSON")
    parser.add_argument(
        "--league-season",
        action="append",
        type=_parsear_league_season,
        default=[],
        metavar="ID=TEMPORADA",
        help="Pedir partidos para una liga/temporada exacta; se puede repetir",
    )
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    destination = args.out.expanduser().resolve()
    if destination == repo_root or repo_root in destination.parents:
        parser.error("El destino de evidencia debe permanecer fuera del repositorio")
    api_key = os.environ.get("PITCHAPI_API_KEY", "")
    if not api_key.strip():
        parser.error("PITCHAPI_API_KEY no está disponible en el entorno protegido")

    try:
        with ClientePitchAPI(api_key) as cliente:
            ligas = cliente.listar_ligas()
            ids_liga = {liga.get("id") for liga in ligas}
            seleccion = []
            for league_id, season in args.league_season:
                if league_id not in ids_liga:
                    raise ValueError("Liga solicitada no aparece en el catálogo autenticado")
                partidos = cliente.listar_partidos_liga(league_id, season=season)
                seleccion.append(
                    {"league_id": league_id, "season": season, "match_count": len(partidos), "matches": partidos}
                )
    except Exception as exc:
        # Excepciones de red/HTTP del cliente están sanitizadas. No se publica su
        # cadena original para evitar que un adaptador futuro exponga headers.
        if isinstance(exc, (ValueError, argparse.ArgumentError)):
            parser.error(str(exc))
        parser.error(f"Auditoría PitchAPI falló ({type(exc).__name__})")

    evidencia: dict[str, Any] = {
        "schema": "PITCHAPI_CATALOG_SNAPSHOT_V1",
        "source": "PitchAPI",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "league_count": len(ligas),
        "leagues": [
            {
                "id": liga.get("id"),
                "name": liga.get("name"),
                "country_code": liga.get("country_code"),
                "seasons": liga.get("seasons", []),
            }
            for liga in ligas
        ],
        "requested_league_seasons": seleccion,
    }
    evidencia["sha256_content"] = sha256_json(evidencia)
    try:
        _guardar_sin_sobrescribir(args.out, evidencia)
    except FileExistsError:
        parser.error("El archivo destino ya existe; se conserva sin cambios")
    except OSError as exc:
        parser.error(f"No se pudo guardar evidencia ({type(exc).__name__})")
    print(
        json.dumps(
            {
                "output": str(args.out.expanduser().resolve()),
                "league_count": len(ligas),
                "requested_seasons": len(seleccion),
                "sha256_content": evidencia["sha256_content"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
