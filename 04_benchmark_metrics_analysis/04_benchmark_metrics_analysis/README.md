# 04 Benchmark Metrics Analysis

Owner responsibility: calculate quantitative metrics for comparing eye-tracking recordings.

## Goal

Produce first-pass benchmark metrics from standardised gaze data and quality-check outputs.

## Inputs

- `standard_gaze.csv`
- `standard_video_timestamps.csv`
- `standard_marker_events.csv`
- Optional `quality_report.csv`

## Outputs

- `benchmark_metrics.csv`
- `benchmark_metrics.json`

## Run

```bash
python src/benchmark_metrics.py --standard-dir outputs/2025_04_12_001 --output outputs/benchmark_metrics.csv
```

## Acceptance Criteria

- Calculate recording duration.
- Calculate effective sampling rate.
- Calculate valid and invalid sample counts.
- Calculate valid sample rate.
- Calculate simple gaze dispersion metrics.
- Keep formulas documented and easy to audit.

## Sprint 1 Boundary

This task should produce reliable first-pass metrics. Advanced fixation detection and clinical-grade calibration metrics can be added later.
