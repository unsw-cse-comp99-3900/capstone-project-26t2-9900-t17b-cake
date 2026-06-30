# 05 Visualisation Reporting

Owner responsibility: turn cleaned metrics and quality reports into readable figures for sprint demos, client feedback, and final project reporting.

## Goal

This module converts the integrated OpenET 2 metrics table into visual evidence that can be understood without reading raw CSV files. It supports the project role of QA, documentation, and integration by making data quality, session coverage, and benchmark results easier to inspect.

## Inputs

The current script expects a combined metrics CSV produced by the upstream pipeline. The required columns are documented in `docs/integration_contract.md`.

Typical input examples:

- `outputs/quality_metrics.csv`
- `outputs/benchmark_metrics.csv`
- an integrated Sprint 1/Sprint 2 metrics export

## Outputs

The script writes four PNG figures to the selected output directory:

- `sessions_by_date.png`
- `sampling_rate_by_session.png`
- `valid_rate_by_session.png`
- `quality_flags_summary.png`

These figures can be used in Demo B, meeting minutes, client updates, and final report evidence.

## Run

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Generate figures:

```bash
python3 src/visualise_results.py --metrics outputs/quality_metrics.csv --output-dir outputs/figures
```

Run tests:

```bash
python3 -m pytest -q
```

## Acceptance Criteria

- Plot session counts by collection date.
- Plot effective sampling rate by session.
- Plot valid gaze sample rate by session.
- Plot quality flag summary, including a clear empty-state chart when no flags are present.
- Save figures in a deterministic output folder.
- Fail with a readable error if required input columns are missing.

## Sprint Boundary

For the current sprint, static PNG figures are enough because the upstream data and metric contracts are still stabilising. Interactive dashboards can be added later once the integrated pipeline, filtering rules, and client reporting needs are confirmed.
