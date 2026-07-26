# Code Walkthrough

## Main Execution Chain

`START_DEMO.ps1` → `src/run_all.py` → `src/analyze_client_meeting_v2.py` → `src/build_ui_manifest.py` → `src/serve_ui.py`

## `analyze_client_meeting_v2.py`

- `CLIENT_CANDIDATES_S`: Fixed client candidates `[0.05, 0.10, 0.15]`.
- `subject_cell_metrics()`: Calculates target error and repeated-window spread within each participant × condition × target cell, then aggregates them with equal weighting to prevent bias from differing sample counts.
- `bootstrap_candidate_comparisons()`: Performs a paired bootstrap across participants (3,000 iterations with a fixed seed).
- `select_client_delay()`: Starts at 0.0500 s. It upgrades to a longer candidate only if that candidate shows a clear and non-conflicting improvement; otherwise, it retains the shorter value.
- `output_name()`: Ensures that every PNG filename includes the scope, topic, condition, delay to four decimal places, and selected delay.
- `apply_openet_visual_qc()`: Applies nearest-target + 3.5×MAD filtering only to OpenET-style presentation figures.
- `openet_observation_ellipse()`: Replicates the covariance/eigendecomposition/χ²=5.991 parameter ellipse used by OpenET2.
- `plot_client_candidate_metric()`: Generates separate PRIMARY full-size figures for accuracy and spread.

## `analyze_real_openet2.py`

- Reads GP3HD gaze/marker files and corrects the target sequence.
- `means_for_delay()`: Retains gaze data after marker onset + delay and calculates the marker-window mean.
- `ellipse_stats()`: Scales the ellipse using an empirical higher quantile of Mahalanobis distance, ensuring that at least 95% of the points are covered by the ellipse.
- `build_ellipse_master()`: Outputs the centre, semi-axes, angle, area, centre-to-target error, and empirical coverage.
- `plot_per_recording()`: Outputs a standalone raw-gaze ellipse figure for each recording.

## `build_ui_manifest.py`

Reads CSV/JSON files and the newly named PNG files to generate `ui/data/ui_manifest.json`. The UI is driven by the manifest, so the manifest must be rebuilt after every analysis rerun.

## `run_all.py` and `serve_ui.py`

- `run_all.py`: Analysis → manifest → HTTP server.
- `serve_ui.py`: Serves the page at `localhost:8765`.
- The HTML file cannot be opened directly by double-clicking because browsers restrict fetching JSON/ES modules in `file://` mode. A local server must be used.

## Most Common Places to Modify

- Change the candidates: `CLIENT_CANDIDATES_S` (this changes the client's evaluation criteria and must be confirmed first).
- Change the full scan: runtime argument `--delays-s 0.00:0.20:0.01`.
- Change coverage: runtime argument `--coverage 0.95`.
- Change figure appearance: `style_plots()`, `plot_client_candidate_metric()`, and `plot_recording_target_comparison()`.
- Change naming: `output_name()`; do not bypass it by constructing filenames directly.
