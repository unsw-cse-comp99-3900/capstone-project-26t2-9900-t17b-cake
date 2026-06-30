from __future__ import annotations

import argparse
import csv
import logging
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkflowConfig:
    output_root: Path
    subject_id: str
    device_id: str
    test_id: str
    dry_run: bool = True


def next_session_folder(output_root: Path) -> Path:
    date_dir = output_root / time.strftime("%Y_%m_%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(p for p in date_dir.iterdir() if p.is_dir() and p.name[:3].isdigit())
    next_id = int(existing[-1].name[:3]) + 1 if existing else 0
    session_dir = date_dir / f"{next_id:03}"
    session_dir.mkdir()
    return session_dir


def write_recording_info(session_dir: Path, config: WorkflowConfig) -> None:
    rows = [
        ("Recording start time", time.time()),
        ("SubjectID", config.subject_id),
        ("EyeTrackerID", config.device_id),
        ("TestID", config.test_id),
        ("DryRun", config.dry_run),
    ]
    with (session_dir / "Recording_info.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def setup_logger(session_dir: Path) -> logging.Logger:
    logger = logging.getLogger("openet_workflow")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(session_dir / "application.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def run_workflow(config: WorkflowConfig) -> Path:
    session_dir = next_session_folder(config.output_root)
    logger = setup_logger(session_dir)
    write_recording_info(session_dir, config)

    logger.info("Session created: %s", session_dir)
    if config.dry_run:
        logger.info("Dry run mode: no hardware started")
    else:
        logger.info("Hardware mode requested; adapters should be started here")
        raise NotImplementedError("Live device adapters are not implemented in this starter module")

    logger.info("Workflow completed")
    return session_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--subject-id", required=True)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    session_dir = run_workflow(
        WorkflowConfig(
            output_root=args.output_root,
            subject_id=args.subject_id,
            device_id=args.device_id,
            test_id=args.test_id,
            dry_run=args.dry_run,
        )
    )
    print(f"Created session folder: {session_dir}")


if __name__ == "__main__":
    main()
