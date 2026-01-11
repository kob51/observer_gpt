"""Google Gemini LLM implementation."""

from typing import Optional

from google import genai
from google.genai import types

from .base import BaseLLM, QueryResult
from src.config import config


class GeminiLLM(BaseLLM):
    """Google Gemini implementation.

    Uses the Google GenAI API to query Gemini models about Ultimate Frisbee rules.
    """

    def __init__(
        self,
        rulebook: str = "usau",
        model: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
    ):
        """Initialize Gemini LLM.

        Args:
            rulebook: Which rulebook to use ("usau", "wfdf", or "both")
            model: Gemini model to use
            api_key: Google API key (defaults to config.yaml)
            temperature: Response temperature (lower = more deterministic)
        """
        super().__init__(rulebook)
        self._model_name = model
        self._temperature = temperature

        # Initialize the client
        self._client = genai.Client(
            api_key=api_key or config.get_api_key("google")
        )
        self._last_usage: Optional[dict] = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _query_llm(self, prompt: str) -> str:
        """Send query to Gemini API."""
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self._temperature,
            ),
        )

        # Gemini provides token counts in usage_metadata
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            self._last_usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
            }

        return response.text

    def stream_query(self, prompt: str):
        """Stream query to Gemini API, yielding chunks as they arrive."""
        response = self._client.models.generate_content_stream(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self._temperature,
            ),
        )

        full_text = ""
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                yield chunk.text

            # Capture usage from final chunk
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                self._last_usage = {
                    "prompt_tokens": chunk.usage_metadata.prompt_token_count,
                    "completion_tokens": chunk.usage_metadata.candidates_token_count,
                }

    def _parse_response(self, response: str) -> QueryResult:
        """Parse response with token usage from Gemini."""
        result = super()._parse_response(response)
        if self._last_usage:
            result.tokens_used = (
                self._last_usage.get("prompt_tokens", 0) +
                self._last_usage.get("completion_tokens", 0)
            )
        return result
