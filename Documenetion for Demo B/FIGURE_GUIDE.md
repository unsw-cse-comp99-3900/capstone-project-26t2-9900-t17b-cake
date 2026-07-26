# Figure Description and Naming Guide

## Naming Structure

`scope__topic__condition-XXX__delay-0.0500s__selected-0.0500s.png`

- `S03/S04/S06/S07/S08`: Correspond to evidence slides in the PPT.
- `DETAIL`: Process-level or local evidence.
- `SECONDARY`: 0–200 ms sensitivity scan.
- `QA`: Ellipse coverage/centre/area checks.
- Delays are always expressed in seconds to four decimal places, and the condition is always included in the filename.

## What Each Type of Figure Shows

| Folder                                 | Count | What It Shows                                                | Why It Is Needed                                             |
| -------------------------------------- | ----: | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `primary_client_candidates`            |     2 | Accuracy/spread for the three client candidates              | Directly answers the primary delay question                  |
| `metric_curves`                        |     8 | Complete 0–200 ms curves                                     | Secondary sensitivity analysis/audit                         |
| `extended_scan_by_condition`           |    63 | A standalone process scatter plot for every condition and delay | Avoids compressing the process into a montage                |
| `selected_delay_by_condition`          |     3 | Overview of the selected delay across the three stages       | Quickly presents Calib/10/60                                 |
| `target_condition_selected_delay`      |    27 | Local evidence for every target and stage                    | Checks target centre/spread                                  |
| `ellipse_per_recording_selected_delay` |    39 | A raw-gaze empirical ellipse for each recording              | Cross-checks the ellipse master and coverage                 |
| `recording_target_comparison`          |     4 | OpenET2-style recording × target means                       | Provides a clear presentation using equal-area markers, visual QC, and χ² ellipses |
| `ellipse_quality_assurance`            |     3 | Coverage, centre error, and area                             | Validates ellipses after selecting the delay                 |

`results/tables/figure_index.csv` provides `what_it_shows` and `why_it_exists` for each of the 149 figures. Use it as the master index when a figure-by-figure explanation is required.

## Difference Between OpenET-Style Figures and Client Ellipses

- OpenET-style figures: nearest-target + 3.5×MAD visual QC and parametric χ² 95% ellipses; used only for clear comparisons across recordings.
- Client QA: raw-gaze empirical quantile ellipses; ensures that at least 95% of input points fall within the ellipse; used to validate the master table and coverage.
- Neither is included in the delay score.
