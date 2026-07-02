from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED_MARKER_EVENTS = 27


def interval_stats(times: pd.Series) -> dict[str, float]:
    values = pd.to_numeric(times, errors="coerce").dropna().to_numpy()
    if len(values) < 2:
        return {
            "duplicate_timestamps": 0.0,
            "negative_time_jumps": 0.0,
            "irregular_interval_pct": float("nan"),
        }

    diffs = np.diff(values)
    positive = diffs[diffs > 0]
    if len(positive) == 0:
        irregular = float("nan")
    else:
        median = np.median(positive)
        irregular = float(np.mean(np.abs(positive - median) > median * 0.5)) if median > 0 else float("nan")

    return {
        "duplicate_timestamps": float(np.sum(diffs == 0)),
        "negative_time_jumps": float(np.sum(diffs < 0)),
        "irregular_interval_pct": irregular,
    }


def evaluate_standard_dir(standard_dir: Path, session_id: str = "") -> dict[str, object]:
    gaze_path = standard_dir / "standard_gaze.csv"
    video_path = standard_dir / "standard_video_timestamps.csv"
    marker_path = standard_dir / "standard_marker_events.csv"

    flags: list[str] = []
    gaze = pd.read_csv(gaze_path) if gaze_path.exists() else pd.DataFrame()
    video = pd.read_csv(video_path) if video_path.exists() else pd.DataFrame()
    marker = pd.read_csv(marker_path) if marker_path.exists() else pd.DataFrame()

    valid_rate = float(gaze["valid"].mean()) if "valid" in gaze and len(gaze) else float("nan")
    stats = interval_stats(gaze["time_s"]) if "time_s" in gaze else interval_stats(pd.Series(dtype=float))
    marker_events = int(len(marker))

    if gaze.empty:
        flags.append("missing_gaze")
    if np.isfinite(valid_rate) and valid_rate < 0.8:
        flags.append("low_valid_gaze_rate")
    if stats["duplicate_timestamps"] > 0:
        flags.append("duplicate_timestamps")
    if stats["negative_time_jumps"] > 0:
        flags.append("negative_time_jumps")
    if np.isfinite(stats["irregular_interval_pct"]) and stats["irregular_interval_pct"] > 0.2:
        flags.append("irregular_sampling")
    if video.empty:
        flags.append("missing_video_timestamps")
    if marker_events != EXPECTED_MARKER_EVENTS:
        flags.append("unexpected_marker_count")

    return {
        "session_id": session_id or standard_dir.name,
        "valid_rate": valid_rate,
        "duplicate_timestamps": int(stats["duplicate_timestamps"]),
        "negative_time_jumps": int(stats["negative_time_jumps"]),
        "irregular_interval_pct": stats["irregular_interval_pct"],
        "marker_events": marker_events,
        "quality_flags": ";".join(flags) if flags else "ok",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--standard-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/quality_report.csv"))
    args = parser.parse_args()
    result = evaluate_standard_dir(args.standard_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([result]).to_csv(args.output, index=False)
    args.output.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
