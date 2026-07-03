from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_importer import import_marker_csv


def test_missing_marker_file_returns_empty_standard_table():
    table = import_marker_csv(Path("missing.csv"))
    assert list(table.columns) == ["marker_start_s", "marker_end_s", "marker_id"]
    assert table.empty
