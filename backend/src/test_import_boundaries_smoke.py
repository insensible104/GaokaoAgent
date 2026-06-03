"""Smoke checks for lightweight import boundaries.

The recommendation core should be usable without importing the full agent
runtime or LLM provider SDKs.  These checks protect fast domain-model tests from
accidental LangGraph/LangChain coupling.
"""

from __future__ import annotations

import importlib
import sys


def _assert_not_loaded(*module_names: str) -> None:
    loaded = [name for name in module_names if name in sys.modules]
    assert not loaded, f"unexpected heavyweight imports loaded: {loaded}"


def test_models_package_does_not_import_langgraph_by_default() -> None:
    importlib.import_module("models.game_matrix")

    _assert_not_loaded("langgraph")


def test_utils_package_does_not_import_llm_providers_by_default() -> None:
    importlib.import_module("utils")

    _assert_not_loaded("langchain_openai", "langchain_ollama", "langchain_google_genai")


def test_recommendation_submodule_import_does_not_import_llm_factory() -> None:
    importlib.import_module("recommendation.bundle_risk")

    _assert_not_loaded("langchain_openai", "utils.llm_factory")


def test_enrollment_loader_import_does_not_import_probability_stack() -> None:
    importlib.import_module("engines.enrollment_loader")

    _assert_not_loaded("scipy", "engines.probability")


def test_agents_package_does_not_import_llm_agents_by_default() -> None:
    importlib.import_module("agents")

    _assert_not_loaded("langchain_openai", "utils.llm_factory")


if __name__ == "__main__":
    test_models_package_does_not_import_langgraph_by_default()
    test_utils_package_does_not_import_llm_providers_by_default()
    test_recommendation_submodule_import_does_not_import_llm_factory()
    test_enrollment_loader_import_does_not_import_probability_stack()
    test_agents_package_does_not_import_llm_agents_by_default()
    print("import boundary smoke tests passed")
