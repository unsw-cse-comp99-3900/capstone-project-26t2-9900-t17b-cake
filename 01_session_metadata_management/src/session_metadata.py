from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class SessionRecord:
    session_id: str
    date: str
    run_id: str
    session_path: str
    subject_id: str = ""
    device_id: str = ""
    test_id: str = ""
    has_gp3: bool = False
    has_video: bool = False
    has_recording_info: bool = False
    has_marker: bool = False
    has_calibration: bool = False
    has_log: bool = False


def read_recording_info(path: Path) -> dict[str, str]:
    recording_info: dict[str, str] = {}

    if not path.exists():
        return recording_info

    with path.open(newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 2:
                continue

            key = row[0].strip()
            if key == "":
                continue

            recording_info[key] = row[1].strip()

    return recording_info


def discover_sessions(data_root: Path) -> list[SessionRecord]:
    session_records: list[SessionRecord] = []
    date_folders: list[Path] = []

    for item in data_root.iterdir():
        if item.is_dir():
            date_folders.append(item)

    date_folders.sort()

    for date_folder in date_folders:
        run_folders: list[Path] = []

        for item in date_folder.iterdir():
            if item.is_dir():
                run_folders.append(item)

        run_folders.sort()

        for run_folder in run_folders:
            recording_info_path = run_folder / "Recording_info.csv"
            recording_info = read_recording_info(recording_info_path)

            has_calibration_file = False
            for _ in run_folder.glob("*.cal"):
                has_calibration_file = True
                break

            session_record = SessionRecord(
                session_id=f"{date_folder.name}/{run_folder.name}",
                date=date_folder.name,
                run_id=run_folder.name,
                session_path=str(run_folder),
                subject_id=recording_info.get("SubjectID", ""),
                device_id=recording_info.get(
                    "EyeTrackerID",
                    recording_info.get("EyeTracker ID", ""),
                ),
                test_id=recording_info.get("TestID", ""),
                has_gp3=(run_folder / "GP3HD_data.csv").exists(),
                has_video=(run_folder / "Video_data.csv").exists(),
                has_recording_info=recording_info_path.exists(),
                has_marker=(run_folder / "acc_marker_external.csv").exists(),
                has_calibration=has_calibration_file
                or (run_folder / "Calibration_info.txt").exists(),
                has_log=(run_folder / "application.log").exists(),
            )

            session_records.append(session_record)

    return session_records


def write_outputs(records: list[SessionRecord], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for record in records:
        rows.append(asdict(record))

    if len(rows) == 0:
        output.write_text("", encoding="utf-8")
        return

    field_names = list(rows[0].keys())

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)

    json_output = output.with_suffix(".json")
    json_output.write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/session_inventory.csv"),
    )
    args = parser.parse_args()

    records = discover_sessions(args.data_root)
    write_outputs(records, args.output)

    print(f"Discovered {len(records)} sessions")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()