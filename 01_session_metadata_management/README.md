# 01 Session Metadata Management

Owner responsibility: define and implement the standard session structure for OpenET 2.

## Goal

Turn raw dated recording folders into a clean session inventory with consistent IDs, metadata fields, and file-presence checks.

## Inputs

- Existing recording folders such as `ET acc testing data/2025_04_11/000`
- `Recording_info.csv`
- Optional calibration files and logs

## Outputs

- `session_inventory.csv`
- `session_inventory.json`
- A documented metadata schema for downstream modules

## Run

```bash
python src/session_metadata.py --data-root "../ET acc testing data" --output outputs/session_inventory.csv
```

## Acceptance Criteria

- Detect all available sessions under a data root.
- Generate stable session IDs in the form `YYYY_MM_DD/run_id`.
- Extract subject ID, device ID, test ID, and file availability.
- Do not hard-code local user paths.
- Include tests for missing metadata and missing files.

## GitHub Notes

This folder is safe to publish. Do not commit raw session data. Put local datasets in `data/`, which is ignored.
