"""Client-meeting-first delay analysis for the real OpenET2 Demo B data.

The 2026-07-17 client meeting explicitly requested 50, 100, and 150 ms onset
checks.  A 0--200 ms scan is retained as a secondary sensitivity analysis.
Accuracy and precision are reported separately; a 95% data ellipse is a QA
deliverable and is not added to an arbitrary delay-selection score.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

# The chart is generated in the background; there is no need to open the graphics window.
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd


# The three main delays specified in the client meeting
CLIENT_CANDIDATES_S = [0.05, 0.10, 0.15]

# Reuse the original data reading and basic plotting functions
PRIMARY_MODULE_PATH = Path(__file__).with_name("analyze_real_openet2.py")


# Dynamically read the main analysis file to avoid repeatedly writing existing functions.
def load_primary_module():
    spec = importlib.util.spec_from_file_location(
        "openet2_primary_analysis", PRIMARY_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {PRIMARY_MODULE_PATH}")
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # The legacy module is reused for parsing, ellipse QA, and recording plots.
    # Override its filename helper so every new output has four decimal places.
    module.delay_stem = delay_stem
    module.delay_label = delay_label
    return module


# Retain the original command-line input format.
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--delays-s", default="0.00:0.20:0.01")
    parser.add_argument("--coverage", type=float, default=0.95)
    parser.add_argument("--min-window-samples", type=int, default=5)
    parser.add_argument("--bootstrap-repetitions", type=int, default=3000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260717)
    return parser.parse_args()


# The delay function consistently retains four decimal places in both the file and the results.
def delay_label(delay_s: float) -> str:
    return f"{delay_s:.4f} s"


def delay_stem(delay_s: float) -> str:
    return f"delay_{delay_s:.4f}s"


# Generate a uniform filename based on the graph's scope, theme, and delay.
def output_name(
    scope: str,
    topic: str,
    condition: str,
    *,
    delay_s: float | None = None,
    delay_set_s: list[float] | None = None,
    scan_start_s: float | None = None,
    scan_end_s: float | None = None,
    selected_delay_s: float | None = None,
    target_id: int | None = None,
    extra: str | None = None,
) -> str:
    """Return a filename that is self-explanatory outside the UI.

    Every PNG states its presentation scope (for example S03 or DETAIL),
    analytical topic, test condition, and either one exact delay or the exact
    scan range.  Four decimal places are mandatory for delay seconds.
    """
    parts = [scope, topic, f"condition-{condition}"]
    if target_id is not None:
        parts.append(f"target-{target_id:02d}")
    if delay_s is not None:
        parts.append(f"delay-{delay_s:.4f}s")
    elif delay_set_s is not None:
        formatted = "-".join(f"{value:.4f}s" for value in delay_set_s)
        parts.append(f"delay-CANDIDATES_{formatted}")
    elif scan_start_s is not None and scan_end_s is not None:
        parts.append(f"delay-SCAN_{scan_start_s:.4f}s-{scan_end_s:.4f}s")
    else:
        raise ValueError("An exact delay or scan range is required for every PNG")
    if selected_delay_s is not None:
        parts.append(f"selected-{selected_delay_s:.4f}s")
    if extra:
        parts.append(extra)
    return "__".join(parts) + ".png"


# Add parameters and result descriptions at the bottom of the image.
def add_figure_footer(figure: plt.Figure, text: str) -> None:
    layout_engine = figure.get_layout_engine()
    if layout_engine is not None and hasattr(layout_engine, "set"):
        layout_engine.set(rect=(0.0, 0.065, 1.0, 0.935))
    figure.text(
        0.5,
        0.010,
        text,
        ha="center",
        va="bottom",
        fontsize=9,
        color="#64748B",
    )


# Each participant, condition, and target first calculates one row of results.
def subject_cell_metrics(means: pd.DataFrame) -> pd.DataFrame:
    """Create one equally weighted row per participant/test-ID/target cell.

    Each recording has three marker presentations for each of nine targets.
    Accuracy is the median target distance of those marker-window means.
    Spread is the median distance of those means from their robust cell centre.
    """
    rows: list[dict[str, object]] = []
    keys = ["subject_id", "condition", "target_id"]
    for key, cell in means.groupby(keys, sort=True):
        subject_id, condition, target_id = key
        centre_x = float(cell["gaze_x_deg"].median())
        centre_y = float(cell["gaze_y_deg"].median())
        radial = np.hypot(
            cell["gaze_x_deg"].to_numpy() - centre_x,
            cell["gaze_y_deg"].to_numpy() - centre_y,
        )
        rows.append(
            {
                "delay_s": float(cell["delay_s"].iloc[0]),
                "delay_ms": int(cell["delay_ms"].iloc[0]),
                "subject_id": subject_id,
                "condition": condition,
                "target_id": int(target_id),
                "marker_window_means": int(len(cell)),
                "accuracy_median_target_error_deg": float(
                    cell["target_error_deg"].median()
                ),
                "repeat_spread_median_radial_deg": float(np.median(radial)),
            }
        )
    return pd.DataFrame(rows)


# Summarize the results of a delay across all data or a single condition.
def aggregate_metric_row(
    cell_metrics: pd.DataFrame,
    means: pd.DataFrame,
    condition: str | None,
) -> dict[str, object]:
    cells = cell_metrics
    used_means = means
    if condition is not None:
        cells = cells[cells["condition"] == condition]
        used_means = used_means[used_means["condition"] == condition]
    return {
        "delay_s": float(means["delay_s"].iloc[0]),
        "delay_ms": int(means["delay_ms"].iloc[0]),
        "condition": condition or "ALL",
        "balanced_accuracy_deg": float(
            cells["accuracy_median_target_error_deg"].median()
        ),
        "balanced_repeat_spread_deg": float(
            cells["repeat_spread_median_radial_deg"].median()
        ),
        "participant_condition_target_cells": int(len(cells)),
        "valid_marker_windows": int(len(used_means)),
        "valid_gaze_samples": int(used_means["valid_samples"].sum()),
    }


# Organize the bootstrap data by participant.
def bootstrap_arrays(cell_metrics: pd.DataFrame, condition: str | None) -> dict:
    work = cell_metrics
    if condition is not None:
        work = work[work["condition"] == condition]
    return {
        subject: (
            rows["accuracy_median_target_error_deg"].to_numpy(),
            rows["repeat_spread_median_radial_deg"].to_numpy(),
        )
        for subject, rows in work.groupby("subject_id", sort=False)
    }


# 对一次 bootstrap 抽样计算 accuracy 和 spread
def bootstrap_statistic(arrays: dict, sampled_subjects: np.ndarray) -> tuple[float, float]:
    accuracy = np.concatenate([arrays[subject][0] for subject in sampled_subjects])
    spread = np.concatenate([arrays[subject][1] for subject in sampled_subjects])
    return float(np.median(accuracy)), float(np.median(spread))


# 比较 50、100 和 150 ms，判断更长 delay 是否真的更好
def bootstrap_candidate_comparisons(
    cells_by_delay: dict[float, pd.DataFrame],
    conditions: list[str],
    repetitions: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    comparisons = [(0.05, 0.10), (0.10, 0.15), (0.05, 0.15)]
    for condition in [None] + conditions:
        arrays_by_delay = {
            delay: bootstrap_arrays(cells_by_delay[delay], condition)
            for delay in CLIENT_CANDIDATES_S
        }
        common_subjects = np.array(
            sorted(set.intersection(*(set(value) for value in arrays_by_delay.values())))
        )
        if len(common_subjects) < 2:
            continue
        for shorter, longer in comparisons:
            accuracy_diff = np.empty(repetitions)
            spread_diff = np.empty(repetitions)
            for index in range(repetitions):
                sampled = rng.choice(
                    common_subjects, size=len(common_subjects), replace=True
                )
                acc_short, spread_short = bootstrap_statistic(
                    arrays_by_delay[shorter], sampled
                )
                acc_long, spread_long = bootstrap_statistic(
                    arrays_by_delay[longer], sampled
                )
                accuracy_diff[index] = acc_long - acc_short
                spread_diff[index] = spread_long - spread_short
            acc_ci = np.quantile(accuracy_diff, [0.025, 0.5, 0.975])
            spread_ci = np.quantile(spread_diff, [0.025, 0.5, 0.975])
            acc_improves = bool(acc_ci[2] < 0)
            spread_improves = bool(spread_ci[2] < 0)
            acc_worsens = bool(acc_ci[0] > 0)
            spread_worsens = bool(spread_ci[0] > 0)
            longer_clearly_better = (acc_improves or spread_improves) and not (
                acc_worsens or spread_worsens
            )
            rows.append(
                {
                    "condition": condition or "ALL",
                    "shorter_delay_s": shorter,
                    "longer_delay_s": longer,
                    "common_participants": int(len(common_subjects)),
                    "bootstrap_repetitions": repetitions,
                    "accuracy_difference_longer_minus_shorter_median_deg": float(
                        acc_ci[1]
                    ),
                    "accuracy_difference_ci95_low_deg": float(acc_ci[0]),
                    "accuracy_difference_ci95_high_deg": float(acc_ci[2]),
                    "spread_difference_longer_minus_shorter_median_deg": float(
                        spread_ci[1]
                    ),
                    "spread_difference_ci95_low_deg": float(spread_ci[0]),
                    "spread_difference_ci95_high_deg": float(spread_ci[2]),
                    "longer_clearly_better": longer_clearly_better,
                    "interpretation": (
                        "longer delay has a clear non-conflicting improvement"
                        if longer_clearly_better
                        else "no clear non-conflicting improvement; prefer shorter per client rule"
                    ),
                }
            )
    return pd.DataFrame(rows)


# 按 client rule 从 50 ms 开始选择最终 delay
def select_client_delay(comparisons: pd.DataFrame, condition: str) -> float:
    """Start at 50 ms; move longer only for clear non-conflicting improvement."""
    selected = 0.05
    subset = comparisons[comparisons["condition"] == condition]
    for candidate in [0.10, 0.15]:
        row = subset[
            np.isclose(subset["shorter_delay_s"], selected)
            & np.isclose(subset["longer_delay_s"], candidate)
        ]
        if not row.empty and bool(row.iloc[0]["longer_clearly_better"]):
            selected = candidate
    return selected


# 绘制单个 condition 在一个 delay 下的 gaze 分布
def plot_condition_delay(
    module,
    means: pd.DataFrame,
    targets: pd.DataFrame,
    condition: str,
    delay_s: float,
    selected_delay_s: float,
    path: Path,
) -> None:
    subset = means[means["condition"] == condition]
    figure, axis = plt.subplots(figsize=(13.333, 7.5), constrained_layout=True)
    module.draw_targets(axis, targets, annotate=True)
    colors = module.target_colors()
    for target_id, group in subset.groupby("target_id", sort=True):
        color = colors[int(target_id)]
        axis.scatter(
            group["gaze_x_deg"],
            group["gaze_y_deg"],
            s=58,
            marker=module.CONDITION_MARKERS.get(condition, "o"),
            facecolors="none" if condition == "Calib & Acc" else color,
            edgecolors=color,
            linewidths=1.25,
            alpha=0.78,
            zorder=5,
        )
    module.apply_full_screen_axes(axis)
    cell = subject_cell_metrics(subset)
    accuracy = float(cell["accuracy_median_target_error_deg"].median())
    spread = float(cell["repeat_spread_median_radial_deg"].median())
    selected_text = " — CLIENT-RULE SELECTION" if math.isclose(
        delay_s, selected_delay_s
    ) else ""
    axis.set_title(
        f"{module.CONDITION_LABELS.get(condition, condition)} | "
        f"delay {delay_s:.4f} s ({delay_s * 1000:.0f} ms){selected_text}\n"
        f"Recording evidence: one marker per window mean",
        pad=16,
    )
    add_figure_footer(
        figure,
        f"condition={condition}  |  delay={delay_s:.4f} s  |  "
        f"balanced accuracy={accuracy:.3f} deg  |  repeat spread={spread:.3f} deg  |  "
        f"valid windows={len(subset)}",
    )
    module.save_figure(figure, path)


# 绘制 0 到 200 ms 的完整 sensitivity scan
def plot_metric_curve(
    frame: pd.DataFrame,
    condition: str,
    column: str,
    ylabel: str,
    selected_delay_s: float,
    path: Path,
) -> None:
    subset = frame[frame["condition"] == condition].sort_values("delay_s")
    figure, axis = plt.subplots(figsize=(13.333, 7.5), constrained_layout=True)
    axis.plot(
        subset["delay_s"],
        subset[column],
        marker="o",
        markersize=6.5,
        linewidth=2.6,
        color="#1D4ED8",
    )
    candidates = subset[subset["delay_s"].isin(CLIENT_CANDIDATES_S)]
    axis.scatter(
        candidates["delay_s"],
        candidates[column],
        s=125,
        marker="D",
        color="#F59E0B",
        edgecolors="#92400E",
        linewidths=1.2,
        label="client candidates: 0.0500, 0.1000, 0.1500 s",
        zorder=5,
    )
    selected_row = subset[np.isclose(subset["delay_s"], selected_delay_s)].iloc[0]
    axis.axvline(selected_delay_s, linestyle="--", color="#DC2626", linewidth=2.2)
    axis.scatter(
        [selected_delay_s],
        [selected_row[column]],
        s=220,
        color="#DC2626",
        edgecolors="white",
        linewidths=1.5,
        label=f"client-rule selection: {selected_delay_s:.4f} s",
        zorder=7,
    )
    axis.set_xticks(subset["delay_s"])
    axis.set_xticklabels([f"{value:.2f}" for value in subset["delay_s"]], rotation=0)
    axis.set_xlabel("Onset delay (s)")
    axis.set_ylabel(ylabel)
    axis.set_title(
        f"{condition} | {ylabel}\n"
        f"Full sensitivity scan: 0.0000–0.2000 s; selected delay: {selected_delay_s:.4f} s"
    )
    axis.grid(True)
    axis.set_axisbelow(True)
    axis.legend(loc="best")
    for row in candidates.itertuples():
        axis.annotate(
            f"{row.delay_s:.4f} s",
            (row.delay_s, getattr(row, column)),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            color="#92400E",
            fontweight="semibold",
        )
    add_figure_footer(
        figure,
        "Client candidates are labelled directly. Lower values are better; accuracy and spread are evaluated separately.",
    )
    module = None
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(figure)


# 单独突出 client 指定的三个 delay
def plot_client_candidate_metric(
    frame: pd.DataFrame,
    condition: str,
    column: str,
    ylabel: str,
    selected_delay_s: float,
    path: Path,
) -> None:
    subset = frame[
        (frame["condition"] == condition)
        & frame["delay_s"].isin(CLIENT_CANDIDATES_S)
    ].sort_values("delay_s")
    if len(subset) != len(CLIENT_CANDIDATES_S):
        raise ValueError(f"Missing client candidate rows for {condition}/{column}")
    figure, axis = plt.subplots(figsize=(13.333, 7.5), constrained_layout=True)
    axis.axvspan(
        selected_delay_s - 0.018,
        selected_delay_s + 0.018,
        color="#FEF3C7",
        alpha=0.95,
        zorder=0,
        label=f"recommended {selected_delay_s:.4f} s",
    )
    axis.plot(
        subset["delay_s"],
        subset[column],
        color="#1D4ED8",
        linewidth=3.0,
        marker="o",
        markersize=11,
        markerfacecolor="white",
        markeredgewidth=2.6,
        zorder=4,
    )
    selected = subset[np.isclose(subset["delay_s"], selected_delay_s)].iloc[0]
    axis.scatter(
        [selected_delay_s],
        [selected[column]],
        s=250,
        color="#DC2626",
        edgecolors="white",
        linewidths=2.0,
        zorder=6,
    )
    for row in subset.itertuples():
        value = getattr(row, column)
        axis.annotate(
            f"{value:.4f}",
            (row.delay_s, value),
            xytext=(0, 16),
            textcoords="offset points",
            ha="center",
            fontsize=14,
            fontweight="semibold",
            color="#0F172A",
        )
    axis.set_xticks(CLIENT_CANDIDATES_S)
    axis.set_xticklabels(
        [f"{value:.4f} s\n({value * 1000:.0f} ms)" for value in CLIENT_CANDIDATES_S]
    )
    axis.set_xlabel("Client-requested onset compensation")
    axis.set_ylabel(ylabel)
    axis.set_title(
        f"PRIMARY client comparison | {condition} | {ylabel}\n"
        "50, 100 and 150 ms only; lower is better"
    )
    axis.grid(axis="y")
    axis.set_axisbelow(True)
    axis.margins(y=0.16)
    axis.legend(loc="best")
    add_figure_footer(
        figure,
        "Meeting rule: use a longer candidate only for a clear improvement without a conflicting worsening; otherwise use the shorter candidate.",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=240, bbox_inches="tight", facecolor="white", pad_inches=0.18)
    plt.close(figure)


# 使用 OpenET2 的 visual QC 规则筛选绘图点
def apply_openet_visual_qc(
    recording_means: pd.DataFrame,
    targets: pd.DataFrame,
) -> pd.DataFrame:
    """Reproduce OpenET2's paper-plot QC for the visual comparison only."""
    result = recording_means.copy()
    target_coordinates = targets[["target_x_deg", "target_y_deg"]].to_numpy(float)
    target_ids = targets["target_id"].to_numpy(int)
    gaze_coordinates = result[["gaze_x_deg", "gaze_y_deg"]].to_numpy(float)
    distances = np.linalg.norm(
        gaze_coordinates[:, np.newaxis, :] - target_coordinates[np.newaxis, :, :],
        axis=2,
    )
    result["visual_nearest_target_id"] = target_ids[np.argmin(distances, axis=1)]
    result["visual_target_error_deg"] = np.hypot(
        result["gaze_x_deg"] - result["target_x_deg"],
        result["gaze_y_deg"] - result["target_y_deg"],
    )
    result["visual_qc_cutoff_deg"] = np.nan
    result["visual_qc_status"] = np.where(
        result["visual_nearest_target_id"].eq(result["target_id"]),
        "included",
        "target_mismatch",
    )
    included = result["visual_qc_status"].eq("included")
    for target_id, group in result[included].groupby("target_id"):
        errors = group["visual_target_error_deg"].astype(float)
        if len(errors) < 5:
            cutoff = float(errors.max())
        else:
            median = float(errors.median())
            mad = float((errors - median).abs().median())
            cutoff = (
                float(errors.max())
                if mad <= 1e-12
                else median + 3.5 * 1.4826 * mad
            )
        target_rows = result["target_id"].eq(target_id)
        result.loc[target_rows, "visual_qc_cutoff_deg"] = cutoff
        outliers = (
            target_rows
            & result["visual_qc_status"].eq("included")
            & result["visual_target_error_deg"].gt(cutoff)
        )
        result.loc[outliers, "visual_qc_status"] = "robust_centroid_outlier"
    return result


# 根据 recording-level points 计算 95% observation ellipse
def openet_observation_ellipse(points: np.ndarray):
    """Return OpenET2's parametric 95% observation ellipse (chi-square 5.991)."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3:
        return None
    covariance = np.cov(points, rowvar=False)
    if covariance.shape != (2, 2) or not np.isfinite(covariance).all():
        return None
    values, vectors = np.linalg.eigh(covariance)
    values = np.maximum(values, 0)
    if float(values.max()) <= 0:
        return None
    order = values.argsort()[::-1]
    values = values[order]
    vectors = vectors[:, order]
    angle = float(np.degrees(np.arctan2(vectors[1, 0], vectors[0, 0])))
    width, height = 2 * np.sqrt(values * 5.991)
    return points.mean(axis=0), float(width), float(height), angle


# 生成 recording-level target comparison 图
def plot_recording_target_comparison(
    module,
    means: pd.DataFrame,
    targets: pd.DataFrame,
    condition: str,
    delay_s: float,
    coverage: float,
    path: Path,
) -> pd.DataFrame:
    """OpenET2-style summary using current Demo B data at one exact delay.

    The old OpenET2 figure is visually clear because it plots one recording-
    level target mean rather than all raw samples.  This implementation keeps
    that data level, distinguishes the three test conditions by marker shape,
    and treats the ellipse as descriptive QA only.
    """
    group_columns = [
        "date", "run_id", "subject_id", "condition", "target_id",
        "target_x_deg", "target_y_deg",
    ]
    recording_means = (
        means.groupby(group_columns, as_index=False)
        .agg(
            gaze_x_deg=("gaze_x_deg", "mean"),
            gaze_y_deg=("gaze_y_deg", "mean"),
            marker_windows=("window_index", "size"),
        )
    )
    plot_means = recording_means
    if condition != "ALL":
        plot_means = recording_means[recording_means["condition"] == condition].copy()
    if plot_means.empty:
        raise ValueError(f"No recording-target means for condition {condition}")
    visual_qc = apply_openet_visual_qc(plot_means, targets)
    included_means = visual_qc[visual_qc["visual_qc_status"].eq("included")].copy()
    excluded_count = int(len(visual_qc) - len(included_means))
    if included_means.empty:
        raise ValueError(f"No recording-target means survived visual QC for {condition}")
    colors = module.target_colors()
    figure, axis = plt.subplots(figsize=(12.0, 8.2), constrained_layout=True)

    date_values = sorted(included_means["date"].astype(str).unique())
    date_markers = {date: marker for date, marker in zip(date_values, ["o", "*"])}
    for target_id, target_group in included_means.groupby("target_id", sort=True):
        color = colors[int(target_id)]
        target_row = target_group.iloc[0]
        axis.scatter(
            [target_row["target_x_deg"]],
            [target_row["target_y_deg"]],
            marker="x",
            s=180,
            color="#168B36",
            linewidths=2.6,
            zorder=8,
        )
        axis.text(
            float(target_row["target_x_deg"]),
            float(target_row["target_y_deg"]) + 0.9,
            f"T{int(target_id)}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#166534",
            zorder=9,
        )
        if condition == "ALL":
            for test_id in module.CONDITION_ORDER:
                observations = target_group[target_group["condition"] == test_id]
                if observations.empty:
                    continue
                marker = module.CONDITION_MARKERS[test_id]
                axis.scatter(
                    observations["gaze_x_deg"],
                    observations["gaze_y_deg"],
                    marker=marker,
                    s=82,
                    facecolors="none" if test_id == "Calib & Acc" else color,
                    edgecolors=color,
                    linewidths=1.1,
                    alpha=0.88,
                    zorder=4,
                )
        else:
            for date in date_values:
                observations = target_group[target_group["date"].astype(str) == date]
                if observations.empty:
                    continue
                marker = date_markers[date]
                axis.scatter(
                    observations["gaze_x_deg"],
                    observations["gaze_y_deg"],
                    marker=marker,
                    s=82,
                    facecolors="none" if marker == "o" else color,
                    edgecolors=color,
                    linewidths=1.1,
                    alpha=0.88,
                    zorder=4,
                )
        ellipse = openet_observation_ellipse(
            target_group[["gaze_x_deg", "gaze_y_deg"]].to_numpy()
        )
        if ellipse is not None:
            centre, width, height, angle = ellipse
            axis.scatter(
                [centre[0]],
                [centre[1]],
                marker="+",
                s=150,
                color="#DC2626",
                linewidths=2.0,
                zorder=10,
            )
            axis.add_patch(
                Ellipse(
                    (centre[0], centre[1]),
                    width=width,
                    height=height,
                    angle=angle,
                    fill=False,
                    edgecolor="#DC2626",
                    linestyle="--",
                    linewidth=1.7,
                    alpha=0.9,
                    zorder=6,
                )
            )

    module.apply_full_screen_axes(axis)
    axis.set_title(
        f"{module.CONDITION_LABELS.get(condition, condition)} | "
        f"recording-level target means at delay {delay_s:.4f} s "
        f"({delay_s * 1000:.0f} ms)\n"
        "OpenET2-style visual QC; one point per recording × target",
        pad=14,
    )
    if condition == "ALL":
        condition_handles = [
            Line2D(
                [0], [0], marker=module.CONDITION_MARKERS[test_id],
                color="none", markeredgecolor="black",
                markerfacecolor="none" if test_id == "Calib & Acc" else "black",
                markersize=7.5, label=module.CONDITION_LABELS[test_id],
            )
            for test_id in module.CONDITION_ORDER
        ]
    else:
        condition_handles = [
            Line2D(
                [0], [0], marker=date_markers[date], color="none",
                markeredgecolor="black",
                markerfacecolor="none" if date_markers[date] == "o" else "black",
                markersize=7.5, label=f"{date.replace('_', '-')} recording",
            )
            for date in date_values
        ]
    condition_handles.extend(
        [
            Line2D([0], [0], marker="x", color="#168B36", linestyle="none", markersize=8, label="Target position"),
            Line2D([0], [0], marker="+", color="#DC2626", linestyle="none", markersize=9, label="Observation centre"),
            Line2D([0], [0], color="#DC2626", linestyle="--", linewidth=1.7, label="OpenET2-style 95% observation ellipse (chi-square)"),
        ]
    )
    axis.legend(handles=condition_handles, loc="center left", bbox_to_anchor=(0.015, 0.50))
    add_figure_footer(
        figure,
        f"condition={condition} | delay={delay_s:.4f} s | plotted={len(included_means)}/{len(visual_qc)}; "
        f"excluded by nearest-target + 3.5xMAD visual QC={excluded_count}. Parametric chi-square ellipse is not the client empirical-coverage test and is not used in the delay score.",
    )
    module.save_figure(figure, path)
    return visual_qc


# 把最终推荐和限制写进 Markdown 结果说明
def write_result_notes(
    output_root: Path,
    selected_delay_s: float,
    selected_by_condition: dict[str, float],
    metric_frame: pd.DataFrame,
    comparisons: pd.DataFrame,
) -> None:
    overall = metric_frame[metric_frame["condition"] == "ALL"].set_index("delay_s")
    client_rows = overall.loc[CLIENT_CANDIDATES_S]
    lines = [
        "# Client-meeting-first delay result",
        "",
        f"Recommended delay under the meeting rule: **{selected_delay_s:.4f} s**.",
        "",
        "This is not the minimum of an accuracy-plus-ellipse score. The meeting asked to compare "
        "50, 100, and 150 ms on two separate outcomes: closeness to the target and reduction of "
        "spread. Participant-level paired bootstrap intervals did not show a clear, non-conflicting "
        "improvement for the longer candidates. The meeting's tie rule therefore selects the shortest "
        "candidate, 50 ms.",
        "",
        "## Client candidate medians",
        "",
        "| delay | balanced accuracy (deg) | balanced repeat spread (deg) | valid windows |",
        "|---:|---:|---:|---:|",
    ]
    for delay, row in client_rows.iterrows():
        lines.append(
            f"| {delay:.4f} s | {row['balanced_accuracy_deg']:.4f} | "
            f"{row['balanced_repeat_spread_deg']:.4f} | {int(row['valid_marker_windows'])} |"
        )
    lines.extend(
        [
            "",
            "## Selections by test ID",
            "",
        ]
    )
    for condition, delay in selected_by_condition.items():
        lines.append(f"- {condition}: {delay:.4f} s")
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- The 0.0000–0.2000 s scan is a sensitivity analysis added by the analyst; the client explicitly named only 0.0500, 0.1000, and 0.1500 s.",
            "- The 95% ellipse is checked after delay selection. It is not part of the primary selection score.",
            "- Degree coordinates use the existing 60° × 33.75° field-of-view assumption because physical screen/viewing geometry is absent.",
            "- The result is an evidence-based exploratory recommendation, not a universally validated physiological reaction-time estimate.",
            "",
            f"Pairwise bootstrap rows: {len(comparisons)}; see `tables/client_candidate_pairwise_bootstrap.csv`.",
        ]
    )
    (output_root / "BEST_DELAY_RESULT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


# 主流程：读取数据、计算指标、选择 delay、生成表格和图片
def main() -> None:
    # 1. 读取参数并加载原有分析模块
    args = parse_args()
    if not 0 < args.coverage < 1:
        raise ValueError("--coverage must be between 0 and 1")
    module = load_primary_module()
    module.style_plots()
    delays = module.parse_delay_spec(args.delays_s)
    for candidate in CLIENT_CANDIDATES_S:
        if candidate not in delays:
            raise ValueError(f"Required client candidate {candidate:.4f} s is missing")

    # 2. 建立所有输出文件夹
    output_root = args.output_root.resolve()
    figures = output_root / "figures"
    tables = output_root / "tables"
    extended_figures = figures / "extended_scan_by_condition"
    candidate_figures = figures / "primary_client_candidates"
    metric_figures = figures / "metric_curves"
    selected_condition_figures = figures / "selected_delay_by_condition"
    target_figures = figures / "target_condition_selected_delay"
    recording_figures = figures / "ellipse_per_recording_selected_delay"
    qa_figures = figures / "ellipse_quality_assurance"
    comparison_figures = figures / "recording_target_comparison"
    delay_tables = tables / "delay_steps"
    for directory in [
        extended_figures,
        candidate_figures,
        metric_figures,
        selected_condition_figures,
        target_figures,
        recording_figures,
        qa_figures,
        comparison_figures,
        delay_tables,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    # 3. 读取 target 信息和全部 recording 数据
    targets = module.target_table()
    assigned, inventory = module.collect_assigned_samples(
        args.data_root.resolve(), targets
    )
    conditions = module.ordered_conditions(inventory["condition"].unique())
    targets.to_csv(tables / "corrected_target_positions.csv", index=False)
    inventory.to_csv(tables / "session_inventory.csv", index=False)

    # 4. 对每个 delay 计算 window means 和汇总指标
    means_by_delay: dict[float, pd.DataFrame] = {}
    cells_by_delay: dict[float, pd.DataFrame] = {}
    aggregate_rows: list[dict[str, object]] = []
    cell_parts: list[pd.DataFrame] = []
    for delay_s in delays:
        means = module.means_for_delay(assigned, delay_s, args.min_window_samples)
        if means.empty:
            continue
        cells = subject_cell_metrics(means)
        means_by_delay[delay_s] = means
        cells_by_delay[delay_s] = cells
        cell_parts.append(cells)
        means.to_csv(
            delay_tables / f"window_means_{delay_stem(delay_s)}.csv", index=False
        )
        aggregate_rows.append(aggregate_metric_row(cells, means, None))
        for condition in conditions:
            aggregate_rows.append(aggregate_metric_row(cells, means, condition))

    metric_frame = pd.DataFrame(aggregate_rows).sort_values(
        ["condition", "delay_s"]
    )
    all_cells = pd.concat(cell_parts, ignore_index=True)
    metric_frame.to_csv(tables / "delay_metrics_accuracy_and_spread.csv", index=False)
    all_cells.to_csv(tables / "participant_condition_target_metrics.csv", index=False)

    # 5. 用 paired bootstrap 比较三个 client candidates
    comparisons = bootstrap_candidate_comparisons(
        cells_by_delay,
        conditions,
        args.bootstrap_repetitions,
        args.bootstrap_seed,
    )
    comparisons.to_csv(tables / "client_candidate_pairwise_bootstrap.csv", index=False)
    selected_delay_s = select_client_delay(comparisons, "ALL")
    selected_by_condition = {
        condition: select_client_delay(comparisons, condition)
        for condition in conditions
    }
    # 保存最终 delay、判断规则和分析说明
    selection = {
        "selected_delay_s": selected_delay_s,
        "selected_delay_formatted": delay_label(selected_delay_s),
        "client_candidates_s": CLIENT_CANDIDATES_S,
        "extended_sensitivity_scan_s": delays,
        "selected_by_condition_s": selected_by_condition,
        "primary_accuracy_metric": (
            "median across equally weighted participant-condition-target cells; "
            "cell value is median target error of its marker-window means"
        ),
        "primary_spread_metric": (
            "median across equally weighted participant-condition-target cells; "
            "cell value is median radial spread of repeated marker-window means"
        ),
        "decision_rule": (
            "start at 0.0500 s; use a longer client candidate only when participant-level "
            "paired bootstrap shows a clear improvement in accuracy or spread without a "
            "clear worsening of the other; otherwise prefer the shorter delay"
        ),
        "meeting_interpretation": (
            "primary comparison is exactly 0.0500, 0.1000, and 0.1500 s; the meeting "
            "also requires separate calibration, 10-minute, and 60-minute views and a "
            "final shortest-equivalent recommendation"
        ),
        "openet2_reference_warning": (
            "the OpenET2 v1.5 reference figure used target_settle_time_s=0.6000 and "
            "paper-style target-mismatch/MAD filtering, so it is a visual/statistical "
            "reference only and is not evidence for choosing 0.6000 s in Demo B"
        ),
        "ellipse_role": "post-selection empirical 95% coverage QA; excluded from delay score",
        "bootstrap_repetitions": args.bootstrap_repetitions,
        "bootstrap_seed": args.bootstrap_seed,
    }
    (tables / "selected_delay_client_rule.json").write_text(
        json.dumps(selection, indent=2), encoding="utf-8"
    )

    # 6. 生成每个 condition 和每个 delay 的完整图
    figure_index: list[dict[str, str]] = []
    for delay_s, means in means_by_delay.items():
        for condition in conditions:
            condition_dir = extended_figures / module.safe_name(condition)
            filename = output_name(
                "DETAIL",
                "condition-scatter",
                module.safe_name(condition),
                delay_s=delay_s,
            )
            plot_condition_delay(
                module,
                means,
                targets,
                condition,
                delay_s,
                selected_by_condition[condition],
                condition_dir / filename,
            )
            figure_index.append(
                {
                    "filename": str(
                        Path("extended_scan_by_condition")
                        / module.safe_name(condition)
                        / filename
                    ),
                    "category": "extended_condition_delay",
                    "condition": condition,
                    "delay_s": delay_s,
                    "what_it_shows": (
                        f"One full-size {condition} process figure at {delay_s:.4f} s; "
                        "each point is one marker-window mean."
                    ),
                    "why_it_exists": (
                        "Inspect every delay separately without mixing the three test IDs."
                    ),
                }
            )

    # 7. 生成 client 最关心的 50、100 和 150 ms 对比图
    for column, label, stem, scope in [
        (
            "balanced_accuracy_deg",
            "Balanced target accuracy error (deg)",
            "accuracy",
            "S03",
        ),
        (
            "balanced_repeat_spread_deg",
            "Balanced repeat spread (deg)",
            "spread",
            "S04",
        ),
    ]:
        filename = output_name(
            scope,
            f"PRIMARY-client-candidates-{stem}",
            "ALL",
            delay_set_s=CLIENT_CANDIDATES_S,
            selected_delay_s=selected_delay_s,
        )
        plot_client_candidate_metric(
            metric_frame,
            "ALL",
            column,
            label,
            selected_delay_s,
            candidate_figures / filename,
        )
        figure_index.append(
            {
                "filename": str(Path("primary_client_candidates") / filename),
                "category": "primary_client_candidate_metric",
                "condition": "ALL",
                "delay_s": selected_delay_s,
                "what_it_shows": (
                    f"Primary client comparison of {label.lower()} at exactly "
                    "0.0500, 0.1000, and 0.1500 s."
                ),
                "why_it_exists": (
                    "Direct answer to the meeting request; the full 0.0000–0.2000 s "
                    "scan is deliberately kept separate."
                ),
            }
        )

    # 8. 生成 0 到 200 ms 的 secondary sensitivity scan
    for condition in ["ALL"] + conditions:
        condition_selected = (
            selected_delay_s
            if condition == "ALL"
            else selected_by_condition[condition]
        )
        for column, label, stem in [
            ("balanced_accuracy_deg", "Balanced target accuracy error (deg)", "accuracy"),
            ("balanced_repeat_spread_deg", "Balanced repeat spread (deg)", "spread"),
        ]:
            filename = output_name(
                "SECONDARY",
                f"sensitivity-scan-{stem}",
                module.safe_name(condition),
                scan_start_s=min(delays),
                scan_end_s=max(delays),
                selected_delay_s=condition_selected,
            )
            plot_metric_curve(
                metric_frame,
                condition,
                column,
                label,
                condition_selected,
                metric_figures / filename,
            )
            figure_index.append(
                {
                    "filename": str(Path("metric_curves") / filename),
                    "category": "metric_curve",
                    "condition": condition,
                    "delay_s": condition_selected,
                    "what_it_shows": f"{label} across the full scan for {condition}.",
                    "why_it_exists": "Summary comparison; client candidates are highlighted.",
                }
            )

    # 9. 输出最终选中 delay 对应的数据和 condition 图
    selected_means = means_by_delay[selected_delay_s]
    selected_means.to_csv(
        tables / f"window_means_selected_{delay_stem(selected_delay_s)}.csv",
        index=False,
    )
    for condition in conditions:
        condition_delay = selected_by_condition[condition]
        condition_means = means_by_delay[condition_delay]
        filename = output_name(
            "DETAIL",
            "selected-condition-scatter",
            module.safe_name(condition),
            delay_s=condition_delay,
            selected_delay_s=condition_delay,
        )
        plot_condition_delay(
            module,
            condition_means,
            targets,
            condition,
            condition_delay,
            condition_delay,
            selected_condition_figures / filename,
        )
        figure_index.append(
            {
                "filename": str(Path("selected_delay_by_condition") / filename),
                "category": "selected_condition_summary",
                "condition": condition,
                "delay_s": condition_delay,
                "what_it_shows": f"Selected client-rule delay for {condition}.",
                "why_it_exists": "One prominent readable output per test ID.",
            }
        )

    # 10. 计算 ellipse QA，并生成 target-level 图
    ellipse_master = module.build_ellipse_master(
        assigned, selected_delay_s, args.coverage
    )
    ellipse_master.to_csv(
        tables / f"ellipse_master_{delay_stem(selected_delay_s)}.csv", index=False
    )
    target_lookup = targets.set_index("target_id")
    for target_id in sorted(module.TARGETS_NORM):
        for condition in conditions:
            filename = output_name(
                "DETAIL",
                "target-evidence",
                module.safe_name(condition),
                target_id=target_id,
                delay_s=selected_delay_s,
            )
            created = module.plot_target_condition(
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
                        "filename": str(Path("target_condition_selected_delay") / filename),
                        "category": "target_condition",
                        "condition": condition,
                        "delay_s": selected_delay_s,
                        "what_it_shows": f"Target {target_id}, {condition}, selected delay.",
                        "why_it_exists": "Readable target-level view of marker-window means.",
                    }
                )

    # 11. 生成每个 recording 的单独 ellipse 图
    recording_rows = module.plot_per_recording(
        assigned,
        ellipse_master,
        targets,
        selected_delay_s,
        args.coverage,
        recording_figures,
    )
    for row in recording_rows:
        row["filename"] = str(
            Path("ellipse_per_recording_selected_delay")
            / Path(row["filename"]).name
        )
        row["condition"] = "individual recording"
        row["delay_s"] = selected_delay_s
    figure_index.extend(recording_rows)

    # 12. 生成不同 test ID 的 recording-level comparison
    comparison_scopes = {
        "Calib & Acc": "S06",
        "Acc 10min": "S07",
        "Acc 60min": "S08",
        "ALL": "SUMMARY",
    }
    comparison_tables = []
    for comparison_condition in conditions + ["ALL"]:
        comparison_filename = output_name(
            comparison_scopes[comparison_condition],
            "recording-target-comparison",
            module.safe_name(comparison_condition),
            delay_s=selected_delay_s,
            selected_delay_s=selected_delay_s,
        )
        recording_target_means = plot_recording_target_comparison(
            module,
            selected_means,
            targets,
            comparison_condition,
            selected_delay_s,
            args.coverage,
            comparison_figures / comparison_filename,
        )
        recording_target_means.insert(0, "comparison_scope", comparison_condition)
        comparison_tables.append(recording_target_means)
        figure_index.append(
            {
                "filename": str(Path("recording_target_comparison") / comparison_filename),
                "category": "recording_target_comparison",
                "condition": comparison_condition,
                "delay_s": selected_delay_s,
                "what_it_shows": (
                    f"One recording-level mean per target for {comparison_condition}; "
                    "date markers have equal area and ellipses are descriptive."
                ),
                "why_it_exists": (
                    "OpenET2-style view rebuilt with current Demo B data and the client-selected delay."
                ),
            }
        )
    pd.concat(comparison_tables, ignore_index=True).to_csv(
        tables / f"recording_target_means_{delay_stem(selected_delay_s)}.csv",
        index=False,
    )

    # 13. 输出 ellipse coverage、centre error 和 area QA 图
    qa_specs = [
        (
            "QA",
            "ellipse-coverage",
            "empirical_coverage",
            "Fraction of raw gaze inside ellipse",
            f"Empirical 95% data-ellipse coverage by test ID | delay {selected_delay_s:.4f} s",
            args.coverage,
        ),
        (
            "S05",
            "ellipse-center-error",
            "center_error_deg",
            "Ellipse centre-to-target error (deg)",
            f"Ellipse centre error by test ID | delay {selected_delay_s:.4f} s",
            None,
        ),
        (
            "QA",
            "ellipse-area",
            "area_deg2",
            "Ellipse area (deg²)",
            f"Ellipse spread by test ID | delay {selected_delay_s:.4f} s",
            None,
        ),
    ]
    for scope, topic, column, ylabel, title, reference in qa_specs:
        filename = output_name(
            scope,
            topic,
            "ALL",
            delay_s=selected_delay_s,
            selected_delay_s=selected_delay_s,
        )
        module.plot_quality_box(
            ellipse_master,
            column,
            ylabel,
            title,
            qa_figures / filename,
            reference,
        )
        figure_index.append(
            {
                "filename": str(Path("ellipse_quality_assurance") / filename),
                "category": "ellipse_qa",
                "condition": "ALL",
                "delay_s": selected_delay_s,
                "what_it_shows": title,
                "why_it_exists": "Post-selection ellipse correctness/position/spread QA.",
            }
        )

    # 14. 保存 figure index、source manifest 和最终文字结果
    pd.DataFrame(figure_index).to_csv(tables / "figure_index.csv", index=False)
    manifest = {
        "analysis_priority": "client meeting first; user full-grid idea as secondary sensitivity analysis",
        "source_data_root": str(args.data_root.resolve()),
        "source_sessions": int(len(inventory)),
        "selected_delay_s": selected_delay_s,
        "client_candidates_s": CLIENT_CANDIDATES_S,
        "extended_delays_s": delays,
        "openet2_reference_settle_time_s": 0.6,
        "openet2_reference_role": "visual/statistical reference only; not a Demo B candidate",
        "coverage": args.coverage,
        "ellipse_rows": int(len(ellipse_master)),
        "figure_count": int(len(figure_index)),
        "target_sequence": module.TARGET_SEQUENCE,
        "target_mapping_normalised": module.TARGETS_NORM,
        "assumed_field_of_view_deg": {
            "x": module.FOV_X_DEG,
            "y": module.FOV_Y_DEG,
        },
    }
    (tables / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    write_result_notes(
        output_root,
        selected_delay_s,
        selected_by_condition,
        metric_frame,
        comparisons,
    )
    # 15. 保留原来的终端输出
    print(json.dumps(selection, indent=2))
    print(f"sessions={len(inventory)}")
    print(f"selected_delay={selected_delay_s:.4f}")
    print(f"ellipse_rows={len(ellipse_master)}")
    print(f"figures={len(figure_index)}")


if __name__ == "__main__":
    main()
