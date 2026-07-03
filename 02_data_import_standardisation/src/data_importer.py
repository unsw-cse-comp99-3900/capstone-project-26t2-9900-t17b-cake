from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _first_matching_column(columns: list[str], candidates: set[str]) -> str | None:
    normalised = {col.lower().replace(" ", "").replace("_", ""): col for col in columns}
    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalised:
            return normalised[key]
    return None


def import_gp3hd_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, encoding="utf-8-sig")
    raw = raw.rename(columns={col: col.strip() for col in raw.columns})

    time_col = _first_matching_column(list(raw.columns), {"Time_s", "Time (ms)", "Time"})
    if time_col is None:
        raise ValueError(f"No time column found in {path}")

    standard = pd.DataFrame(
        {
            "time_s": pd.to_numeric(raw[time_col], errors="coerce"),
            "gaze_x": pd.to_numeric(raw.get("FPOGX"), errors="coerce"),
            "gaze_y": pd.to_numeric(raw.get("FPOGY"), errors="coerce"),
            "valid": pd.to_numeric(raw.get("FPOGV"), errors="coerce").fillna(0).astype(int),
            "source_device": "GP3HD",
            "raw_cx": pd.to_numeric(raw.get("CX"), errors="coerce"),
            "raw_cy": pd.to_numeric(raw.get("CY"), errors="coerce"),
        }
    )
    return standard


def import_video_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, encoding="utf-8-sig")
    time_col = _first_matching_column(list(raw.columns), {"Time_s", "Time (ms)", "Time"})
    frame_col = _first_matching_column(list(raw.columns), {"FrameID", "Frame ID"})
    if time_col is None:
        raise ValueError(f"No time column found in {path}")

    return pd.DataFrame(
        {
            "frame_id": pd.to_numeric(raw[frame_col], errors="coerce") if frame_col else range(len(raw)),
            "time_s": pd.to_numeric(raw[time_col], errors="coerce"),
        }
    )


def import_marker_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["marker_start_s", "marker_end_s", "marker_id"])
    raw = pd.read_csv(path, header=None, encoding="utf-8-sig")
    if raw.empty:
        return pd.DataFrame(columns=["marker_start_s", "marker_end_s", "marker_id"])
    return pd.DataFrame(
        {
            "marker_start_s": pd.to_numeric(raw.iloc[:, 0], errors="coerce"),
            "marker_end_s": pd.to_numeric(raw.iloc[:, 1], errors="coerce"),
            "marker_id": "accuracy_target",
        }
    )


def standardise_session(session_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    import_gp3hd_csv(session_path / "GP3HD_data.csv").to_csv(output_dir / "standard_gaze.csv", index=False)
    import_video_csv(session_path / "Video_data.csv").to_csv(
        output_dir / "standard_video_timestamps.csv", index=False
    )
    import_marker_csv(session_path / "acc_marker_external.csv").to_csv(
        output_dir / "standard_marker_events.csv", index=False
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    standardise_session(args.session_path, args.output_dir)
    print(f"Wrote standardised tables to {args.output_dir}")


if __name__ == "__main__":
    main()
