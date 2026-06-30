from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collection_workflow import WorkflowConfig, run_workflow


def test_dry_run_creates_recording_info(tmp_path):
    session_dir = run_workflow(
        WorkflowConfig(
            output_root=tmp_path,
            subject_id="TEST01",
            device_id="GP3HD",
            test_id="Calib & Acc",
            dry_run=True,
        )
    )
    assert (session_dir / "Recording_info.csv").exists()
