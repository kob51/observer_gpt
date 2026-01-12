"""Load and manage rulebook context for LLM queries."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional


def get_parsed_rules_path() -> Path:
    """Get the path to the parsed_rules directory."""
    # Navigate from src/context to project root
    return Path(__file__).parent.parent.parent / "parsed_rules"


@lru_cache(maxsize=4)
def load_rulebook_context(rulebook: str = "usau") -> str:
    """Load rulebook markdown content for LLM context.

    Args:
        rulebook: Which rulebook to load ("usau", "wfdf", or "both")

    Returns:
        Markdown content of the rulebook(s)

    Note:
        Results are cached - rulebook text is loaded only once per rulebook type.
    """
    parsed_path = get_parsed_rules_path()

    if rulebook == "both":
        usau_content = _load_single_rulebook("usau")
        wfdf_content = _load_single_rulebook("wfdf")
        return f"=== USAU RULES ===\n\n{usau_content}\n\n=== WFDF RULES ===\n\n{wfdf_content}"
    else:
        return _load_single_rulebook(rulebook)


@lru_cache(maxsize=4)
def _load_single_rulebook(rulebook: str) -> str:
    """Load a single rulebook's markdown content."""
    parsed_path = get_parsed_rules_path()
    rules_file = parsed_path / f"{rulebook}_rules.md"

    if not rules_file.exists():
        raise FileNotFoundError(f"Rulebook not found: {rules_file}")

    return rules_file.read_text()


@lru_cache(maxsize=1)
def load_image_catalog() -> dict:
    """Load the image catalog for reference in responses.

    Note:
        Result is cached - catalog is loaded only once.
    """
    catalog_path = get_parsed_rules_path() / "images" / "image_catalog.json"

    if not catalog_path.exists():
        return {}

    with open(catalog_path) as f:
        return json.load(f)


def search_images(query: str, rulebook: str = "both") -> list[dict]:
    """Search for relevant images based on exact keyword phrase matches.

    Args:
        query: Search query (e.g., "field diagram", "hand signal")
        rulebook: Which rulebook to search ("usau", "wfdf", or "both")

    Returns:
        List of matching image info dicts with paths
    """
    import re

    catalog = load_image_catalog()
    query_lower = query.lower()
    results = []

    def keyword_matches(keywords: list[str], text: str) -> bool:
        """Check if any keyword phrase appears in text as a complete phrase."""
        for kw in keywords:
            # Use word boundaries to match complete phrases only
            pattern = r'\b' + re.escape(kw.lower()) + r'\b'
            if re.search(pattern, text):
                return True
        return False

    # Filter catalog by selected rulebook
    if rulebook == "both":
        rulebooks_to_search = catalog.keys()
    else:
        rulebooks_to_search = [rulebook] if rulebook in catalog else []

    for rb in rulebooks_to_search:
        items = catalog[rb]
        for key, info in items.items():
            if isinstance(info, dict):
                keywords = info.get("keywords", [])
                if keyword_matches(keywords, query_lower):
                    results.append({
                        "rulebook": rb,
                        "key": key,
                        "file": info.get("file"),
                        "description": info.get("description"),
                        "path": str(get_parsed_rules_path() / "images" / info.get("file", ""))
                    })
            elif isinstance(info, list):
                # Handle arrays like hand_signals
                for item in info:
                    keywords = item.get("keywords", [])
                    if keyword_matches(keywords, query_lower):
                        results.append({
                            "rulebook": rb,
                            "key": key,
                            "file": item.get("file"),
                            "description": item.get("description"),
                            "path": str(get_parsed_rules_path() / "images" / item.get("file", ""))
                        })

    return results
