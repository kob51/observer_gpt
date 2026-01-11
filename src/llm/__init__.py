"""LLM providers for Ultimate Frisbee rules queries."""

from .base import BaseLLM, QueryResult
from .openai_llm import OpenAILLM
from .anthropic_llm import AnthropicLLM
from .gemini_llm import GeminiLLM

__all__ = ["BaseLLM", "QueryResult", "OpenAILLM", "AnthropicLLM", "GeminiLLM"]


# Model registry for easy lookup
AVAILABLE_MODELS = {
    "gpt-4o-mini": {
        "provider": "openai",
        "class": OpenAILLM,
        "display_name": "GPT-4o Mini",
    },
    "gpt-4o": {
        "provider": "openai",
        "class": OpenAILLM,
        "display_name": "GPT-4o",
    },
    "claude-sonnet-4-20250514": {
        "provider": "anthropic",
        "class": AnthropicLLM,
        "display_name": "Claude Sonnet 4",
    },
    "claude-3-5-haiku-20241022": {
        "provider": "anthropic",
        "class": AnthropicLLM,
        "display_name": "Claude 3.5 Haiku",
    },
    "gemini-2.5-flash": {
        "provider": "google",
        "class": GeminiLLM,
        "display_name": "Gemini 2.5 Flash",
    },
    "gemini-2.5-pro": {
        "provider": "google",
        "class": GeminiLLM,
        "display_name": "Gemini 2.5 Pro",
    },
}


def get_llm(model: str, rulebook: str = "usau") -> BaseLLM:
    """Factory function to get an LLM instance by model name.

    Args:
        model: Model identifier (e.g., "gpt-4o-mini", "claude-sonnet-4-20250514")
        rulebook: Which rulebook to use ("usau", "wfdf", or "both")

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If model is not recognized
    """
    if model not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown model: {model}. Available: {list(AVAILABLE_MODELS.keys())}")

    model_info = AVAILABLE_MODELS[model]
    return model_info["class"](rulebook=rulebook, model=model)
