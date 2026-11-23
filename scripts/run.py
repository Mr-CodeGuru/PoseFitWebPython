#!/usr/bin/env python3
"""Cross-platform PoseFit launcher (Windows PowerShell/CMD, Linux/macOS sh).

Zero bash assumptions. Uses pathlib.Path everywhere.
Checks the Python runtime environment, validates built frontend assets,
spawns the FastAPI/Uvicorn server, and opens the user's default browser.
"""

from __future__ import annotations

import argparse
import sys
import time
import webbrowser
from pathlib import Path

# Verify Python version requirement: Python >= 3.11
if sys.version_info < (3, 11):  # noqa: UP036
    sys.stderr.write(
        f"ERROR: PoseFit requires Python 3.11 or newer.\n"
        f"Currently running on Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}.\n"
    )
    sys.exit(1)

# Ensure posefit src is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
POSEFIT_SRC = REPO_ROOT / "posefit" / "src"
if POSEFIT_SRC.exists() and str(POSEFIT_SRC) not in sys.path:
    sys.path.insert(0, str(POSEFIT_SRC))

DIST_PATH = REPO_ROOT / "web" / "dist"


def check_environment() -> None:
    """Checks core runtime dependencies."""
    missing: list[str] = []
    for mod in ("numpy", "fastapi", "uvicorn", "pydantic", "yaml"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        sys.stderr.write(
            f"ERROR: Missing required dependencies: {', '.join(missing)}\n"
            f"Please run: pip install -e {REPO_ROOT / 'posefit'}\n"
        )
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PoseFit local-first AI coach launcher",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind to (strictly 127.0.0.1 for local privacy)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to serve on",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the default web browser",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable uvicorn hot reloading for development",
    )
    return parser.parse_args()


def main() -> None:
    check_environment()
    args = parse_args()

    # Inform user about frontend asset state
    if not (DIST_PATH / "index.html").exists():
        sys.stdout.write(
            f"\n[NOTE] Built frontend not found at: {DIST_PATH}\n"
            f"To build the React UI, run:\n"
            f"  cd {REPO_ROOT / 'web'}\n"
            f"  npm run build\n"
            f"Static SPA hosting will fall back when built.\n\n"
        )
    else:
        sys.stdout.write(f"[OK] Frontend assets verified at: {DIST_PATH}\n")

    url = f"http://{args.host}:{args.port}"
    sys.stdout.write(f"Starting PoseFit AI Coach on {url} ...\n")

    if not args.no_browser:
        # Schedule browser opening in background after server socket opens
        import threading

        def _open_browser() -> None:
            time.sleep(1.2)
            webbrowser.open(url)

        threading.Thread(target=_open_browser, daemon=True).start()

    import uvicorn

    uvicorn.run(
        "posefit.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
