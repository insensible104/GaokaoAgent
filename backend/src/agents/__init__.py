"""Agent exports for the GaokaoAgent supervisor graph.

Agent modules have different dependency profiles.  For example, importing the
critic or profiling agent touches the LLM factory, while importing the game
agent only needs the recommendation stack.  Resolve exports lazily so focused
imports such as ``agents.game_agent`` do not require every agent dependency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .critic_agent_enhanced import critic_agent_node
    from .deep_research_agent import deep_research_agent_node
    from .deliberation_agents import (
        deliberation_coordinator_node,
        evidence_guardian_agent_node,
        opportunity_advocate_agent_node,
        risk_guardian_agent_node,
    )
    from .game_agent import game_agent_node
    from .multimodal_agent import multimodal_agent_node
    from .profiling_agent import profiling_agent_node
    from .report_agent import report_agent_node
    from .router_agent import router_agent_node

_LAZY_EXPORTS = {
    "router_agent_node": ("agents.router_agent", "router_agent_node"),
    "profiling_agent_node": ("agents.profiling_agent", "profiling_agent_node"),
    "game_agent_node": ("agents.game_agent", "game_agent_node"),
    "report_agent_node": ("agents.report_agent", "report_agent_node"),
    "critic_agent_node": ("agents.critic_agent_enhanced", "critic_agent_node"),
    "deep_research_agent_node": ("agents.deep_research_agent", "deep_research_agent_node"),
    "multimodal_agent_node": ("agents.multimodal_agent", "multimodal_agent_node"),
    "risk_guardian_agent_node": ("agents.deliberation_agents", "risk_guardian_agent_node"),
    "opportunity_advocate_agent_node": ("agents.deliberation_agents", "opportunity_advocate_agent_node"),
    "evidence_guardian_agent_node": ("agents.deliberation_agents", "evidence_guardian_agent_node"),
    "deliberation_coordinator_node": ("agents.deliberation_agents", "deliberation_coordinator_node"),
}


def __getattr__(name: str) -> Any:
    """Resolve agent exports on demand."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY_EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "router_agent_node",
    "profiling_agent_node",
    "game_agent_node",
    "report_agent_node",
    "critic_agent_node",
    "deep_research_agent_node",
    "multimodal_agent_node",
    "risk_guardian_agent_node",
    "opportunity_advocate_agent_node",
    "evidence_guardian_agent_node",
    "deliberation_coordinator_node",
]
