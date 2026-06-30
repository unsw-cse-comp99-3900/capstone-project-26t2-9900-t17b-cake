# Integration Contract

## Session Folder Contract

The workflow should create:

```text
<output-root>/
  YYYY_MM_DD/
    000/
      Recording_info.csv
      application.log
```

Live device modules may later add:

- `GP3HD_data.csv`
- `Tobii_data.csv`
- `Video_data.csv`
- `acc_marker_external.csv`
- `ext_display_acc_video.avi`
- calibration outputs

## Workflow States

- `created`
- `calibration_started`
- `recording_started`
- `stimulus_running`
- `recording_stopped`
- `completed`
- `failed`

## Design Rule

Device-specific code should sit behind adapter functions. The workflow should not directly depend on one hardware SDK in its core logic.
