# 02 Data Import Standardisation

## Overview

The **02_data_import_standardisation** module imports raw eye-tracking data and converts it into a standard OpenET format. It is the first step of the offline analysis pipeline and provides consistent data for all downstream modules.

---

## Goal

- Import raw eye-tracking files.
- Standardise different device formats.
- Generate common CSV outputs for later analysis.
- Support future eye-tracking formats without changing downstream modules.

---

## Inputs

Current supported files:

- `GP3HD_data.csv`
- `Video_data.csv`
- `acc_marker_external.csv`

Future formats may include:

- Tobii CSV
- TSV
- JSON
- Other structured exports

---

## Outputs

The module generates three standard files:

- `standard_gaze.csv`
- `standard_video_timestamps.csv`
- `standard_marker_events.csv`

These outputs are used by the Quality Check, Benchmark, and Visualisation modules.

---

## Running

```bash
python src/data_importer.py \
    --session-path "../ET acc testing data/2025_04_12/001" \
    --output-dir outputs/2025_04_12_001
```

---

## Acceptance Criteria

- Read GP3HD files with different time column names.
- Convert gaze coordinates and validity into numeric values.
- Produce consistent output column names.
- Allow new importers to be added without modifying downstream modules.

---

## Design

This module follows a modular design by separating data import from later analysis tasks. All device-specific data is converted into a unified OpenET format, allowing other modules to process data without knowing the original file structure.

---

## Summary

This module provides a reliable data ingestion layer for the project. By standardising raw eye-tracking data into a common format, it ensures compatibility, maintainability, and scalability across the entire analysis pipeline.
