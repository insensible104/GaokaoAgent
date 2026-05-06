"""Thin wrapper for the unified GaokaoAgent CLI."""

from __future__ import annotations

from pathlib import Path
import sys


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from gaokao_agent_cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
