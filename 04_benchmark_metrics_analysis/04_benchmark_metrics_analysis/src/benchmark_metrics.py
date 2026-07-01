from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def duration_s(times: pd.Series) -> float:
    values = pd.to_numeric(times, errors="coerce").dropna()
    if len(values) < 2:
        return float("nan")
    return float(values.max() - values.min())


def effective_sampling_hz(times: pd.Series) -> float:
    values = pd.to_numeric(times, errors="coerce").dropna()
    duration = duration_s(values)
    if len(values) < 2 or not np.isfinite(duration) or duration <= 0:
        return float("nan")
    return float((len(values) - 1) / duration)


def compute_metrics(standard_dir: Path, session_id: str = "") -> dict[str, object]:
    gaze_path = standard_dir / "standard_gaze.csv"
    marker_path = standard_dir / "standard_marker_events.csv"

    gaze = pd.read_csv(gaze_path) if gaze_path.exists() else pd.DataFrame()
    marker = pd.read_csv(marker_path) if marker_path.exists() else pd.DataFrame()

    if gaze.empty:
        return {
            "session_id": session_id or standard_dir.name,
            "gaze_samples": 0,
            "duration_s": float("nan"),
            "effective_sampling_hz": float("nan"),
            "valid_samples": 0,
            "invalid_samples": 0,
            "valid_rate": float("nan"),
            "gaze_dispersion_x": float("nan"),
            "gaze_dispersion_y": float("nan"),
            "marker_events": int(len(marker)),
        }

    valid = pd.to_numeric(gaze["valid"], errors="coerce").fillna(0).astype(int) == 1
    valid_gaze = gaze.loc[valid, ["gaze_x", "gaze_y"]].apply(pd.to_numeric, errors="coerce").dropna()
    valid_samples = int(valid.sum())
    total_samples = int(len(gaze))

    return {
        "session_id": session_id or standard_dir.name,
        "gaze_samples": total_samples,
        "duration_s": duration_s(gaze["time_s"]),
        "effective_sampling_hz": effective_sampling_hz(gaze["time_s"]),
        "valid_samples": valid_samples,
        "invalid_samples": total_samples - valid_samples,
        "valid_rate": valid_samples / total_samples if total_samples else float("nan"),
        "gaze_dispersion_x": float(valid_gaze["gaze_x"].std()) if len(valid_gaze) > 1 else float("nan"),
        "gaze_dispersion_y": float(valid_gaze["gaze_y"].std()) if len(valid_gaze) > 1 else float("nan"),
        "marker_events": int(len(marker)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--standard-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/benchmark_metrics.csv"))
    args = parser.parse_args()
    result = compute_metrics(args.standard_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([result]).to_csv(args.output, index=False)
    args.output.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
