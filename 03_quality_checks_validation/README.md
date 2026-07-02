# 03 Quality Checks Validation

Owner responsibility: detect common recording problems automatically.

## Goal

Build validation checks that flag suspicious or incomplete eye-tracking recordings before they are used in benchmarking.This module performs first-pass quality validation on the standardised eye-tracking session data produced by task 02. It checks each session for common data quality issues and generates a session-level quality report for review.

## Inputs

- `standard_gaze.csv`
- `standard_video_timestamps.csv`
- `standard_marker_events.csv`

## Outputs

- `quality_report.csv`
- `quality_report.json`
- A list of human-readable flags per session

## Run

```bash
python src/quality_checks.py --standard-dir outputs/2025_04_12_001 --output outputs/quality_report.csv
```

## Acceptance Criteria

- Detect low valid gaze rate.
- Detect duplicate timestamps.
- Detect backward time jumps.
- Detect irregular sampling intervals.
- Detect missing video timestamps.
- Detect unexpected marker event count.
- Keep threshold values configurable.
