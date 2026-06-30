# Integration Contract

This document records the minimum data contract between the upstream metric pipeline and the visualisation/reporting module.

## Expected Metrics Columns

Required columns:

- `session_id`
- `date`
- `run_id`
- `effective_sampling_hz` or `gp3_effective_hz`
- `valid_rate` or `gp3_valid_rate`

Optional column:

- `quality_flags`

If `quality_flags` is missing, the module treats all sessions as unflagged and produces a "No quality flags detected" figure.

## Output Files

- `sessions_by_date.png`
- `sampling_rate_by_session.png`
- `valid_rate_by_session.png`
- `quality_flags_summary.png`

## Integration Notes

- `date` should identify the collection date or session date.
- `run_id` should be stable enough to distinguish sessions within the same date.
- `effective_sampling_hz` should represent the calculated sampling rate after cleaning.
- `valid_rate` should be between `0` and `1`, where `1` means all samples are valid.
- Multiple quality flags should be separated with semicolons, for example `low_valid_rate;low_sampling_rate`.

## Design Rule

Figures should be readable in a classroom demo and useful for later client discussion. Prefer clear labels, stable filenames, and moderate information density over crowded charts.
