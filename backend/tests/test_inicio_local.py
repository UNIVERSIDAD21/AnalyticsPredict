"""Arranque en frío simulado: sin servidores, procesos, red o datos reales."""
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace


def test_arranque_frio_puede_superar_quince_segundos_sin_fallar(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('inicio_frio', Path(__file__).resolve().parents[2] / 'scripts/iniciar_local.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    build = tmp_path / 'frontend/dist'; build.mkdir(parents=True)
    (build / 'index.html').write_text('<html>prueba</html>')
    reloj = {'t': 0.}
    monkeypatch.setattr(mod, 'RAIZ', tmp_path)
    monkeypatch.setattr(mod.time, 'monotonic', lambda: reloj['t'])
    monkeypatch.setattr(mod.time, 'sleep', lambda n: reloj.update(t=reloj['t'] + n))
    monkeypatch.setattr(mod, 'comprobar_puertos', lambda _: None)
    monkeypatch.setattr(mod, 'cerrar_backend', lambda _: None)
    monkeypatch.setattr(mod.subprocess, 'Popen', lambda *a, **k: SimpleNamespace(poll=lambda: None))
    servidor = SimpleNamespace(serve_forever=lambda: None, shutdown=lambda: None, server_close=lambda: None)
    monkeypatch.setattr(mod, 'ThreadingHTTPServer', lambda *a, **k: servidor)

    class Respuesta(io.BytesIO):
        status = 200

    def consultar(url, **_):
        if reloj['t'] < 20: raise OSError('Importación en frío aún en curso')
        return Respuesta(json.dumps({'modelos': {'nba': {'disponible': True}}}).encode())

    monkeypatch.setattr(mod, 'urlopen', consultar)
    assert mod.main(['--sin-abrir', '--comprobar']) == 0
    assert reloj['t'] >= 20
