"""RAG (Retrieval-Augmented Generation) module for Observer-GPT."""

from .retriever import RulebookRetriever, get_retriever
from .vector_store import VectorStore
from .embeddings import EmbeddingModel

__all__ = ["RulebookRetriever", "get_retriever", "VectorStore", "EmbeddingModel"]
