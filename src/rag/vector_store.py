"""Simple vector store for RAG retrieval."""

import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

from .embeddings import EmbeddingModel


class VectorStore:
    """Simple in-memory vector store with numpy."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize vector store.

        Args:
            cache_dir: Directory to cache embeddings. If None, uses default.
        """
        self._embeddings: Optional[np.ndarray] = None
        self._chunks: list[dict] = []
        self._embedding_model = EmbeddingModel()

        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / ".rag_cache"
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(exist_ok=True)

    def add_chunks(self, chunks: list[dict], rulebook: str):
        """Add chunks to the vector store.

        Args:
            chunks: List of chunk dicts with 'content', 'section', 'source' keys
            rulebook: Rulebook identifier for caching
        """
        cache_file = self._cache_dir / f"{rulebook}_embeddings.pkl"

        # Try to load from cache
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                cached = pickle.load(f)
                self._embeddings = cached["embeddings"]
                self._chunks = cached["chunks"]
                return

        # Generate embeddings
        texts = [chunk["content"] for chunk in chunks]
        self._embeddings = self._embedding_model.embed(texts)
        self._chunks = chunks

        # Cache for next time
        with open(cache_file, "wb") as f:
            pickle.dump({
                "embeddings": self._embeddings,
                "chunks": self._chunks,
            }, f)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for most relevant chunks.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of chunk dicts with added 'score' key
        """
        if self._embeddings is None or len(self._chunks) == 0:
            return []

        # Embed query
        query_embedding = self._embedding_model.embed_single(query)

        # Compute cosine similarity
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        chunk_norms = self._embeddings / np.linalg.norm(
            self._embeddings, axis=1, keepdims=True
        )

        # Dot product = cosine similarity (since normalized)
        similarities = np.dot(chunk_norms, query_norm)

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Return chunks with scores
        results = []
        for idx in top_indices:
            chunk = self._chunks[idx].copy()
            chunk["score"] = float(similarities[idx])
            results.append(chunk)

        return results
