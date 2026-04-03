from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.walkforward_scorecard_futbol import generar_ventanas


def test_generar_ventanas_sin_leakage_y_ordenadas():
    fin = datetime(2026, 4, 1, tzinfo=timezone.utc)
    ventanas = generar_ventanas(fin, train_days=180, cal_days=60, eval_days=30, n_windows=3)

    assert len(ventanas) == 3
    for w in ventanas:
        assert w.inicio_train < w.fin_train <= w.inicio_cal < w.fin_cal <= w.inicio_eval < w.fin_eval

    assert ventanas[0].inicio_eval < ventanas[1].inicio_eval < ventanas[2].inicio_eval
