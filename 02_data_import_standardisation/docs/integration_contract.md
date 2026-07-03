# Integration Contract

## Standard Gaze Table

`standard_gaze.csv` columns:

- `time_s`
- `gaze_x`
- `gaze_y`
- `valid`
- `source_device`
- `raw_cx`
- `raw_cy`

## Standard Video Timestamp Table

`standard_video_timestamps.csv` columns:

- `frame_id`
- `time_s`

## Standard Marker Event Table

`standard_marker_events.csv` columns:

- `marker_start_s`
- `marker_end_s`
- `marker_id`

## Design Rule

Importers clean and standardise data, but they do not decide whether a recording is good or bad. Quality decisions belong to task 03.
