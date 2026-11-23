#!/usr/bin/env python3
"""PoseFit launcher alias under posefit/scripts/run.py."""

from __future__ import annotations

import sys
from pathlib import Path

# Delegate directly to root scripts/run.py
ROOT_RUN = Path(__file__).resolve().parent.parent.parent / "scripts" / "run.py"
if ROOT_RUN.exists():
    with open(ROOT_RUN, "rb") as f:
        exec(compile(f.read(), str(ROOT_RUN), "exec"))
else:
    sys.stderr.write("Could not locate scripts/run.py\n")
    sys.exit(1)
