"""LLM providers for Ultimate Frisbee rules queries."""

from .base import BaseLLM, QueryResult
from .gemini_llm import GeminiLLM

__all__ = ["BaseLLM", "QueryResult", "GeminiLLM", "get_llm"]


def get_llm(rulebook: str = "usau") -> BaseLLM:
    """Get the default LLM instance (Gemini).

    Args:
        rulebook: Which rulebook to use ("usau", "wfdf", or "both")

    Returns:
        Configured GeminiLLM instance
    """
    from src.config import config
    model = config.get_default_model()
    return GeminiLLM(rulebook=rulebook, model=model)
