# Integration Contract

## Public Output Columns

`session_inventory.csv` should expose these columns:

- `session_id`
- `date`
- `run_id`
- `session_path`
- `subject_id`
- `device_id`
- `test_id`
- `has_gp3`
- `has_video`
- `has_recording_info`
- `has_marker`
- `has_calibration`
- `has_log`

## Downstream Consumers

- Data import uses `session_path` and file-presence columns.
- Quality checks use `session_id` and expected files.
- Metrics and visualisation use `date`, `device_id`, and `test_id` for grouping.

## Design Rule

The metadata module should not parse gaze samples. It only discovers sessions and metadata.
