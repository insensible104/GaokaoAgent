"""Backend source package bootstrap.

Route A (FastAPI) expects the app to be started via `uvicorn src.main:app`.

Most modules under `backend/src/` use top-level imports like `from models...`,
`from agents...`, etc. Those imports require `backend/src` to be on `sys.path`.

When `uvicorn` imports `src.main`, Python adds `backend/` (not `backend/src/`)
to `sys.path`, so we add `backend/src` here to keep imports consistent.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

