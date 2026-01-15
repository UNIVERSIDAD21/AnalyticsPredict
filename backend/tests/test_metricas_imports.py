from pathlib import Path
import sys
import importlib

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_importar_metricas_no_importa_db():
    sys.modules.pop("db", None)
    importlib.import_module("backtesting.metricas")

    assert "db" not in sys.modules
