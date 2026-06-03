"""Quant engine convenience exports.

Avoid importing all numeric subsystems from the package initializer.  Focused
imports such as ``engines.enrollment_loader`` should not require scipy or the
full probability stack unless those functions are actually used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .adjustment_sim import simulate_adjustment
    from .probability import calculate_admission_probability
    from .quant_engine import GaokaoQuantEngine
    from .quant_signals import calculate_fear_index, calculate_volatility

_LAZY_EXPORTS = {
    "GaokaoQuantEngine": ("engines.quant_engine", "GaokaoQuantEngine"),
    "calculate_admission_probability": ("engines.probability", "calculate_admission_probability"),
    "calculate_fear_index": ("engines.quant_signals", "calculate_fear_index"),
    "calculate_volatility": ("engines.quant_signals", "calculate_volatility"),
    "simulate_adjustment": ("engines.adjustment_sim", "simulate_adjustment"),
}


def __getattr__(name: str) -> Any:
    """Resolve engine exports on demand."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY_EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "GaokaoQuantEngine",
    "calculate_admission_probability",
    "calculate_fear_index",
    "calculate_volatility",
    "simulate_adjustment",
]
