from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


FIGURE_FILENAMES = (
    "sessions_by_date.png",
    "sampling_rate_by_session.png",
    "valid_rate_by_session.png",
    "quality_flags_summary.png",
)


def _column(df: pd.DataFrame, *names: str) -> str:
    for name in names:
        if name in df.columns:
            return name
    tried = ", ".join(names)
    available = ", ".join(df.columns.astype(str))
    raise KeyError(f"Missing expected column. Tried: {tried}. Available columns: {available}")


def _require_columns(df: pd.DataFrame) -> None:
    required = ("session_id", "date", "run_id")
    missing = [name for name in required if name not in df.columns]
    if missing:
        raise KeyError(f"Missing required column(s): {', '.join(missing)}")
    _column(df, "effective_sampling_hz", "gp3_effective_hz")
    _column(df, "valid_rate", "gp3_valid_rate")


def _prepare_sessions(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["date"] = prepared["date"].astype(str)
    prepared["run_id"] = prepared["run_id"].astype(str)
    prepared["session_short"] = prepared["date"].str[-5:] + "/" + prepared["run_id"]
    return prepared.sort_values(["date", "run_id"]).reset_index(drop=True)


def _quality_flag_counts(df: pd.DataFrame) -> pd.DataFrame:
    if "quality_flags" not in df.columns:
        return pd.DataFrame(columns=["flag", "count"])

    flags = (
        df["quality_flags"]
        .fillna("ok")
        .astype(str)
        .str.strip()
        .replace({"": "ok", "nan": "ok", "None": "ok"})
        .str.split(";")
    )
    exploded = df.assign(flag=flags).explode("flag")
    exploded["flag"] = exploded["flag"].astype(str).str.strip()
    exploded = exploded[~exploded["flag"].isin(["", "ok", "nan", "None"])]

    if exploded.empty:
        return pd.DataFrame(columns=["flag", "count"])

    return (
        exploded.groupby("flag", as_index=False)["session_id"]
        .count()
        .rename(columns={"session_id": "count"})
        .sort_values(["count", "flag"], ascending=[False, True])
    )


def style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 180,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
        }
    )


def save(path: Path) -> Path:
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def make_figures(metrics_csv: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    style()
    df = pd.read_csv(metrics_csv)
    _require_columns(df)

    outputs: list[Path] = []

    plt.figure(figsize=(7, 4))
    by_date = df.groupby("date", as_index=False)["session_id"].count()
    sns.barplot(data=by_date, x="date", y="session_id", color="#4C78A8")
    plt.title("Available sessions by collection date")
    plt.xlabel("Collection date")
    plt.ylabel("Session count")
    outputs.append(save(output_dir / "sessions_by_date.png"))

    rate_col = _column(df, "effective_sampling_hz", "gp3_effective_hz")
    valid_col = _column(df, "valid_rate", "gp3_valid_rate")
    ordered = _prepare_sessions(df)

    plt.figure(figsize=(9, 4.5))
    sns.scatterplot(data=ordered, x="session_short", y=rate_col, hue="date", s=55)
    plt.axhline(60, color="#E45756", linewidth=1.2, linestyle="--", label="60 Hz reference")
    plt.title("Effective sampling rate by session")
    plt.xlabel("Session")
    plt.ylabel("Effective Hz")
    plt.xticks(rotation=70, ha="right")
    outputs.append(save(output_dir / "sampling_rate_by_session.png"))

    plt.figure(figsize=(9, 4.5))
    sns.lineplot(data=ordered, x="session_short", y=valid_col, hue="date", marker="o")
    plt.ylim(0, 1.05)
    plt.title("Valid gaze sample rate by session")
    plt.xlabel("Session")
    plt.ylabel("Valid sample rate")
    plt.xticks(rotation=70, ha="right")
    outputs.append(save(output_dir / "valid_rate_by_session.png"))

    flag_counts = _quality_flag_counts(df)
    plt.figure(figsize=(8, 4.5))
    if flag_counts.empty:
        plt.text(0.5, 0.5, "No quality flags detected", ha="center", va="center", fontsize=14)
        plt.axis("off")
    else:
        sns.barplot(data=flag_counts, y="flag", x="count", color="#F58518")
        plt.title("Automated quality flags across sessions")
        plt.xlabel("Session count")
        plt.ylabel("Quality flag")
    outputs.append(save(output_dir / "quality_flags_summary.png"))

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate OpenET 2 visualisation report figures.")
    parser.add_argument("--metrics", type=Path, required=True, help="Path to the integrated metrics CSV.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/figures"))
    args = parser.parse_args()
    outputs = make_figures(args.metrics, args.output_dir)
    print(f"Wrote {len(outputs)} figures to {args.output_dir}")


if __name__ == "__main__":
    main()
