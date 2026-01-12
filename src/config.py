"""Configuration management for Observer-GPT."""

from pathlib import Path
from typing import Optional

import yaml


class Config:
    """Centralized configuration for API keys and settings.

    Loads configuration from config.yaml in the project root.
    Currently supports Google Gemini as the LLM provider.
    """

    _instance: Optional["Config"] = None
    _config: dict = {}

    def __new__(cls):
        """Singleton pattern - only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from config.yaml."""
        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            with open(config_path) as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider.

        Args:
            provider: Provider name (currently only "google" is supported)

        Returns:
            API key string or None if not configured
        """
        try:
            key = self._config.get(provider, {}).get("api_key")
            return key
        except:
            raise RuntimeError(f"Error retrieving API key for provider: {provider}")

    def get_default_model(self) -> str:
        """Get the default model."""
        return self._config.get("defaults", {}).get("model", "gemini-2.0-flash")

    def get_default_rulebook(self) -> str:
        """Get the default rulebook."""
        return self._config.get("defaults", {}).get("rulebook", "usau")

    # RAG settings
    def is_rag_enabled(self) -> bool:
        """Check if RAG mode is enabled."""
        return self._config.get("rag", {}).get("enabled", False)

    def get_rag_top_k(self) -> int:
        """Get number of chunks to retrieve in RAG mode."""
        return self._config.get("rag", {}).get("top_k", 5)

    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM from config.yaml."""
        return self._config.get("system_prompt", "")


# Global config instance
config = Config()
