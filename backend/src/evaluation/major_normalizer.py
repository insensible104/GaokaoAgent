"""Major-code and major-name normalization for backtest matching."""

from __future__ import annotations

import re
import unicodedata


_PAREN_CONTENT_RE = re.compile(r"[\(（【\[].*?[\)）】\]]")
_PUNCT_RE = re.compile(r"[\s\-_·,，、;；:：/\\]+")


def normalize_major_name(value: object) -> str:
    """Return a conservative comparison key for major names."""
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    text = unicodedata.normalize("NFKC", text).lower()
    text = _PAREN_CONTENT_RE.sub("", text)
    text = _PUNCT_RE.sub("", text)
    return text


def major_names_match(left: object, right: object) -> bool:
    """Match exact or parenthetical-suffix variants without broad fuzziness."""
    left_key = normalize_major_name(left)
    right_key = normalize_major_name(right)
    if not left_key or not right_key:
        return False
    return left_key == right_key or (
        min(len(left_key), len(right_key)) >= 4
        and (left_key in right_key or right_key in left_key)
    )
