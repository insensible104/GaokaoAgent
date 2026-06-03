"""Core data-model exports.

Keep this package initializer lightweight.  Some modules under ``models`` are
plain Pydantic schemas, while ``state`` depends on LangGraph.  Importing
LangGraph from here makes simple domain-model tests require the full agent
runtime, so heavyweight exports are resolved lazily.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .audit_result import AuditResult, AuditStatus
from .game_matrix import GameMatrix, GameRow, StrategyTag, VolatilityLevel
from .user_profile import HollandCode, RiskTolerance, UserProfile

if TYPE_CHECKING:
    from .report import ReportDraft
    from .state import SupervisorState

_LAZY_EXPORTS = {
    "ReportDraft": ("models.report", "ReportDraft"),
    "SupervisorState": ("models.state", "SupervisorState"),
}


def __getattr__(name: str) -> Any:
    """Load heavier model exports only when callers explicitly request them."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY_EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "UserProfile",
    "RiskTolerance",
    "HollandCode",
    "GameMatrix",
    "GameRow",
    "StrategyTag",
    "VolatilityLevel",
    "ReportDraft",
    "AuditResult",
    "AuditStatus",
    "SupervisorState",
]
