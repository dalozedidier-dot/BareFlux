from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

existing_pythonpath = os.environ.get("PYTHONPATH")
if existing_pythonpath:
    os.environ["PYTHONPATH"] = os.pathsep.join([str(SRC), existing_pythonpath])
else:
    os.environ["PYTHONPATH"] = str(SRC)
