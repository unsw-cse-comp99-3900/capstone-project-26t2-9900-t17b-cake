from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quality_checks import interval_stats


def test_interval_stats_counts_duplicate_timestamps():
    stats = interval_stats(pd.Series([1.0, 1.0, 1.1]))
    assert stats["duplicate_timestamps"] == 1
