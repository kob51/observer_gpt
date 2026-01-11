"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QueryResult:
    """Result from an LLM query."""
    answer: str
    sources: list[str]  # List of rule references used
    model: str
    tokens_used: Optional[int] = None
    rag_chunks: list[dict] = field(default_factory=list)  # Retrieved chunks if RAG used
    rag_enabled: bool = False  # Whether RAG was used for this query


class BaseLLM(ABC):
    """Abstract base class for LLM providers.

    To add a new LLM provider, subclass this and implement:
    - _query_llm(): Send the prompt to the LLM and return the response
    """

    def __init__(self, rulebook: str = "usau", use_rag: Optional[bool] = None):
        """Initialize the LLM with a rulebook context.

        Args:
            rulebook: Which rulebook to use ("usau", "wfdf", or "both")
            use_rag: Override RAG setting (None = use config default)
        """
        self.rulebook = rulebook
        self._context: Optional[str] = None
        self._retriever = None
        self._last_retrieved_chunks: list[dict] = []

        # Determine RAG setting
        from src.config import config
        if use_rag is None:
            self._use_rag = config.is_rag_enabled()
        else:
            self._use_rag = use_rag
        self._rag_top_k = config.get_rag_top_k()

    @property
    def context(self) -> str:
        """Lazy-load the full rulebook context (for non-RAG mode)."""
        if self._context is None:
            from src.context.rulebook_loader import load_rulebook_context
            self._context = load_rulebook_context(self.rulebook)
        return self._context

    @property
    def retriever(self):
        """Get the cached RAG retriever for this rulebook."""
        if self._retriever is None:
            from src.rag import get_retriever
            self._retriever = get_retriever(self.rulebook)
        return self._retriever

    def query(
        self,
        question: str,
        use_rag: Optional[bool] = None,
    ) -> QueryResult:
        """Query the LLM about Ultimate Frisbee rules.

        Args:
            question: The user's question about rules
            use_rag: Override RAG setting for this query (None = use instance default)

        Returns:
            QueryResult with the answer and metadata
        """
        # Determine RAG mode for this query
        rag_enabled = use_rag if use_rag is not None else self._use_rag

        prompt = self._build_prompt(question, use_rag=rag_enabled)
        response = self._query_llm(prompt)
        result = self._parse_response(response)

        # Add RAG metadata
        result.rag_enabled = rag_enabled
        result.rag_chunks = self._last_retrieved_chunks.copy()

        return result

    def query_stream(
        self,
        question: str,
        use_rag: Optional[bool] = None,
        rag_top_k: Optional[int] = None,
    ):
        """Stream a query response, yielding chunks as they arrive.

        Args:
            question: The user's question about rules
            use_rag: Override RAG setting for this query (None = use instance default)
            rag_top_k: Number of chunks to retrieve (None = use instance default)

        Yields:
            Text chunks as they are generated
        """
        # Determine RAG mode for this query
        rag_enabled = use_rag if use_rag is not None else self._use_rag
        self._last_rag_enabled = rag_enabled

        # Override top_k if provided
        if rag_top_k is not None:
            self._rag_top_k = rag_top_k

        prompt = self._build_prompt(question, use_rag=rag_enabled)

        # Use streaming if available, otherwise fall back to regular query
        if hasattr(self, 'stream_query'):
            yield from self.stream_query(prompt)
        else:
            yield self._query_llm(prompt)

    def get_last_query_result(self, full_response: str) -> QueryResult:
        """Get QueryResult after streaming completes.

        Args:
            full_response: The complete response text from streaming

        Returns:
            QueryResult with the answer and metadata
        """
        result = self._parse_response(full_response)
        result.rag_enabled = getattr(self, '_last_rag_enabled', False)
        result.rag_chunks = self._last_retrieved_chunks.copy()
        return result

    def _build_prompt(
        self,
        question: str,
        use_rag: bool = False,
    ) -> str:
        """Build the full prompt with context and question."""
        from src.config import config

        # Get context based on mode
        if use_rag:
            context = self._get_rag_context(question)
            context_note = f"(Retrieved top {self._rag_top_k} most relevant sections)"
        else:
            context = self.context
            context_note = "(Full rulebook)"

        # Get system prompt from config
        base_prompt = config.get_system_prompt()

        system_prompt = f"""{base_prompt}

RULEBOOK CONTENT {context_note}:
{context}

END OF RULEBOOK CONTENT
"""
        return f"{system_prompt}\n\nQuestion: {question}"

    def _get_rag_context(self, question: str) -> str:
        """Get context using RAG retrieval."""
        chunks = self.retriever.retrieve(question, top_k=self._rag_top_k)
        self._last_retrieved_chunks = chunks

        if not chunks:
            # Fallback to full context if retrieval fails
            return self.context

        # Format chunks into context
        context_parts = []
        for chunk in chunks:
            source = chunk["source"].upper()
            section = chunk["section"]
            content = chunk["content"]

            context_parts.append(f"=== {source}: {section} ===\n{content}")

        return "\n\n".join(context_parts)

    @abstractmethod
    def _query_llm(self, prompt: str) -> str:
        """Send the prompt to the LLM and return the raw response.

        Subclasses must implement this method.

        Args:
            prompt: The full prompt including context and question

        Returns:
            The raw text response from the LLM
        """
        pass

    def _parse_response(self, response: str) -> QueryResult:
        """Parse the LLM response into a QueryResult.

        Override this in subclasses if needed for custom parsing.
        """
        # Extract rule citations from the response
        import re
        sources = []

        # Match USAU style: 17.C.2.a or 17.C.2
        usau_pattern = r'\b(\d{1,2}\.[A-Z](?:\.\d+)?(?:\.[a-z])?)\b'
        sources.extend(re.findall(usau_pattern, response))

        # Match WFDF style: 12.1.1 or 12.1
        wfdf_pattern = r'\b(\d{1,2}\.\d+(?:\.\d+)?(?:\.\d+)?)\b'
        sources.extend(re.findall(wfdf_pattern, response))

        # Deduplicate while preserving order
        seen = set()
        unique_sources = []
        for s in sources:
            if s not in seen:
                seen.add(s)
                unique_sources.append(s)

        return QueryResult(
            answer=response,
            sources=unique_sources,
            model=self.model_name,
            tokens_used=None
        )

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the model being used."""
        pass
