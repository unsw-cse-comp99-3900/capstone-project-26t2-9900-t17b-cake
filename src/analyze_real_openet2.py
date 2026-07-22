"""CLIMB meeting revision: analyse the real OpenET2 Demo B CSV data.

Key decisions implemented here:

* each row of acc_marker_external.csv is one marker onset-offset window;
* the onset is shifted forward by an explicit human-response delay;
* every delay is rendered as its own full-size image and labelled in seconds;
* target IDs 2 and 3 use the corrected mapping agreed in the 2026-07-17 meeting;
* ellipses cover 95% of the observed data, not the confidence interval of a mean;
* condition, target-condition, and recording QA figures are individual files.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, FancyArrowPatch
import numpy as np
import pandas as pd


FOV_X_DEG = 60.0
FOV_Y_DEG = 33.75
TARGET_SEQUENCE = [
    7, 2, 1, 5, 9, 3, 4, 6, 8,
    7, 8, 2, 5, 6, 4, 3, 9, 1,
    6, 2, 1, 4, 5, 8, 9, 3, 7,
]

# Corrected after the meeting: old figures had target IDs 2 and 3 swapped.
TARGETS_NORM = {
    1: (0.15, 0.15),
    2: (0.85, 0.15),
    3: (0.33, 0.33),
    4: (0.66, 0.33),
    5: (0.50, 0.50),
    6: (0.33, 0.66),
    7: (0.66, 0.66),
    8: (0.15, 0.85),
    9: (0.85, 0.85),
}

CONDITION_ORDER = ["Calib & Acc", "Acc 10min", "Acc 60min"]
CONDITION_MARKERS = {"Calib & Acc": "o", "Acc 10min": "^", "Acc 60min": "s"}
CONDITION_LABELS = {
    "Calib & Acc": "Calibration & accuracy",
    "Acc 10min": "Accuracy after 10 min",
    "Acc 60min": "Accuracy after 60 min",
}

# Recording_info.csv is missing for this one session. The dataset otherwise has
# one complete calibration/10min/60min triplet per participant; CL98 is the only
# subject missing a 60min row, so the repair is explicit and auditable.
INFERRED_METADATA = {
    ("2025_04_11", "007"): {"subject_id": "CL98", "condition": "Acc 60min"},
}

RECORDING_KEYS = ["date", "run_id", "subject_id", "condition"]
WINDOW_KEYS = RECORDING_KEYS + [
    "window_index",
    "target_id",
    "onset_s",
    "offset_s",
    "target_x_deg",
    "target_y_deg",
]


@dataclass(frozen=True)
class EllipseStats:
    center_x_deg: float
    center_y_deg: float
    semi_major_deg: float
    semi_minor_deg: float
    angle_deg: float
    area_deg2: float
    empirical_coverage: float
    n_points: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--delays-s",
        default="0,0.05,0.10:0.20:0.01",
        help="Seconds; supports comma values and inclusive start:stop:step ranges.",
    )
    parser.add_argument("--coverage", type=float, default=0.95)
    parser.add_argument("--min-window-samples", type=int, default=5)
    parser.add_argument("--tie-tolerance", type=float, default=0.02)
    return parser.parse_args()


def parse_delay_spec(spec: str) -> list[float]:
    microseconds: set[int] = set()
    for token in (part.strip() for part in spec.split(",")):
        if not token:
            continue
        if ":" not in token:
            microseconds.add(round(float(token) * 1_000_000))
            continue
        values = [float(value) for value in token.split(":")]
        if len(values) != 3:
            raise ValueError(f"Invalid delay range: {token!r}")
        start, stop, step = values
        if start < 0 or stop < start or step <= 0:
            raise ValueError(f"Invalid delay range: {token!r}")
        start_us = round(start * 1_000_000)
        stop_us = round(stop * 1_000_000)
        step_us = round(step * 1_000_000)
        microseconds.update(range(start_us, stop_us + 1, step_us))
    if not microseconds or min(microseconds) < 0:
        raise ValueError("At least one non-negative delay is required.")
    return [value / 1_000_000 for value in sorted(microseconds)]


def delay_label(delay_s: float) -> str:
    return f"{delay_s:.4f} s"


def delay_stem(delay_s: float) -> str:
    return f"delay_{delay_s:.4f}s"


def safe_name(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_") or "unknown"


def ordered_conditions(values: Iterable[str]) -> list[str]:
    found = list(dict.fromkeys(str(value) for value in values))
    first = [value for value in CONDITION_ORDER if value in found]
    return first + sorted(value for value in found if value not in first)


def norm_to_deg(x: np.ndarray | float, y: np.ndarray | float) -> tuple[np.ndarray, np.ndarray]:
    return (np.asarray(x) - 0.5) * FOV_X_DEG, -(np.asarray(y) - 0.5) * FOV_Y_DEG


def target_table() -> pd.DataFrame:
    rows = []
    for target_id, (x_norm, y_norm) in TARGETS_NORM.items():
        x_deg, y_deg = norm_to_deg(x_norm, y_norm)
        rows.append(
            {
                "target_id": target_id,
                "target_x_norm": x_norm,
                "target_y_norm": y_norm,
                "target_x_deg": float(x_deg),
                "target_y_deg": float(y_deg),
            }
        )
    return pd.DataFrame(rows)


def read_recording_info(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path, header=None, names=["key", "value"], dtype=str)
    return {
        str(key).strip(): str(value).strip()
        for key, value in zip(frame["key"], frame["value"])
    }


def read_markers(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=["onset_s", "offset_s"])
    frame = pd.read_csv(path, header=None, names=["onset_s", "offset_s"])
    frame[["onset_s", "offset_s"]] = frame[["onset_s", "offset_s"]].apply(
        pd.to_numeric, errors="coerce"
    )
    frame = frame.dropna().reset_index(drop=True)
    frame = frame[frame["offset_s"] > frame["onset_s"]].reset_index(drop=True)
    frame["window_index"] = np.arange(1, len(frame) + 1)
    return frame


def read_gaze(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    frame = pd.read_csv(path)
    required = ["Time_s", "FPOGX", "FPOGY", "FPOGV"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    frame[required] = frame[required].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=required)
    frame = frame[
        frame["FPOGV"].eq(1)
        & frame["FPOGX"].between(0, 1)
        & frame["FPOGY"].between(0, 1)
    ].copy()
    gx, gy = norm_to_deg(frame["FPOGX"].to_numpy(), frame["FPOGY"].to_numpy())
    frame["gaze_x_deg"] = gx
    frame["gaze_y_deg"] = gy
    return frame


def find_sessions(data_root: Path) -> list[Path]:
    return sorted(
        session
        for session in data_root.glob("*/*")
        if session.is_dir()
        and (session / "GP3HD_data.csv").exists()
        and (session / "acc_marker_external.csv").exists()
    )


def collect_assigned_samples(
    data_root: Path, targets: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_lookup = targets.set_index("target_id")
    assigned_parts: list[pd.DataFrame] = []
    session_rows: list[dict[str, object]] = []
    for session_path in find_sessions(data_root):
        date = session_path.parent.name
        run_id = session_path.name
        info = read_recording_info(session_path / "Recording_info.csv")
        inferred = INFERRED_METADATA.get((date, run_id), {})
        subject_id = info.get("SubjectID") or inferred.get("subject_id", "unknown")
        condition = info.get("TestID") or inferred.get("condition", "unknown")
        metadata_source = "Recording_info.csv" if info.get("TestID") else "inferred_missing_recording_info"
        markers = read_markers(session_path / "acc_marker_external.csv")
        gaze = read_gaze(session_path / "GP3HD_data.csv")
        usable = min(len(markers), len(TARGET_SEQUENCE))
        retained_in_windows = 0
        for zero_index in range(usable):
            marker = markers.iloc[zero_index]
            target_id = TARGET_SEQUENCE[zero_index]
            target = target_lookup.loc[target_id]
            window = gaze[
                gaze["Time_s"].between(marker["onset_s"], marker["offset_s"], inclusive="both")
            ].copy()
            if window.empty:
                continue
            window["date"] = date
            window["run_id"] = run_id
            window["subject_id"] = subject_id
            window["condition"] = condition
            window["window_index"] = zero_index + 1
            window["target_id"] = target_id
            window["onset_s"] = float(marker["onset_s"])
            window["offset_s"] = float(marker["offset_s"])
            window["target_x_deg"] = float(target["target_x_deg"])
            window["target_y_deg"] = float(target["target_y_deg"])
            window["relative_time_s"] = window["Time_s"] - float(marker["onset_s"])
            assigned_parts.append(
                window[
                    WINDOW_KEYS
                    + ["Time_s", "relative_time_s", "gaze_x_deg", "gaze_y_deg"]
                ]
            )
            retained_in_windows += len(window)
        session_rows.append(
            {
                "date": date,
                "run_id": run_id,
                "subject_id": subject_id,
                "condition": condition,
                "metadata_source": metadata_source,
                "marker_rows": len(markers),
                "usable_marker_rows": usable,
                "valid_gaze_samples_in_windows": retained_in_windows,
                "calibration_avg_error": info.get("Calibration avg error", ""),
                "calibration_valid_points": info.get("Calibration valid points", ""),
            }
        )
    if not assigned_parts:
        raise RuntimeError(f"No usable gaze samples found under {data_root}")
    assigned = pd.concat(assigned_parts, ignore_index=True)
    inventory = pd.DataFrame(session_rows).sort_values(["date", "run_id"])
    return assigned, inventory


def ellipse_stats(points: np.ndarray, coverage: float) -> EllipseStats | None:
    points = np.asarray(points, dtype=float)
    points = points[np.isfinite(points).all(axis=1)]
    if len(points) < 3:
        return None
    center = points.mean(axis=0)
    covariance = np.cov(points, rowvar=False)
    if covariance.shape != (2, 2) or not np.isfinite(covariance).all():
        return None
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.maximum(eigenvalues[order], 1e-10)
    eigenvectors = eigenvectors[:, order]
    projected = (points - center) @ eigenvectors
    distances_sq = np.sum(projected**2 / eigenvalues, axis=1)
    scale_sq = float(np.quantile(distances_sq, coverage, method="higher"))
    semi_axes = np.sqrt(eigenvalues * max(scale_sq, 0.0))
    angle_deg = math.degrees(math.atan2(eigenvectors[1, 0], eigenvectors[0, 0]))
    empirical = float(np.mean(distances_sq <= scale_sq + 1e-12))
    return EllipseStats(
        center_x_deg=float(center[0]),
        center_y_deg=float(center[1]),
        semi_major_deg=float(semi_axes[0]),
        semi_minor_deg=float(semi_axes[1]),
        angle_deg=float(angle_deg),
        area_deg2=float(math.pi * semi_axes[0] * semi_axes[1]),
        empirical_coverage=empirical,
        n_points=int(len(points)),
    )


def means_for_delay(
    assigned: pd.DataFrame, delay_s: float, min_window_samples: int
) -> pd.DataFrame:
    kept = assigned[assigned["relative_time_s"] >= delay_s]
    means = (
        kept.groupby(WINDOW_KEYS, sort=False, as_index=False)
        .agg(
            gaze_x_deg=("gaze_x_deg", "mean"),
            gaze_y_deg=("gaze_y_deg", "mean"),
            valid_samples=("gaze_x_deg", "size"),
        )
    )
    means = means[means["valid_samples"] >= min_window_samples].copy()
    means["delay_s"] = delay_s
    means["delay_ms"] = round(delay_s * 1000)
    means["target_error_deg"] = np.hypot(
        means["gaze_x_deg"] - means["target_x_deg"],
        means["gaze_y_deg"] - means["target_y_deg"],
    )
    return means


def evaluate_delay(means: pd.DataFrame, coverage: float) -> dict[str, float | int]:
    radii = []
    for _, group in means.groupby(["condition", "target_id"], sort=False):
        stats = ellipse_stats(group[["gaze_x_deg", "gaze_y_deg"]].to_numpy(), coverage)
        if stats is not None:
            radii.append(math.sqrt(stats.area_deg2 / math.pi))
    median_error = float(means["target_error_deg"].median())
    median_radius = float(np.median(radii)) if radii else float("nan")
    return {
        "delay_s": float(means["delay_s"].iloc[0]),
        "delay_ms": int(means["delay_ms"].iloc[0]),
        "valid_windows": int(len(means)),
        "valid_samples": int(means["valid_samples"].sum()),
        "median_target_error_deg": median_error,
        "median_ellipse_equivalent_radius_deg": median_radius,
        "composite_score_deg": median_error + median_radius,
    }


def choose_delay(metrics: pd.DataFrame, tie_tolerance: float) -> tuple[float, float, float]:
    usable = metrics[np.isfinite(metrics["composite_score_deg"])].copy()
    if usable.empty:
        raise RuntimeError("No delay produced a usable score.")
    best = float(usable["composite_score_deg"].min())
    allowance = max(abs(best) * tie_tolerance, 0.01)
    eligible = usable[usable["composite_score_deg"] <= best + allowance]
    return float(eligible["delay_s"].min()), best, allowance


def target_colors() -> dict[int, object]:
    # A colour-blind-friendlier set with enough contrast on a white background.
    palette = [
        "#3B82F6", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6",
        "#06B6D4", "#EC4899", "#64748B", "#84CC16",
    ]
    return {
        target_id: palette[(target_id - 1) % len(palette)]
        for target_id in TARGETS_NORM
    }


def style_plots() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 240,
            "font.family": "DejaVu Sans",
            "font.size": 14,
            "figure.facecolor": "white",
            "axes.facecolor": "#FBFCFE",
            "axes.edgecolor": "#94A3B8",
            "axes.titlecolor": "#0F172A",
            "axes.labelcolor": "#334155",
            "axes.titlesize": 20,
            "axes.titleweight": "semibold",
            "axes.labelsize": 15,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "xtick.color": "#475569",
            "ytick.color": "#475569",
            "legend.fontsize": 11,
            "legend.frameon": True,
            "legend.framealpha": 0.94,
            "legend.facecolor": "white",
            "legend.edgecolor": "#CBD5E1",
            "axes.linewidth": 1.0,
            "grid.color": "#CBD5E1",
            "grid.alpha": 0.45,
            "grid.linewidth": 0.8,
        }
    )


def save_figure(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        path,
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.18,
    )
    plt.close(figure)


def draw_ellipse(
    axis: plt.Axes,
    stats: EllipseStats,
    color: object,
    linewidth: float = 2.2,
    alpha: float = 0.95,
) -> None:
    axis.add_patch(
        Ellipse(
            (stats.center_x_deg, stats.center_y_deg),
            width=2 * stats.semi_major_deg,
            height=2 * stats.semi_minor_deg,
            angle=stats.angle_deg,
            facecolor="none",
            edgecolor=color,
            linewidth=linewidth,
            linestyle="--",
            alpha=alpha,
            zorder=6,
        )
    )


def draw_targets(axis: plt.Axes, targets: pd.DataFrame, annotate: bool = True) -> None:
    axis.scatter(
        targets["target_x_deg"],
        targets["target_y_deg"],
        s=300,
        color="white",
        edgecolors="#CBD5E1",
        linewidths=1.0,
        zorder=1,
    )
    axis.scatter(
        targets["target_x_deg"],
        targets["target_y_deg"],
        s=150,
        marker="x",
        color="#168B36",
        linewidths=3.0,
        zorder=8,
    )
    if annotate:
        for row in targets.itertuples():
            axis.text(
                row.target_x_deg,
                row.target_y_deg + 1.00,
                f"T{row.target_id}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
                color="#166534",
                bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
                zorder=9,
            )


def apply_full_screen_axes(axis: plt.Axes) -> None:
    axis.set_xlim(-32, 32)
    axis.set_ylim(-19, 19)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("Gaze X in assumed screen-angle grid (deg)")
    axis.set_ylabel("Gaze Y in assumed screen-angle grid (deg)")
    axis.axhline(0, color="#94A3B8", linewidth=1.0, zorder=0)
    axis.axvline(0, color="#94A3B8", linewidth=1.0, zorder=0)
    axis.grid(True)
    axis.set_axisbelow(True)


def condition_handles() -> list[Line2D]:
    handles = []
    for condition in CONDITION_ORDER:
        handles.append(
            Line2D(
                [0],
                [0],
                marker=CONDITION_MARKERS[condition],
                color="black",
                markerfacecolor="none" if condition == "Calib & Acc" else "black",
                markeredgewidth=1.8,
                markersize=11,
                linestyle="none",
                label=CONDITION_LABELS[condition],
            )
        )
    return handles


def plot_target_layout(targets: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(14, 8.5), constrained_layout=True)
    positions = {
        int(row.target_id): np.array([row.target_x_deg, row.target_y_deg])
        for row in targets.itertuples()
    }
    for index, (start_id, end_id) in enumerate(
        zip(TARGET_SEQUENCE[:-1], TARGET_SEQUENCE[1:]), start=1
    ):
        start = positions[start_id]
        end = positions[end_id]
        axis.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=15,
                linewidth=2.2 if index <= 9 else 1.3,
                color="#c94c4c",
                alpha=0.42 if index <= 9 else 0.18,
                zorder=0,
            )
        )
    draw_targets(axis, targets, annotate=True)
    apply_full_screen_axes(axis)
    axis.set_title(
        "Corrected 9-target layout and 27 onset–offset marker windows\n"
        "Target 2 = top-right; target 3 = inner top-left; each target appears 3 times",
        pad=20,
    )
    save_figure(figure, path)


def plot_delay_step(
    means: pd.DataFrame,
    targets: pd.DataFrame,
    delay_s: float,
    coverage: float,
    metric: dict[str, float | int],
    selected: bool,
    path: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(14, 8.5), constrained_layout=True)
    colors = target_colors()
    draw_targets(axis, targets, annotate=True)
    for condition in ordered_conditions(means["condition"].unique()):
        for target_id, group in means[means["condition"] == condition].groupby("target_id"):
            axis.scatter(
                group["gaze_x_deg"],
                group["gaze_y_deg"],
                s=48,
                marker=CONDITION_MARKERS.get(condition, "o"),
                facecolors="none" if condition == "Calib & Acc" else colors[int(target_id)],
                edgecolors=colors[int(target_id)],
                linewidths=1.2,
                alpha=0.76,
                zorder=4,
            )
    apply_full_screen_axes(axis)
    selected_text = " — SELECTED" if selected else ""
    axis.set_title(
        f"Onset delay = {delay_s:.4f} s ({delay_s * 1000:.0f} ms){selected_text}\n"
        f"valid windows = {int(metric['valid_windows'])}; "
        f"median target error = {float(metric['median_target_error_deg']):.2f} deg; "
        f"median 95% spread radius = {float(metric['median_ellipse_equivalent_radius_deg']):.2f} deg\n"
        "Process view: large targets + window means; ellipses are in separate condition/target files",
        pad=18,
    )
    axis.legend(handles=condition_handles(), loc="lower center", ncol=3, frameon=True)
    save_figure(figure, path)


def plot_metric(
    metrics: pd.DataFrame,
    selected_delay_s: float,
    column: str,
    ylabel: str,
    title: str,
    path: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(12.5, 7.2), constrained_layout=True)
    axis.plot(
        metrics["delay_s"],
        metrics[column],
        color="#24588d",
        marker="o",
        linewidth=3.0,
        markersize=8,
    )
    selected_row = metrics[np.isclose(metrics["delay_s"], selected_delay_s)].iloc[0]
    axis.axvline(selected_delay_s, color="#c63f3f", linestyle="--", linewidth=2.5)
    axis.scatter(
        [selected_delay_s],
        [selected_row[column]],
        s=180,
        color="#c63f3f",
        zorder=5,
        label=f"selected {selected_delay_s:.4f} s",
    )
    axis.set_xticks(metrics["delay_s"])
    axis.set_xticklabels([f"{value:.2f}" for value in metrics["delay_s"]], rotation=45)
    axis.set_xlabel("Onset delay (s)")
    axis.set_ylabel(ylabel)
    axis.set_title(title, pad=18)
    axis.grid(alpha=0.24, linewidth=1.0)
    axis.legend(frameon=False)
    save_figure(figure, path)


def plot_condition_summary(
    means: pd.DataFrame,
    targets: pd.DataFrame,
    condition: str,
    delay_s: float,
    coverage: float,
    path: Path,
) -> None:
    subset = means[means["condition"] == condition]
    figure, axis = plt.subplots(figsize=(14, 8.5), constrained_layout=True)
    colors = target_colors()
    draw_targets(axis, targets, annotate=True)
    for target_id, group in subset.groupby("target_id"):
        color = colors[int(target_id)]
        axis.scatter(
            group["gaze_x_deg"],
            group["gaze_y_deg"],
            s=70,
            marker=CONDITION_MARKERS.get(condition, "o"),
            facecolors="none" if condition == "Calib & Acc" else color,
            edgecolors=color,
            linewidths=1.5,
            alpha=0.80,
            zorder=4,
        )
        stats = ellipse_stats(group[["gaze_x_deg", "gaze_y_deg"]].to_numpy(), coverage)
        if stats is not None:
            draw_ellipse(axis, stats, color, linewidth=3.2)
            axis.scatter(
                [stats.center_x_deg],
                [stats.center_y_deg],
                marker="+",
                s=170,
                color=color,
                linewidths=3.0,
                zorder=8,
            )
    apply_full_screen_axes(axis)
    axis.set_title(
        f"{CONDITION_LABELS.get(condition, condition)} — onset delay {delay_s:.4f} s\n"
        f"Each point = one marker-window mean; ellipse = empirical {coverage:.0%} of data",
        pad=18,
    )
    save_figure(figure, path)


def build_ellipse_master(
    assigned: pd.DataFrame, selected_delay_s: float, coverage: float
) -> pd.DataFrame:
    kept = assigned[assigned["relative_time_s"] >= selected_delay_s]
    rows: list[dict[str, object]] = []
    group_columns = RECORDING_KEYS + ["target_id"]
    for key, group in kept.groupby(group_columns, sort=True):
        stats = ellipse_stats(group[["gaze_x_deg", "gaze_y_deg"]].to_numpy(), coverage)
        if stats is None:
            continue
        target_x = float(group["target_x_deg"].iloc[0])
        target_y = float(group["target_y_deg"].iloc[0])
        row = dict(zip(group_columns, key))
        row.update(asdict(stats))
        row.update(
            {
                "delay_s": selected_delay_s,
                "delay_ms": round(selected_delay_s * 1000),
                "target_x_deg": target_x,
                "target_y_deg": target_y,
                "center_error_deg": math.hypot(
                    stats.center_x_deg - target_x, stats.center_y_deg - target_y
                ),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def plot_target_condition(
    means: pd.DataFrame,
    target_id: int,
    condition: str,
    target: pd.Series,
    delay_s: float,
    coverage: float,
    path: Path,
) -> bool:
    subset = means[
        means["target_id"].eq(target_id) & means["condition"].eq(condition)
    ]
    if subset.empty:
        return False
    color = target_colors()[target_id]
    figure, axis = plt.subplots(figsize=(9.6, 8.0), constrained_layout=True)
    axis.scatter(
        [target["target_x_deg"]],
        [target["target_y_deg"]],
        s=340,
        color="white",
        edgecolors="#CBD5E1",
        linewidths=1.0,
        zorder=1,
    )
    axis.scatter(
        [target["target_x_deg"]],
        [target["target_y_deg"]],
        s=165,
        marker="x",
        color="#168651",
        linewidths=3.2,
        zorder=8,
        label="target centre",
    )
    axis.scatter(
        subset["gaze_x_deg"],
        subset["gaze_y_deg"],
        s=62,
        marker=CONDITION_MARKERS.get(condition, "o"),
        facecolors="none" if condition == "Calib & Acc" else color,
        edgecolors=color,
        linewidths=1.25,
        alpha=0.76,
        zorder=4,
        label="marker-window means",
    )
    stats = ellipse_stats(subset[["gaze_x_deg", "gaze_y_deg"]].to_numpy(), coverage)
    if stats is not None:
        draw_ellipse(axis, stats, "#DC2626", linewidth=2.3)
        axis.scatter(
            [stats.center_x_deg],
            [stats.center_y_deg],
            marker="+",
            s=150,
            color="#DC2626",
            linewidths=2.4,
            zorder=9,
            label="ellipse centre",
        )
    target_x = float(target["target_x_deg"])
    target_y = float(target["target_y_deg"])
    radial_distance = np.hypot(
        subset["gaze_x_deg"].to_numpy() - target_x,
        subset["gaze_y_deg"].to_numpy() - target_y,
    )
    half_span = float(np.clip(np.quantile(radial_distance, 0.90) + 1.5, 4.5, 10.0))
    center_x = target_x
    center_y = target_y
    outside_zoom = int(
        (
            (subset["gaze_x_deg"] < center_x - half_span)
            | (subset["gaze_x_deg"] > center_x + half_span)
            | (subset["gaze_y_deg"] < center_y - half_span)
            | (subset["gaze_y_deg"] > center_y + half_span)
        ).sum()
    )
    axis.set_xlim(center_x - half_span, center_x + half_span)
    axis.set_ylim(center_y - half_span, center_y + half_span)
    axis.set_aspect("equal", adjustable="box")
    axis.axhline(0, color="#94A3B8", linewidth=0.9, zorder=0)
    axis.axvline(0, color="#94A3B8", linewidth=0.9, zorder=0)
    axis.grid(True)
    axis.set_axisbelow(True)
    axis.set_xlabel("Gaze X (deg)")
    axis.set_ylabel("Gaze Y (deg)")
    axis.set_title(
        f"Target {target_id} | {CONDITION_LABELS.get(condition, condition)} | "
        f"delay {delay_s:.4f} s ({delay_s * 1000:.0f} ms)\n"
        f"One point per marker-window mean; descriptive {coverage:.0%} observation ellipse",
        pad=16,
    )
    axis.legend(loc="best")
    figure.text(
        0.5, 0.012,
        f"condition={condition}  |  target={target_id:02d}  |  delay={delay_s:.4f} s  |  "
        f"windows={len(subset)}  |  points outside zoom={outside_zoom}",
        ha="center", va="bottom", fontsize=9, color="#64748B",
    )
    save_figure(figure, path)
    return True


def plot_per_recording(
    assigned: pd.DataFrame,
    ellipse_master: pd.DataFrame,
    targets: pd.DataFrame,
    selected_delay_s: float,
    coverage: float,
    output_dir: Path,
) -> list[dict[str, str]]:
    kept = assigned[assigned["relative_time_s"] >= selected_delay_s]
    colors = target_colors()
    index_rows: list[dict[str, str]] = []
    for key, group in kept.groupby(RECORDING_KEYS, sort=True):
        date, run_id, subject_id, condition = key
        figure, axis = plt.subplots(figsize=(13.333, 7.5), constrained_layout=True)
        draw_targets(axis, targets, annotate=True)
        for target_id, target_group in group.groupby("target_id"):
            color = colors[int(target_id)]
            axis.scatter(
                target_group["gaze_x_deg"],
                target_group["gaze_y_deg"],
                s=12,
                color=color,
                alpha=0.20,
                edgecolors="none",
                zorder=3,
            )
            mask = np.ones(len(ellipse_master), dtype=bool)
            for column, value in zip(RECORDING_KEYS + ["target_id"], key + (target_id,)):
                mask &= ellipse_master[column].astype(str).eq(str(value)).to_numpy()
            if mask.any():
                row = ellipse_master.loc[mask].iloc[0]
                stats = EllipseStats(
                    center_x_deg=float(row["center_x_deg"]),
                    center_y_deg=float(row["center_y_deg"]),
                    semi_major_deg=float(row["semi_major_deg"]),
                    semi_minor_deg=float(row["semi_minor_deg"]),
                    angle_deg=float(row["angle_deg"]),
                    area_deg2=float(row["area_deg2"]),
                    empirical_coverage=float(row["empirical_coverage"]),
                    n_points=int(row["n_points"]),
                )
                draw_ellipse(axis, stats, "#DC2626", linewidth=1.7)
                axis.scatter(
                    [stats.center_x_deg],
                    [stats.center_y_deg],
                    marker="+",
                    s=90,
                    color="#DC2626",
                    linewidths=2.0,
                    zorder=9,
                )
        apply_full_screen_axes(axis)
        outside = int(
            ((group["gaze_x_deg"].abs() > 32) | (group["gaze_y_deg"].abs() > 19)).sum()
        )
        axis.set_title(
            f"{date} | {subject_id} | run {run_id} | {CONDITION_LABELS.get(condition, condition)}\n"
            f"delay {selected_delay_s:.4f} s ({selected_delay_s * 1000:.0f} ms) | raw gaze + descriptive {coverage:.0%} ellipses",
            pad=14,
        )
        filename = (
            f"DETAIL__recording-{safe_name(date)}-{safe_name(subject_id)}-run-{safe_name(run_id)}__"
            f"condition-{safe_name(condition)}__delay-{selected_delay_s:.4f}s.png"
        )
        figure.text(
            0.5, 0.012,
            f"recording={date}/{subject_id}/run-{run_id}  |  condition={condition}  |  "
            f"delay={selected_delay_s:.4f} s  |  off-screen raw points clipped={outside}",
            ha="center", va="bottom", fontsize=9, color="#64748B",
        )
        save_figure(figure, output_dir / filename)
        index_rows.append(
            {
                "filename": f"per_recording/{filename}",
                "category": "per_recording",
                "what_it_shows": f"{date}, {subject_id}, run {run_id}, {condition}; raw gaze and 95% data ellipses.",
                "why_it_exists": "Full-size recording QA for sequential visual inspection.",
            }
        )
    return index_rows


def plot_quality_box(
    master: pd.DataFrame,
    column: str,
    ylabel: str,
    title: str,
    path: Path,
    reference: float | None = None,
) -> None:
    conditions = ordered_conditions(master["condition"].unique())
    values = [master.loc[master["condition"] == condition, column].to_numpy() for condition in conditions]
    figure, axis = plt.subplots(figsize=(13.333, 7.5), constrained_layout=True)
    box = axis.boxplot(
        values,
        tick_labels=[CONDITION_LABELS.get(c, c) for c in conditions],
        showmeans=True,
        patch_artist=True,
        medianprops={"color": "#DC2626", "linewidth": 2.0},
        meanprops={"marker": "D", "markerfacecolor": "#16A34A", "markeredgecolor": "white", "markersize": 7},
        boxprops={"color": "#475569", "linewidth": 1.2},
        whiskerprops={"color": "#64748B", "linewidth": 1.1},
        capprops={"color": "#64748B", "linewidth": 1.1},
        flierprops={"marker": "o", "markerfacecolor": "none", "markeredgecolor": "#64748B", "markersize": 4},
    )
    for patch, color in zip(box["boxes"], ["#DBEAFE", "#DCFCE7", "#FEF3C7"]):
        patch.set_facecolor(color)
    if reference is not None:
        axis.axhline(reference, color="#DC2626", linestyle="--", linewidth=2.0, label=f"reference {reference:.0%}")
        axis.legend()
    axis.set_ylabel(ylabel)
    axis.set_title(title, pad=18)
    axis.grid(axis="y")
    axis.set_axisbelow(True)
    axis.tick_params(axis="x", rotation=0)
    save_figure(figure, path)


def main() -> None:
    args = parse_args()
    if not 0 < args.coverage < 1:
        raise ValueError("--coverage must be between 0 and 1.")
    delays = parse_delay_spec(args.delays_s)
    output_root = args.output_root.resolve()
    figures = output_root / "figures"
    tables = output_root / "tables"
    delay_figures = figures / "delay_steps"
    delay_tables = tables / "delay_steps"
    condition_figures = figures / "condition_summary"
    target_figures = figures / "target_condition"
    recording_figures = figures / "per_recording"
    qa_figures = figures / "quality_assurance"
    for directory in (
        delay_figures,
        delay_tables,
        condition_figures,
        target_figures,
        recording_figures,
        qa_figures,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    style_plots()
    targets = target_table()
    assigned, session_inventory = collect_assigned_samples(args.data_root.resolve(), targets)
    targets.to_csv(tables / "corrected_target_positions.csv", index=False)
    session_inventory.to_csv(tables / "session_inventory.csv", index=False)

    means_by_delay: dict[float, pd.DataFrame] = {}
    metric_rows = []
    for delay_s in delays:
        means = means_for_delay(assigned, delay_s, args.min_window_samples)
        if means.empty:
            continue
        means_by_delay[delay_s] = means
        means.to_csv(delay_tables / f"window_means_{delay_stem(delay_s)}.csv", index=False)
        metric_rows.append(evaluate_delay(means, args.coverage))
    metrics = pd.DataFrame(metric_rows).sort_values("delay_s").reset_index(drop=True)
    selected_delay_s, best_score, allowance = choose_delay(metrics, args.tie_tolerance)
    selected_means = means_by_delay[selected_delay_s]
    ellipse_master = build_ellipse_master(assigned, selected_delay_s, args.coverage)

    metrics.to_csv(tables / "delay_metrics.csv", index=False)
    selected_means.to_csv(tables / "window_means_selected_delay.csv", index=False)
    ellipse_master.to_csv(tables / "ellipse_master.csv", index=False)
    selection = {
        "selected_delay_s": selected_delay_s,
        "selected_delay_ms": round(selected_delay_s * 1000),
        "candidate_delays_s": delays,
        "coverage": args.coverage,
        "best_raw_score_deg": best_score,
        "score_allowance_deg": allowance,
        "tie_tolerance_relative": args.tie_tolerance,
        "selection_rule": "smallest delay within tolerance of the minimum composite score",
        "composite_score": "median target error + median equivalent radius of empirical 95% ellipse",
    }
    (tables / "selected_delay.json").write_text(
        json.dumps(selection, indent=2), encoding="utf-8"
    )

    figure_index: list[dict[str, str]] = []
    layout_name = "01_corrected_target_layout_large.png"
    plot_target_layout(targets, figures / layout_name)
    figure_index.append(
        {
            "filename": layout_name,
            "category": "layout",
            "what_it_shows": "Corrected large 9-target layout and 27 marker transitions.",
            "why_it_exists": "Verify target 2/3 correction and target sequence before analysis.",
        }
    )

    for delay_s, means in means_by_delay.items():
        row = metrics[np.isclose(metrics["delay_s"], delay_s)].iloc[0].to_dict()
        filename = f"{delay_stem(delay_s)}.png"
        plot_delay_step(
            means,
            targets,
            delay_s,
            args.coverage,
            row,
            math.isclose(delay_s, selected_delay_s),
            delay_figures / filename,
        )
        figure_index.append(
            {
                "filename": f"delay_steps/{filename}",
                "category": "delay_step",
                "what_it_shows": f"Independent full-size gaze summary at onset delay {delay_s:.2f} s.",
                "why_it_exists": "Inspect every delay separately; compare focus and movement toward targets.",
            }
        )

    metric_plots = [
        (
            "02_target_error_vs_delay_seconds.png",
            "median_target_error_deg",
            "Median target error (deg)",
            "Target error for each onset delay (seconds)",
        ),
        (
            "03_spread_vs_delay_seconds.png",
            "median_ellipse_equivalent_radius_deg",
            "Median 95% ellipse equivalent radius (deg)",
            "Data spread for each onset delay (seconds)",
        ),
        (
            "04_score_vs_delay_seconds.png",
            "composite_score_deg",
            "Composite score (deg; lower is better)",
            "Combined delay-selection score (seconds)",
        ),
    ]
    for filename, column, ylabel, title in metric_plots:
        plot_metric(metrics, selected_delay_s, column, ylabel, title, figures / filename)
        figure_index.append(
            {
                "filename": filename,
                "category": "delay_metric",
                "what_it_shows": title,
                "why_it_exists": "Keep each selection metric readable as a separate large figure.",
            }
        )

    for condition in ordered_conditions(selected_means["condition"].unique()):
        filename = f"condition_{safe_name(condition)}_{delay_stem(selected_delay_s)}.png"
        plot_condition_summary(
            selected_means,
            targets,
            condition,
            selected_delay_s,
            args.coverage,
            condition_figures / filename,
        )
        figure_index.append(
            {
                "filename": f"condition_summary/{filename}",
                "category": "condition_summary",
                "what_it_shows": f"Independent full-size {condition} summary at {selected_delay_s:.2f} s.",
                "why_it_exists": "Do not mix calibration, 10-minute, and 60-minute conditions.",
            }
        )

    target_lookup = targets.set_index("target_id")
    for target_id in sorted(TARGETS_NORM):
        for condition in ordered_conditions(selected_means["condition"].unique()):
            filename = (
                f"target_{target_id:02d}_{safe_name(condition)}_"
                f"{delay_stem(selected_delay_s)}.png"
            )
            created = plot_target_condition(
                selected_means,
                target_id,
                condition,
                target_lookup.loc[target_id],
                selected_delay_s,
                args.coverage,
                target_figures / filename,
            )
            if created:
                figure_index.append(
                    {
                        "filename": f"target_condition/{filename}",
                        "category": "target_condition",
                        "what_it_shows": f"Target {target_id}, {condition}, selected delay {selected_delay_s:.2f} s.",
                        "why_it_exists": "Large zoomed process figure for one target and one test ID only.",
                    }
                )

    figure_index.extend(
        plot_per_recording(
            assigned,
            ellipse_master,
            targets,
            selected_delay_s,
            args.coverage,
            recording_figures,
        )
    )

    qa_specs = [
        (
            "ellipse_coverage_by_condition.png",
            "empirical_coverage",
            "Fraction of raw gaze inside ellipse",
            "Empirical ellipse coverage by test ID",
            args.coverage,
        ),
        (
            "ellipse_center_error_by_condition.png",
            "center_error_deg",
            "Ellipse centre to target error (deg)",
            "Ellipse centre error by test ID",
            None,
        ),
    ]
    for filename, column, ylabel, title, reference in qa_specs:
        plot_quality_box(
            ellipse_master,
            column,
            ylabel,
            title,
            qa_figures / filename,
            reference,
        )
        figure_index.append(
            {
                "filename": f"quality_assurance/{filename}",
                "category": "quality_assurance",
                "what_it_shows": title,
                "why_it_exists": "Separate QA chart for coverage or position error.",
            }
        )

    pd.DataFrame(figure_index).to_csv(tables / "figure_index.csv", index=False)
    manifest = {
        "source": str(args.data_root.resolve()),
        "source_sessions": int(len(session_inventory)),
        "source_marker_windows_expected": int(len(session_inventory) * 27),
        "source_marker_windows_with_means": int(len(selected_means)),
        "target_sequence": TARGET_SEQUENCE,
        "target_mapping": TARGETS_NORM,
        "assumed_field_of_view_deg": {"x": FOV_X_DEG, "y": FOV_Y_DEG},
        "important_limitations": [
            "Marker files contain onset/offset only; target IDs use the forwarded 27-window sequence.",
            "Screen-angle degrees use the documented 60 x 33.75 degree assumption because physical viewing geometry is absent.",
        ],
        "output_figure_count": len(figure_index),
    }
    (tables / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(json.dumps(selection, indent=2))
    print(f"sessions={len(session_inventory)}")
    print(f"window_means={len(selected_means)}")
    print(f"ellipse_rows={len(ellipse_master)}")
    print(f"figures={len(figure_index)}")


if __name__ == "__main__":
    main()
