from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from visualise_results import FIGURE_FILENAMES, _column, _quality_flag_counts, make_figures


def _sample_metrics() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "session_id": ["s1", "s2", "s3"],
            "date": ["2025_04_11", "2025_04_11", "2025_04_12"],
            "run_id": [1, 2, 1],
            "effective_sampling_hz": [59.8, 60.2, 52.0],
            "valid_rate": [0.95, 0.88, 0.62],
            "quality_flags": ["ok", "", "low_valid_rate;low_sampling_rate"],
        }
    )


def test_column_finds_alias() -> None:
    df = pd.DataFrame({"gp3_valid_rate": [1.0]})
    assert _column(df, "valid_rate", "gp3_valid_rate") == "gp3_valid_rate"


def test_make_figures_writes_expected_png_files(tmp_path: Path) -> None:
    metrics_csv = tmp_path / "quality_metrics.csv"
    output_dir = tmp_path / "figures"
    _sample_metrics().to_csv(metrics_csv, index=False)

    outputs = make_figures(metrics_csv, output_dir)

    assert [path.name for path in outputs] == list(FIGURE_FILENAMES)
    for filename in FIGURE_FILENAMES:
        figure_path = output_dir / filename
        assert figure_path.exists()
        assert figure_path.stat().st_size > 0


def test_make_figures_accepts_gp3_column_aliases(tmp_path: Path) -> None:
    metrics = _sample_metrics().rename(
        columns={
            "effective_sampling_hz": "gp3_effective_hz",
            "valid_rate": "gp3_valid_rate",
        }
    )
    metrics_csv = tmp_path / "quality_metrics.csv"
    metrics.to_csv(metrics_csv, index=False)

    outputs = make_figures(metrics_csv, tmp_path / "figures")

    assert len(outputs) == 4


def test_quality_flag_counts_ignores_empty_and_ok_values() -> None:
    counts = _quality_flag_counts(_sample_metrics())

    assert counts.to_dict("records") == [
        {"flag": "low_sampling_rate", "count": 1},
        {"flag": "low_valid_rate", "count": 1},
    ]


def test_make_figures_reports_missing_required_columns(tmp_path: Path) -> None:
    metrics_csv = tmp_path / "bad_metrics.csv"
    pd.DataFrame({"session_id": ["s1"]}).to_csv(metrics_csv, index=False)

    with pytest.raises(KeyError, match="Missing required column"):
        make_figures(metrics_csv, tmp_path / "figures")
