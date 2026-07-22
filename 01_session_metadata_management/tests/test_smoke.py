from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from session_metadata import read_recording_info


def test_missing_recording_info_returns_empty_dict():
    assert read_recording_info(Path("does_not_exist.csv")) == {}
