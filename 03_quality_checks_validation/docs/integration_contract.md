# Integration Contract

## Input Contract

This module consumes standardised tables created by task 02.

Expected input data should already be standardised and include:

- gaze sample timestamps
- gaze validity values
- session-level identifiers
- marker event records

This module should not read raw device-specific files directly.

## Output Columns

`quality_report.csv` should include:

- `session_id`
- `valid_rate`
- `duplicate_timestamps`
- `negative_time_jumps`
- `irregular_interval_pct`
- `marker_events` / `unexpected marker event count`
- `quality_flags`

## Design Rule

Quality flags are warnings for review. They should not silently delete or modify source data. The original standardised input tables should remain unchanged. Any quality concerns should be recorded in `quality_report.csv` through the `quality_flags` column.
