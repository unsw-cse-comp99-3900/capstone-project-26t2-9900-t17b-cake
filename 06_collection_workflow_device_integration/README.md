# 06 Collection Workflow Device Integration

Owner responsibility: design and integrate the guided data-collection workflow for devices and recordings.

## Goal

Create a repeatable workflow that can eventually coordinate calibration, validation, recording, stimulus presentation, metadata logging, and safe session shutdown.

## Inputs

- Device configuration
- Participant/test/session metadata
- Existing prototype scripts for GP3HD, Tobii, video capture, Aruco markers, and stimulus display

## Outputs

- Session folder creation workflow
- Recording metadata template
- Dry-run workflow for testing without hardware
- Integration plan for live GP3HD/Tobii/video modules

## Run

```bash
python src/collection_workflow.py --output-root outputs --subject-id TEST01 --device-id GP3HD --test-id "Calib & Acc" --dry-run
```

## Acceptance Criteria

- Create a consistent session folder.
- Write `Recording_info.csv`.
- Support dry-run mode without hardware.
- Document how GP3HD, Tobii, video capture, and stimulus scripts will be plugged in.
- Never hard-code one lab computer path.

## Sprint 1 Boundary

This task should stabilise the workflow contract first. Real hardware calls should be guarded behind explicit configuration and safe start/stop handling.
