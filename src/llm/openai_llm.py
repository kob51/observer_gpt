"""OpenAI/ChatGPT LLM implementation."""

from typing import Optional

from openai import OpenAI

from .base import BaseLLM, QueryResult
from src.config import config


class OpenAILLM(BaseLLM):
    """OpenAI ChatGPT implementation.

    Uses the OpenAI API to query GPT models about Ultimate Frisbee rules.
    """

    def __init__(
        self,
        rulebook: str = "usau",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
    ):
        """Initialize OpenAI LLM.

        Args:
            rulebook: Which rulebook to use ("usau", "wfdf", or "both")
            model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
            api_key: OpenAI API key (defaults to config.yaml)
            temperature: Response temperature (lower = more deterministic)
        """
        super().__init__(rulebook)
        self._model = model
        self._temperature = temperature
        self._client = OpenAI(api_key=api_key or config.get_api_key("openai"))
        self._last_usage: Optional[dict] = None

    @property
    def model_name(self) -> str:
        return self._model

    def _query_llm(self, prompt: str) -> str:
        """Send query to OpenAI API."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=self._temperature,
        )

        self._last_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        return response.choices[0].message.content

    def _parse_response(self, response: str) -> QueryResult:
        """Parse response with token usage from OpenAI."""
        result = super()._parse_response(response)
        if self._last_usage:
            result.tokens_used = self._last_usage["total_tokens"]
        return result
