"""Prompt 模板模块"""
from .profiling import profiling_system_prompt, profiling_user_prompt
from .game import game_analysis_prompt
from .report import report_generation_prompt
from .critic import critic_audit_prompt

__all__ = [
    "profiling_system_prompt",
    "profiling_user_prompt",
    "game_analysis_prompt",
    "report_generation_prompt",
    "critic_audit_prompt",
]
