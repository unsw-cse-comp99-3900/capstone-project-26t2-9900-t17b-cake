"""Run the complete Demo B analysis, rebuild the UI manifest, and open the UI."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> None:
    print("\n>", " ".join(f'"{item}"' if " " in item else item for item in command))
    subprocess.run(command, check=True)


def main() -> None:
    package_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=package_root.parent / "input_data" / "ET acc testing data",
    )
    parser.add_argument("--skip-analysis", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if not args.skip_analysis:
        data_root = args.data_root.resolve()
        if not data_root.exists():
            raise FileNotFoundError(
                f"Input data not found: {data_root}\n"
                "Place this package inside climb_meeting_20260717_final or pass --data-root."
            )
        run(
            [
                sys.executable,
                str(package_root / "src" / "analyze_client_meeting_v2.py"),
                "--data-root",
                str(data_root),
                "--output-root",
                str(package_root / "results"),
                "--delays-s",
                "0.00:0.20:0.01",
                "--coverage",
                "0.95",
                "--bootstrap-repetitions",
                "3000",
            ]
        )

    run(
        [
            sys.executable,
            str(package_root / "src" / "build_ui_manifest.py"),
            "--package-root",
            str(package_root),
        ]
    )
    serve = [
        sys.executable,
        str(package_root / "src" / "serve_ui.py"),
        "--package-root",
        str(package_root),
        "--port",
        str(args.port),
    ]
    if args.no_browser:
        serve.append("--no-browser")
    run(serve)


if __name__ == "__main__":
    main()

