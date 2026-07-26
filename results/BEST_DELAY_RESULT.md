# Client-meeting-first delay result

Recommended delay under the meeting rule: **0.0500 s**.

This is not the minimum of an accuracy-plus-ellipse score. The meeting asked to compare 50, 100, and 150 ms on two separate outcomes: closeness to the target and reduction of spread. Participant-level paired bootstrap intervals did not show a clear, non-conflicting improvement for the longer candidates. The meeting's tie rule therefore selects the shortest candidate, 50 ms.

## Client candidate medians

| delay | balanced accuracy (deg) | balanced repeat spread (deg) | valid windows |
|---:|---:|---:|---:|
| 0.0500 s | 2.8906 | 0.5912 | 959 |
| 0.1000 s | 2.9314 | 0.5777 | 955 |
| 0.1500 s | 2.9629 | 0.5707 | 952 |

## Selections by test ID

- Calib & Acc: 0.0500 s
- Acc 10min: 0.0500 s
- Acc 60min: 0.0500 s

## Interpretation limits

- The 0.0000–0.2000 s scan is a sensitivity analysis added by the analyst; the client explicitly named only 0.0500, 0.1000, and 0.1500 s.
- The 95% ellipse is checked after delay selection. It is not part of the primary selection score.
- Degree coordinates use the existing 60° × 33.75° field-of-view assumption because physical screen/viewing geometry is absent.
- The result is an evidence-based exploratory recommendation, not a universally validated physiological reaction-time estimate.

Pairwise bootstrap rows: 12; see `tables/client_candidate_pairwise_bootstrap.csv`.
