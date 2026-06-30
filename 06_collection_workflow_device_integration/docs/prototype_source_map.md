# Prototype Source Map

Existing prototype scripts that may be reused later:

- `GP3_helpers.py`: GP3HD process control and socket data parsing
- `GP3_calibration.py`: GP3 calibration flow with Aruco event synchronisation
- `tobii_helpers.py`: Tobii discovery and subscription starter code
- `cv2_utilities.py`: video capture helpers
- `display_markers_on_2screen.py`: accuracy target display
- `testing_GP3V2_Tobii_recording_display.py`: earlier combined recording script

Do not copy these scripts blindly into production. First extract clean adapter interfaces:

- `start_device()`
- `start_recording()`
- `stop_recording()`
- `write_samples()`
- `close_device()`

Each adapter should be testable in dry-run mode.
