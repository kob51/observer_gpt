#!/usr/bin/env python3
"""Test script for LLM integration."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm import OpenAILLM
from src.context import search_images


def main():
    # Test with USAU rulebook
    print("Initializing OpenAI LLM with USAU rulebook...")
    llm = OpenAILLM(rulebook="usau", model="gpt-4o-mini")

    # Test query
    question = "What is a travel violation and when does it occur?"
    print(f"\nQuestion: {question}\n")

    result = llm.query(question)

    print("=" * 60)
    print("ANSWER:")
    print("=" * 60)
    print(result.answer)
    print("\n" + "=" * 60)
    print(f"Model: {result.model}")
    print(f"Tokens used: {result.tokens_used}")
    print(f"Rule citations found: {result.sources}")

    # Test image search
    print("\n" + "=" * 60)
    print("Testing image search for 'field diagram':")
    print("=" * 60)
    images = search_images("field diagram")
    for img in images:
        print(f"  - {img['rulebook']}: {img['description']}")
        print(f"    Path: {img['path']}")


if __name__ == "__main__":
    main()
