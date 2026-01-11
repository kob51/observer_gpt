"""Observer-GPT Streamlit Web Application."""

import sys
import time
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.llm import get_llm
from src.context import search_images
from src.config import config


# Background loading for RAG resources
@st.cache_resource
def start_background_loading():
    """Start loading RAG resources in background thread."""
    state = {"ready": False, "error": None}

    def load_resources():
        try:
            from src.rag import get_retriever
            # Pre-load retrievers for all rulebook options
            get_retriever("usau")
            get_retriever("wfdf")
            get_retriever("both")
            state["ready"] = True
        except Exception as e:
            state["error"] = str(e)

    thread = threading.Thread(target=load_resources, daemon=True)
    thread.start()
    return state, thread


# Start background loading immediately (non-blocking)
_load_state, _load_thread = start_background_loading()


def wait_for_resources(timeout: float = 30.0) -> bool:
    """Wait for background resources to load. Returns True if ready."""
    _load_thread.join(timeout=timeout)
    if _load_state["error"]:
        raise RuntimeError(f"Failed to load resources: {_load_state['error']}")
    return _load_state["ready"]


# Page config
st.set_page_config(
    page_title="Observer-GPT",
    page_icon="🥏",
    layout="centered",
)

st.title("🥏 Observer-GPT")
st.caption("Your AI-powered Ultimate Frisbee rules assistant")

# Check if Google API key is configured
if not config.get_api_key("google"):
    st.error("Google API key not configured. Please add it to `config.yaml`.")
    st.code("""# config.yaml
google:
  api_key: "AI..."
""")
    st.stop()

# Sidebar for settings
with st.sidebar:
    st.header("Settings")

    # Rulebook selection
    default_rulebook = config.get_default_rulebook()
    rulebook_options = ["usau", "wfdf", "both"]
    rulebook = st.radio(
        "Rulebook",
        options=rulebook_options,
        index=rulebook_options.index(default_rulebook),
        format_func=lambda x: {"usau": "USAU", "wfdf": "WFDF", "both": "Both"}[x],
        horizontal=True,
    )

    st.divider()

    # RAG toggle
    st.subheader("Context Mode")
    use_rag = st.toggle(
        "Use RAG (retrieval)",
        value=config.is_rag_enabled(),
        help="RAG retrieves only relevant sections (~10 chunks) instead of the full rulebook. Faster and cheaper, but may miss some context.",
    )

    if use_rag:
        # Slider hidden for now but kept for future use
        # rag_top_k = st.slider(
        #     "Chunks to retrieve",
        #     min_value=3,
        #     max_value=15,
        #     value=10,
        #     help="More chunks = more context but higher token cost",
        # )
        rag_top_k = 10  # Default: retrieve 10 most relevant sections
        st.caption("Mode: RAG (retrieval)")
    else:
        rag_top_k = 10  # Not used in full context mode
        st.caption("Mode: Full context")

    st.divider()

    # Clear chat button
    if st.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message and message["metadata"]:
            meta = message["metadata"]
            with st.expander("Details"):
                # Timing (if available)
                if meta.get('total_time'):
                    st.caption(f"Total time: {meta['total_time']:.1f}s")
                if meta.get('time_to_first_token'):
                    st.caption(f"Time to first token: {meta['time_to_first_token']:.1f}s")
                if meta.get('output_tokens') and meta.get('total_time'):
                    tokens_per_sec = meta['output_tokens'] / meta['total_time']
                    st.caption(f"Speed: {tokens_per_sec:.1f} tokens/sec")

                if meta.get('total_time'):
                    st.caption("---")

                # Token breakdown
                if meta.get('input_tokens') and meta.get('output_tokens'):
                    st.caption(f"Input tokens: {meta['input_tokens']:,}")
                    st.caption(f"Output tokens: {meta['output_tokens']:,}")
                    st.caption(f"Total tokens: {meta['input_tokens'] + meta['output_tokens']:,}")
                elif meta.get('tokens'):
                    st.caption(f"Total tokens: {meta['tokens']:,}")

                st.caption("---")

                # Model and mode info
                st.caption(f"Model: {meta.get('model', 'N/A')}")
                if meta.get('rulebook'):
                    st.caption(f"Rulebook: {meta['rulebook'].upper()}")
                st.caption(f"Mode: {'RAG' if meta.get('rag_enabled') else 'Full context'}")

                # Citations
                if meta.get('sources'):
                    st.caption(f"Citations: {', '.join(meta['sources'][:5])}")

                # Show RAG chunks if available
                if meta.get('rag_chunks'):
                    st.caption("---")
                    st.caption("Retrieved sections:")
                    for chunk in meta['rag_chunks']:
                        st.caption(f"  - {chunk['source'].upper()}: {chunk['section']} ({chunk.get('score', 0):.2f})")

# Chat input
if prompt := st.chat_input("Describe what happened on the field..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        try:
            # Track timing (use dict for mutable state in nested function)
            timing = {"start": time.time(), "first_token": None}

            # Get LLM
            llm = get_llm(rulebook=rulebook)

            # Wait for RAG resources if needed
            if use_rag and not _load_state["ready"]:
                with st.spinner("Loading embedding model..."):
                    wait_for_resources()

            # Show loading indicator until first chunk arrives
            mode_text = "Retrieving relevant sections..." if use_rag else "Processing full rulebook..."
            status_placeholder = st.empty()
            status_placeholder.markdown(f"*{mode_text}*")

            # Stream the response (shows text as it generates)
            def stream_with_loading():
                first_chunk = True
                for chunk in llm.query_stream(prompt, use_rag=use_rag, rag_top_k=rag_top_k):
                    if first_chunk:
                        timing["first_token"] = time.time() - timing["start"]
                        status_placeholder.empty()  # Clear loading text
                        first_chunk = False
                    yield chunk

            full_response = st.write_stream(stream_with_loading())
            total_time = time.time() - timing["start"]
            time_to_first_token = timing["first_token"]

            # Get full result with metadata
            result = llm.get_last_query_result(full_response)

            # Check for relevant images from the "Relevant Diagrams:" section
            import re
            diagrams_match = re.search(r'Relevant Diagrams?:\s*(.+?)(?:\n\n|$)', full_response, re.IGNORECASE | re.DOTALL)
            if diagrams_match:
                diagrams_text = diagrams_match.group(1)
                images = search_images(diagrams_text, rulebook=rulebook)
                if images:
                    with st.expander("📷 Related Diagrams"):
                        for img in images:
                            img_path = Path(img["path"])
                            if img_path.exists():
                                st.image(str(img_path), caption=img["description"])

            # Calculate additional metrics
            input_tokens = llm._last_usage.get("prompt_tokens", 0) if hasattr(llm, '_last_usage') and llm._last_usage else None
            output_tokens = llm._last_usage.get("completion_tokens", 0) if hasattr(llm, '_last_usage') and llm._last_usage else None
            tokens_per_sec = output_tokens / total_time if output_tokens and total_time > 0 else None

            # Show metadata
            with st.expander("Details"):
                # Timing
                st.caption(f"Total time: {total_time:.1f}s")
                if time_to_first_token:
                    st.caption(f"Time to first token: {time_to_first_token:.1f}s")
                if tokens_per_sec:
                    st.caption(f"Speed: {tokens_per_sec:.1f} tokens/sec")

                st.caption("---")

                # Token breakdown
                if input_tokens and output_tokens:
                    st.caption(f"Input tokens: {input_tokens:,}")
                    st.caption(f"Output tokens: {output_tokens:,}")
                    st.caption(f"Total tokens: {input_tokens + output_tokens:,}")
                elif result.tokens_used:
                    st.caption(f"Total tokens: {result.tokens_used:,}")

                st.caption("---")

                # Model and mode info
                st.caption(f"Model: {result.model}")
                st.caption(f"Rulebook: {rulebook.upper()}")
                st.caption(f"Mode: {'RAG' if result.rag_enabled else 'Full context'}")

                # Citations
                if result.sources:
                    st.caption(f"Citations: {', '.join(result.sources[:5])}")

                # Show RAG chunks if used
                if result.rag_enabled and result.rag_chunks:
                    st.caption("---")
                    st.caption("Retrieved sections:")
                    for chunk in result.rag_chunks:
                        st.caption(f"  - {chunk['source'].upper()}: {chunk['section']} ({chunk.get('score', 0):.2f})")

            # Store in history
            st.session_state.messages.append({
                "role": "assistant",
                "content": result.answer,
                "metadata": {
                    "model": result.model,
                    "tokens": result.tokens_used,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_time": total_time,
                    "time_to_first_token": time_to_first_token,
                    "rulebook": rulebook,
                    "sources": result.sources,
                    "rag_enabled": result.rag_enabled,
                    "rag_chunks": result.rag_chunks if result.rag_enabled else [],
                }
            })

        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.caption("Observer-GPT uses official USAU and WFDF rulebooks. Always verify rulings with certified observers for official play.")
