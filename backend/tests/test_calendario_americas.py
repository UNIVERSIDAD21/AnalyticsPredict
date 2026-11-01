from datetime import date
from pathlib import Path
import json

from scripts import preparar_calendario_americas as cal
from ingesta_futbol_americas import cargar_lote, NUMERICOS
from test_ingesta_futbol_americas import fila


def test_calendario_crea_archivo_antes_del_get_y_replay_no_inventa_resultados(tmp_path, monkeypatch):
    r = fila(codigo_liga="usa.1", temporada=2026, estado="PROGRAMADO", final_completo=False,
             estadisticas_completas=False, inicio_utc="2026-10-27T20:00:00+00:00", inicio_colombia="2026-10-27T15:00:00-05:00",
             incidencias=[], campos_faltantes=[])
    for lado in ("local", "visitante"):
        for f in NUMERICOS: r[lado + "_" + f] = None
    class Cliente:
        def __init__(self, archivo, **kwargs):
            self.archivo = archivo
            self.contadores = {"requests": 0, "cache_hits": 0, "reintentos": 0}
        def obtener(self, endpoint, mes, **kwargs):
            assert self.archivo.root.is_dir()  # regresión del error de primer GET
            self.contadores["cache_hits"] += 1
            return {}, {"sha256": "a" * 64, "observado_utc": "2026-10-26T16:00:00+00:00", "url": "https://site.api.espn.com/scoreboard"}
        def close(self): pass
    monkeypatch.setattr(cal, "ClienteESPN", Cliente)
    monkeypatch.setattr(cal, "eventos_scoreboard", lambda *args: [{"date": r["inicio_utc"], "id": "1234"}])
    monkeypatch.setattr(cal, "normalizar", lambda *args: dict(r))
    run = cal.ejecutar(tmp_path / "salida", tmp_path / "control", date(2026,10,26), date(2026,10,28), ["usa.1"], offline=True)
    lote = cargar_lote(run / "reporte.json")
    assert len(lote["filas"]) == 1 and lote["filas"][0]["local_goles"] is None
    assert lote["resumen"]["contadores_http"] == {"requests": 0, "cache_hits": 1, "reintentos": 0}


def test_401_403_o_circuit_breaker_no_se_evita_y_conserva_pendientes(tmp_path, monkeypatch):
    class Cliente:
        def __init__(self, *args, **kwargs): self.contadores = {"requests": 1, "cache_hits": 0, "reintentos": 0}
        def obtener(self, *args, **kwargs): raise cal.FuenteError("HTTP 403: fuente detenida")
        def close(self): pass
    monkeypatch.setattr(cal, "ClienteESPN", Cliente)
    run = cal.ejecutar(tmp_path / "salida", tmp_path / "control", date(2026,10,26), date(2026,12,26), ["usa.1"])
    r = json.loads((run / "reporte.json").read_text())
    assert r["estado"] == "INCOMPLETO" and r["ventanas_completadas"] == 0
    assert r["consultas_pendientes"] == 1 and len(r["ventanas_pendientes"]) == 3
    assert not cargar_lote(run / "reporte.json")["filas"]
