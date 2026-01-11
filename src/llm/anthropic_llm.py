"""Anthropic Claude LLM implementation."""

from typing import Optional

import anthropic

from .base import BaseLLM, QueryResult
from src.config import config


class AnthropicLLM(BaseLLM):
    """Anthropic Claude implementation.

    Uses the Anthropic API to query Claude models about Ultimate Frisbee rules.
    """

    def __init__(
        self,
        rulebook: str = "usau",
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        """Initialize Anthropic LLM.

        Args:
            rulebook: Which rulebook to use ("usau", "wfdf", or "both")
            model: Anthropic model to use
            api_key: Anthropic API key (defaults to config.yaml)
            temperature: Response temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        super().__init__(rulebook)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = anthropic.Anthropic(
            api_key=api_key or config.get_api_key("anthropic")
        )
        self._last_usage: Optional[dict] = None

    @property
    def model_name(self) -> str:
        return self._model

    def _query_llm(self, prompt: str) -> str:
        """Send query to Anthropic API."""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        self._last_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return response.content[0].text

    def _parse_response(self, response: str) -> QueryResult:
        """Parse response with token usage from Anthropic."""
        result = super()._parse_response(response)
        if self._last_usage:
            result.tokens_used = (
                self._last_usage["input_tokens"] + self._last_usage["output_tokens"]
            )
        return result
