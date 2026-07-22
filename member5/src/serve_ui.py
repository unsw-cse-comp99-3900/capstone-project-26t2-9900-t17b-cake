"""Serve the Demo B package with a zero-dependency local web server."""

from __future__ import annotations

import argparse
import os
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    package_root = args.package_root.resolve()
    os.chdir(package_root)
    url = f"http://{args.host}:{args.port}/ui/index.html"
    server = ThreadingHTTPServer((args.host, args.port), NoCacheHandler)
    print(f"Demo B UI: {url}")
    print("Close this window or press Ctrl+C to stop the server.")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()


