# Integration Contract

## Output Columns

`benchmark_metrics.csv` should include:

- `session_id`
- `gaze_samples`
- `duration_s`
- `effective_sampling_hz`
- `valid_samples`
- `invalid_samples`
- `valid_rate`
- `gaze_dispersion_x`
- `gaze_dispersion_y`
- `marker_events`

## Design Rule

Metrics should be deterministic and formula-based. Do not silently filter data unless the filtering rule is documented in the output.
