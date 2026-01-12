Project Brief: Observer-GPT
Objective: A mobile-optimized RAG (Retrieval-Augmented Generation) web application that allows Ultimate Frisbee players to settle on-field disputes by querying the USAU and WFDF rulebooks.

1. Core Functionality
Dual Ruleset Support: Users can toggle between USA Ultimate (USAU) and WFDF rules.

Natural Language Query: Players describe a scenario (e.g., "I was hit in the air while catching a score") and receive a plain-English ruling.

Rule Citations: Every answer must cite specific rule numbers (e.g., Rule 17.C.2) to ensure authority on the field.

Continuation Logic: The AI must specifically address whether play stops, where the disc goes, and the resulting stall count.

2. Technical Stack (Proposed)
Frontend/App Framework: Streamlit (Python-based) for rapid deployment (potential next version of Next.js for a custom UI).

LLM: OpenAI GPT-4o-mini (for speed and low cost) or Claude 3.5 Sonnet (for complex logic).

Vector Database: Pinecone or Qdrant (Free Tiers) to store structured rulebook "chunks."

Data Processing: RAG pipeline using LangChain or LlamaIndex.

3. Data Strategy (The "Ruleset")
Source Data: Official PDF versions of USAU and WFDF rulebooks, contained in the `rulebooks` folder

Ingestion Format: Markdown (.md). It is critical to maintain hierarchical nesting (e.g., 17 -> C -> 2 -> a) so the AI understands the relationship between rules.

Metadata: Each rule "chunk" in the database must be tagged with source: usau or source: wfdf.

4. User Experience (UI) Requirements
Mobile-First Design: Large text and buttons for outdoor use.

High Contrast: Legible in direct sunlight.

Fast Response: Answers should be delivered in under 3 seconds to avoid holding up the game.

Ruleset Toggle: A prominent switch to toggle between the two organizations.