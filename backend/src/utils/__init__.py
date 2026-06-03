"""Utility exports.

The LLM factory imports provider SDKs.  Resolve it lazily so utility submodules
that do not need an LLM can be imported in lightweight smoke tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .llm_factory import get_llm


def __getattr__(name: str) -> Any:
    """Load provider-backed utilities only when explicitly used."""
    if name != "get_llm":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .llm_factory import get_llm

    globals()[name] = get_llm
    return get_llm

__all__ = ["get_llm"]
