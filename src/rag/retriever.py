"""RAG retriever for rulebook chunks."""

from pathlib import Path
from typing import Optional

from .vector_store import VectorStore


# Module-level cache for retriever instances (one per rulebook)
_retriever_cache: dict[str, "RulebookRetriever"] = {}


def get_retriever(rulebook: str = "usau") -> "RulebookRetriever":
    """Get a cached retriever instance for the given rulebook.

    Args:
        rulebook: Which rulebook to use ("usau", "wfdf", or "both")

    Returns:
        Cached RulebookRetriever instance
    """
    if rulebook not in _retriever_cache:
        _retriever_cache[rulebook] = RulebookRetriever(rulebook)
    return _retriever_cache[rulebook]


class RulebookRetriever:
    """Retrieve relevant rulebook chunks for a query."""

    def __init__(self, rulebook: str = "usau"):
        """Initialize retriever.

        Args:
            rulebook: Which rulebook to use ("usau", "wfdf", or "both")
        """
        self.rulebook = rulebook
        self._store = VectorStore()
        self._initialized = False

    def _load_chunks(self) -> list[dict]:
        """Load chunks from the parsed rules directory."""
        chunks_dir = Path(__file__).parent.parent.parent / "parsed_rules"
        all_chunks = []

        rulebooks = []
        if self.rulebook == "both":
            rulebooks = ["usau", "wfdf"]
        else:
            rulebooks = [self.rulebook]

        for rb in rulebooks:
            rb_chunks_dir = chunks_dir / f"{rb}_chunks"
            if not rb_chunks_dir.exists():
                continue

            for chunk_file in sorted(rb_chunks_dir.glob("*.md")):
                # Skip index files
                if chunk_file.name.startswith("_"):
                    continue

                content = chunk_file.read_text()

                # Extract section name from filename
                section = chunk_file.stem.replace("_", " ")

                all_chunks.append({
                    "content": content,
                    "section": section,
                    "source": rb,
                    "file": str(chunk_file),
                })

        return all_chunks

    def _ensure_initialized(self):
        """Lazy initialization of vector store."""
        if not self._initialized:
            chunks = self._load_chunks()
            self._store.add_chunks(chunks, self.rulebook)
            self._initialized = True

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Retrieve relevant chunks for a query.

        Args:
            query: User's question
            top_k: Number of chunks to retrieve

        Returns:
            List of relevant chunk dicts
        """
        self._ensure_initialized()
        return self._store.search(query, top_k=top_k)

    def get_context(self, query: str, top_k: int = 5) -> str:
        """Get formatted context string for LLM prompt.

        Args:
            query: User's question
            top_k: Number of chunks to include

        Returns:
            Formatted string with relevant rulebook sections
        """
        chunks = self.retrieve(query, top_k=top_k)

        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["source"].upper()
            section = chunk["section"]
            content = chunk["content"]
            score = chunk.get("score", 0)

            context_parts.append(
                f"=== {source}: {section} (relevance: {score:.2f}) ===\n{content}"
            )

        return "\n\n".join(context_parts)
