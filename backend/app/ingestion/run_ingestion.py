"""CLI entry point for data ingestion.

Usage:
    cd backend
    python -m app.ingestion.run_ingestion [--max-id 1025] [--force] [--gens 1-9]
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure backend dir is in path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import get_settings
from app.core.embeddings import get_embeddings
from app.core.generation_mapper import MAX_POKEMON_PER_GEN
from app.ingestion.fetcher import fetch_all_data
from app.ingestion.indexer import index_documents
from app.ingestion.pokeapi_client import PokeAPIClient
from app.ingestion.transformers import build_all_documents_for_generation


def parse_gen_range(gen_str: str) -> list[int]:
    """Parse generation range like '1-9' or '4' or '1,3,5'."""
    gens = []
    for part in gen_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            gens.extend(range(int(start), int(end) + 1))
        else:
            gens.append(int(part))
    return sorted(set(gens))


async def main(max_id: int, force: bool, generations: list[int]):
    settings = get_settings()

    # Check if already indexed
    persist_dir = settings.chroma_persist_dir
    if Path(persist_dir).exists() and not force:
        from langchain_chroma import Chroma

        embeddings = get_embeddings(
            settings.embedding_provider, model=settings.embedding_model
        )
        existing = Chroma(
            persist_directory=persist_dir,
            collection_name=settings.chroma_collection_name,
            embedding_function=embeddings,
        )
        count = existing._collection.count()
        if count > 0:
            print(f"ChromaDB already has {count} documents.")
            print("Use --force to re-index.")
            return

    # Step 1: Fetch all data from PokeAPI
    async with PokeAPIClient(cache_dir="data/raw") as client:
        all_data = await fetch_all_data(client, max_id)

    # Step 2: Build documents for each generation
    all_docs = []
    for gen in generations:
        if gen not in MAX_POKEMON_PER_GEN:
            print(f"Warning: Generation {gen} not recognized, skipping.")
            continue

        print(f"\n--- Building documents for Generation {gen} ---")
        docs = build_all_documents_for_generation(all_data, gen)
        print(f"  Generated {len(docs)} documents")
        all_docs.extend(docs)

    print(f"\n=== Total documents: {len(all_docs)} ===")

    # Step 3: Index into ChromaDB
    embeddings = get_embeddings(
        settings.embedding_provider, model=settings.embedding_model
    )
    index_documents(
        documents=all_docs,
        embeddings=embeddings,
        persist_dir=persist_dir,
        collection_name=settings.chroma_collection_name,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prof. Gallade - Data Ingestion")
    parser.add_argument(
        "--max-id", type=int, default=1025,
        help="Max Pokemon ID to fetch (default: 1025)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-indexing even if data exists",
    )
    parser.add_argument(
        "--gens", type=str, default="1-9",
        help="Generations to build (e.g., '1-9', '4', '1,3,5')",
    )
    args = parser.parse_args()

    generations = parse_gen_range(args.gens)
    print(f"Generations to build: {generations}")

    asyncio.run(main(args.max_id, args.force, generations))
