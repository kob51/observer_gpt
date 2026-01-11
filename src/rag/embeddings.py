"""Embedding generation for RAG."""

import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Generate embeddings using sentence-transformers (local, no API cost)."""

    _instance: Optional["EmbeddingModel"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls):
        """Singleton pattern - only load model once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model.

        Args:
            model_name: Sentence transformer model to use.
                        all-MiniLM-L6-v2 is fast and good quality.
        """
        if self._model is None:
            self._model = SentenceTransformer(model_name)
            self._model_name = model_name

    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        return self._model.encode(texts, convert_to_numpy=True)

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            numpy array of shape (embedding_dim,)
        """
        return self._model.encode(text, convert_to_numpy=True)

    @property
    def embedding_dim(self) -> int:
        """Get the dimension of embeddings."""
        return self._model.get_sentence_embedding_dimension()
