from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from benchmark_metrics import duration_s, effective_sampling_hz


def test_effective_sampling_hz_for_simple_series():
    times = pd.Series([0.0, 0.5, 1.0])
    assert duration_s(times) == 1.0
    assert effective_sampling_hz(times) == 2.0
