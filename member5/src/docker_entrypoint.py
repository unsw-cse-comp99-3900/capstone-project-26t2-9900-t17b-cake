"""Docker entry point: optionally rerun analysis, build UI data, then serve."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> None:
    print(">", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if os.environ.get("RUN_ANALYSIS", "0") == "1":
        data_root = Path(os.environ.get("DATA_ROOT", "/data/ET acc testing data"))
        run(
            [
                sys.executable,
                str(root / "src" / "analyze_client_meeting_v2.py"),
                "--data-root",
                str(data_root),
                "--output-root",
                str(root / "results"),
                "--delays-s",
                "0.00:0.20:0.01",
                "--coverage",
                "0.95",
            ]
        )
    run([sys.executable, str(root / "src" / "build_ui_manifest.py"), "--package-root", str(root)])
    run(
        [
            sys.executable,
            str(root / "src" / "serve_ui.py"),
            "--package-root",
            str(root),
            "--host",
            "0.0.0.0",
            "--port",
            "8765",
            "--no-browser",
        ]
    )


if __name__ == "__main__":
    main()


