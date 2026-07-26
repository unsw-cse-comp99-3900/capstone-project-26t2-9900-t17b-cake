- # OpenET 2 Demo B v3 (2026-07-19)

  This version was rebuilt based on the client meeting, the original OpenET2 v1.5 figures, and the actual Demo B data. All new figures are standalone PNG files, so there is no need to view a montage to understand them. Both the filenames and figure titles specify the condition and the delay to four decimal places.

  ## Final Conclusion

  - Primary client comparison: `0.0500 s / 0.1000 s / 0.1500 s`.
  - Official recommendation: `0.0500 s` (50 ms).
  - Rationale: Although 100/150 ms slightly reduce spread, they slightly worsen accuracy. The paired bootstrap across 14 participants does not show any clear, non-conflicting improvement from the longer candidates. Following the meeting's shorter-if-equivalent rule, 50 ms was selected.
  - `0.0000–0.2000 s` is a secondary sensitivity scan, not the primary selection rule.
  - The OpenET2 example figure uses `0.6000 s` settling, nearest-target + 3.5×MAD visual QC, and a χ²=5.991 ellipse. It serves as a visual/statistical reference and is not a candidate delay for Demo B.

  ## One-Click Launch

  Open PowerShell in this folder:

  ```powershell
  PowerShell -ExecutionPolicy Bypass -File .\START_DEMO.ps1
  ```

  Then select:

  1. `Docker`: Rebuild the container, rerun the analysis, and open the UI.
  2. `Python`: Create `.venv`, install dependencies, rerun the analysis, and open the UI.
  3. `View`: Open the existing results without recalculating them.

  The HTML file cannot be opened by double-clicking because the page needs to load JSON and modules through a local HTTP server. The launcher automatically opens the correct address: `http://localhost:8765/ui/index.html`.

  If this folder has not yet been placed inside the original project, run:

  ```powershell
  PowerShell -ExecutionPolicy Bypass -File .\INSTALL_TO_ORIGINAL_LOCATION.ps1
  ```

  This copies the entire package to:

  `C:\Users\Lenovo\Desktop\demo B\climb_meeting_20260717_final\client_meeting_v3_REDESIGNED_20260719`

  ## How to Use the Folders

  - `DemoB_Client_Meeting_Delay_Evidence_REDESIGNED_2026-07-19.pptx`: A six-slide Demo B presentation; accuracy and spread each have a dedicated full-size figure slide.
  - `DemoB_Client_Meeting_OpenET2_Delay_Recheck_Report_ZH_2026-07-19.docx`: The complete Chinese report.
  - `CLIENT_MEETING_REQUIREMENTS_ZH.md`: Meeting timestamps and actionable requirements.
  - `FIGURE_GUIDE_ZH.md`: What each type of figure shows, why it exists, and how to interpret the filenames.
  - `CODE_WALKTHROUGH_ZH.md`: The code execution chain and explanations of the main functions.
  - `results/figures/primary_client_candidates/`: Two PRIMARY candidate figures.
  - `results/figures/extended_scan_by_condition/`: 63 standalone process figures covering 3 conditions × 21 delays.
  - `results/figures/recording_target_comparison/`: OpenET2-style figures for Calib, 10 min, 60 min, and ALL.
  - `results/figures/target_condition_selected_delay/`: 27 figures covering 9 targets × 3 conditions.
  - `results/figures/ellipse_per_recording_selected_delay/`: Empirical ellipse figures for 39 recordings.
  - `results/tables/figure_index.csv`: Figure-by-figure descriptions for all 149 figures.
  - `results/tables/selected_delay_client_rule.json`: The final selection and selection rule.
  - `src/`: Python analysis, UI manifest, server, and one-click launch code.
  - `ui/`: Local web interface.
  - `meeting_evidence/`: Meeting transcript files in JSON/SRT format.

  ## Example Figure Filename - under results file

  `S07__recording-target-comparison__condition-Acc_10min__delay-0.0500s__selected-0.0500s.png`

  - `S07`: PPT/presentation scope.
  - `recording-target-comparison`: The subject of the figure.
  - `condition-Acc_10min`: The 10-minute accuracy test.
  - `delay-0.0500s`: The delay actually used in this figure.
  - `selected-0.0500s`: The officially selected delay.

  ## Important Limitations

  - Degree coordinates still use the existing assumed FOV of `60° × 33.75°` because the current data does not include screen width/height or viewing distance.
  - `0.0500 s` is the project recommendation for this dataset under the meeting's rules. It should not be described as a universal human reaction time.
  - The OpenET-style χ² ellipse is used only for clear presentation. Client empirical 95% coverage is verified independently using the QA table and ellipse master.
