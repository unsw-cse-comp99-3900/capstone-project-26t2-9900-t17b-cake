# Project requirements traceability

| Brief requirement | Implementation | Verification |
|---|---|---|
| 1. Extend existing OpenET | `legacy.py` compatibility boundary; unified `src/openet2` architecture; unchanged client baseline | Original folder-contract and legacy-time tests |
| 2. Structured sessions | `SessionRecord`, CSV+JSON metadata, dated/run folders, trial/condition/timestamps/calibration | Rich metadata and dry-run tests |
| 3. Collection workflow | calibration -> validation -> recording/stimulus/video -> stop -> completion states | Dry-run output/event test; structured device calibration import; planned vs Pygame-flip marker timing; hardware checklist for live |
| 4. Device and metadata | model/serial/software/rate/calibration/display/environment/operator fields | Metadata merge test and inventory output |
| 5. Multi-format import | CSV/TSV/JSON tabular importer plus registration API and GP3/Tobii aliases; optional strictly validated AVI target recovery | Parameterised three-format tests; video nine-point/three-repeat recovery test; 39-video audit |
| 6. Quality checks | missing/invalid samples, gaps, duplicates, irregularity, coordinates, incomplete recording, missing/conflicting/unreadable metadata, calibration, markers, video | Gap, metadata-conflict, malformed-JSON, pipeline, and client-data tests |
| 7. Benchmark metrics | duration/rate/loss/precision/stability/systematic/random/accuracy/angular/repeatability; configurable 0.6 s target settling with exclusion evidence; paper-criteria applicability table | Marker, settling-window, angular, unit-aware calibration, and repeatability tests |
| 8. Visualisation | up to seven focused cohort figures: sampling rate, valid-sample rate, non-empty QC flags, date-level comparison, QC-filtered target locations, QC-filtered error/eccentricity, and QC-filtered target layout/coverage; four-panel per-session review; HTML report. Unfiltered target diagnostics remain in auditable CSV/JSON fields rather than presentation charts. | Pipeline integration test, target-level/QC/ellipse regression tests, visual inspection, and generated artifacts |
| 9. Long-term comparison | date/device/test/condition cohort summary plus separately identified participant-matched repeatability | Participant separation test and three-date synthetic end-to-end dataset |
| 10. Documentation/usability | CLI, example datasets/workflows, README, user/developer/metrics/Docker/hardware/research guides, technical report | Example pipelines, Windows CI, and documentation review |

## External verification boundary

All offline requirements and the complete no-hardware collection contract are
automatically tested. Physical GP3/Tobii calibration, SDK compatibility, monitor
selection, timing latency, and achieved frame rate require the client/lab
devices and are verified using `hardware_validation_checklist.md`.

## Research-readiness controls

The optional research protocol adds visit labels, display and environment
fields, calibration-confidence evidence, target-duration capacity validation,
application-level timing summaries, report evidence-status labels, and portable
SHA-256 input provenance. These controls strengthen requirements 2-4, 7, 9,
and 10 without altering supplied source data or treating hardware validation as
an automated software result.
