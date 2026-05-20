"""Smoke checks for UTF-8 Chinese text in public entrypoints."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from main import QueryRequest


REPO_ROOT = Path(__file__).resolve().parents[2]
MOJIBAKE_MARKERS = (
    "\u9417",
    "\u9358",
    "\u93b4",
    "\u8930",
    "\u93c8",
    "\u20ac",
)


def test_query_request_accepts_chinese_subject_groups():
    for subject_group in ("物理", "历史"):
        request = QueryRequest(
            message="请帮我规划志愿",
            score=620,
            rank=12000,
            subject_group=subject_group,
        )

        assert request.subject_group == subject_group


def test_query_request_rejects_mojibake_subject_groups():
    with pytest.raises(ValidationError):
        QueryRequest(
            message="请帮我规划志愿",
            score=620,
            rank=12000,
            subject_group="\u9417\u2543\u608a",
        )


def test_public_status_files_do_not_contain_mojibake_markers():
    files = [
        REPO_ROOT / "backend" / "src" / "main.py",
        REPO_ROOT / "docs" / "current_project_status_overview.md",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        found = [marker for marker in MOJIBAKE_MARKERS if marker in text]
        assert not found, f"{path} contains mojibake markers: {found}"
