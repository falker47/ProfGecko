"""Diagnostic script: understand WHY the retriever fails for basic Pokemon queries.

Questions to answer:
1. How many documents per entity_type exist per generation?
2. Does the Dragonite Pokemon document actually exist in ChromaDB?
3. What does similarity search return for "Parlami di Dragonite"?
4. What are the similarity SCORES? (Is the Pokemon doc just ranked lower, or absent?)
5. How long are Pokemon docs vs move docs? (Embedding dilution?)
"""

import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from app.config import get_settings
from app.core.embeddings import get_embeddings
from langchain_chroma import Chroma


def main():
    settings = get_settings()
    embeddings = get_embeddings(
        settings.embedding_provider, model=settings.embedding_model,
    )
    vectorstore = Chroma(
        persist_directory=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
    )

    # Access underlying Chroma collection for raw queries
    collection = vectorstore._collection

    print("=" * 70)
    print("1) DOCUMENT COUNT BY ENTITY_TYPE AND GENERATION")
    print("=" * 70)

    # Get all metadata
    all_data = collection.get(include=["metadatas"])
    total = len(all_data["ids"])
    print(f"Total documents in collection: {total}")

    # Count by entity_type + generation
    from collections import Counter
    type_gen_counts = Counter()
    type_counts = Counter()
    gen_counts = Counter()
    for meta in all_data["metadatas"]:
        etype = meta.get("entity_type", "unknown")
        gen = meta.get("generation", "?")
        type_gen_counts[(etype, gen)] += 1
        type_counts[etype] += 1
        gen_counts[gen] += 1

    print("\nBy entity_type (all gens):")
    for etype, count in type_counts.most_common():
        print(f"  {etype:12s}: {count}")

    print("\nBy generation (all types):")
    for gen, count in sorted(gen_counts.items()):
        print(f"  Gen {gen}: {count}")

    print("\nGen 9 breakdown by entity_type:")
    for (etype, gen), count in sorted(type_gen_counts.items()):
        if gen == 9:
            print(f"  {etype:12s}: {count}")

    print()
    print("=" * 70)
    print("2) DOES THE DRAGONITE POKEMON DOCUMENT EXIST?")
    print("=" * 70)

    # Search by metadata
    dragonite_docs = collection.get(
        where={"$and": [
            {"name_en": "dragonite"},
            {"entity_type": "pokemon"},
            {"generation": 9},
        ]},
        include=["documents", "metadatas"],
    )
    print(f"Dragonite pokemon docs (gen 9): {len(dragonite_docs['ids'])}")
    if dragonite_docs["ids"]:
        doc = dragonite_docs["documents"][0]
        meta = dragonite_docs["metadatas"][0]
        print(f"  Metadata: {meta}")
        print(f"  Content (first 500 chars):\n{doc[:500]}")
        print(f"  Content length: {len(doc)} chars")

    # Also check all gens
    dragonite_all = collection.get(
        where={"$and": [
            {"name_en": "dragonite"},
            {"entity_type": "pokemon"},
        ]},
        include=["metadatas"],
    )
    print(f"\nDragonite pokemon docs (all gens): {len(dragonite_all['ids'])}")
    for meta in dragonite_all["metadatas"]:
        print(f"  Gen {meta.get('generation')}: id={meta.get('pokemon_id')}")

    # Check for any doc mentioning dragonite in content
    print()
    print("=" * 70)
    print("3) ALL DOCUMENTS MENTIONING 'dragonite' OR 'Dragonite' IN CONTENT (gen 9)")
    print("=" * 70)

    gen9_docs = collection.get(
        where={"generation": 9},
        include=["documents", "metadatas"],
    )
    dragonite_mentions = []
    for i, doc in enumerate(gen9_docs["documents"]):
        if "dragonite" in doc.lower():
            meta = gen9_docs["metadatas"][i]
            dragonite_mentions.append((meta, doc))

    print(f"Gen 9 docs mentioning 'dragonite': {len(dragonite_mentions)}")
    for meta, doc in dragonite_mentions[:15]:
        etype = meta.get("entity_type", "?")
        name = meta.get("name_it", meta.get("name_en", "?"))
        print(f"  [{etype:8s}] {name}: ...{doc[:120]}...")

    print()
    print("=" * 70)
    print("4) SIMILARITY SEARCH: 'Parlami di Dragonite' (gen 9, no filters)")
    print("=" * 70)

    # Raw similarity search with scores
    query = "Parlami di Dragonite"
    results_with_scores = vectorstore.similarity_search_with_score(
        query, k=20, filter={"generation": 9},
    )
    print(f"Query: '{query}'")
    print(f"Top 20 results (lower distance = better match):")
    for i, (doc, score) in enumerate(results_with_scores):
        meta = doc.metadata
        etype = meta.get("entity_type", "?")
        name = meta.get("name_it", meta.get("name_en", "?"))
        content_preview = doc.page_content[:80].replace("\n", " ")
        print(f"  #{i+1:2d} dist={score:.4f} [{etype:8s}] {name}: {content_preview}")

    print()
    print("=" * 70)
    print("5) SIMILARITY SEARCH: 'Dragonite' (gen 9, no filters)")
    print("=" * 70)

    query2 = "Dragonite"
    results2 = vectorstore.similarity_search_with_score(
        query2, k=20, filter={"generation": 9},
    )
    print(f"Query: '{query2}'")
    print(f"Top 20 results:")
    for i, (doc, score) in enumerate(results2):
        meta = doc.metadata
        etype = meta.get("entity_type", "?")
        name = meta.get("name_it", meta.get("name_en", "?"))
        content_preview = doc.page_content[:80].replace("\n", " ")
        print(f"  #{i+1:2d} dist={score:.4f} [{etype:8s}] {name}: {content_preview}")

    print()
    print("=" * 70)
    print("6) SIMILARITY SEARCH WITH ENTITY_TYPE FILTER: 'Parlami di Dragonite' (pokemon only)")
    print("=" * 70)

    results3 = vectorstore.similarity_search_with_score(
        "Parlami di Dragonite", k=5,
        filter={"$and": [{"generation": 9}, {"entity_type": "pokemon"}]},
    )
    print(f"Top 5 results (pokemon only):")
    for i, (doc, score) in enumerate(results3):
        meta = doc.metadata
        name = meta.get("name_it", meta.get("name_en", "?"))
        print(f"  #{i+1:2d} dist={score:.4f} {name}")

    print()
    print("=" * 70)
    print("7) DOCUMENT LENGTH ANALYSIS (gen 9)")
    print("=" * 70)

    lengths_by_type: dict[str, list[int]] = {}
    for i, doc in enumerate(gen9_docs["documents"]):
        etype = gen9_docs["metadatas"][i].get("entity_type", "?")
        lengths_by_type.setdefault(etype, []).append(len(doc))

    for etype, lengths in sorted(lengths_by_type.items()):
        avg = sum(lengths) / len(lengths)
        mn = min(lengths)
        mx = max(lengths)
        print(f"  {etype:12s}: count={len(lengths):5d}, avg={avg:7.0f}, min={mn:5d}, max={mx:5d} chars")

    print()
    print("=" * 70)
    print("8) CURRENT FILTER TEST: what _detect_excluded_types returns")
    print("=" * 70)

    # Simulate what the current code does
    from app.core.rag_chain import _detect_excluded_types
    test_queries = [
        "Parlami di Dragonite",
        "Mosse di Dragonite?",
        "Che bacca dare a Dragonite?",
        "Natura migliore per Dragonite?",
    ]
    for q in test_queries:
        excluded = _detect_excluded_types(q)
        print(f"  '{q}' -> excluded: {excluded}")

    # Now test what the retriever ACTUALLY returns with the current filter
    print()
    print("=" * 70)
    print("9) ACTUAL RETRIEVER SIMULATION: 'Parlami di Dragonite' with item+nature exclusion")
    print("=" * 70)

    chroma_filter = {"$and": [
        {"generation": 9},
        {"entity_type": {"$ne": "item"}},
        {"entity_type": {"$ne": "nature"}},
    ]}
    results4 = vectorstore.similarity_search_with_score(
        "Parlami di Dragonite", k=12, filter=chroma_filter,
    )
    print(f"Top 12 results (excluding item+nature):")
    for i, (doc, score) in enumerate(results4):
        meta = doc.metadata
        etype = meta.get("entity_type", "?")
        name = meta.get("name_it", meta.get("name_en", "?"))
        content_preview = doc.page_content[:80].replace("\n", " ")
        print(f"  #{i+1:2d} dist={score:.4f} [{etype:8s}] {name}: {content_preview}")

    print()
    print("=" * 70)
    print("10) NEW HYBRID RETRIEVAL: name match + semantic search")
    print("=" * 70)

    from app.core.rag_chain import _extract_candidate_names, RAGChain
    from app.core.llm import get_llm

    test_queries = [
        "Parlami di Dragonite",
        "Mosse di Dragonite?",
        "Parlami di Lucario",
        "Debolezze di Pikachu",
        "Cos'è Surf?",
        "Che abilita ha Garchomp?",
    ]

    settings = get_settings()
    llm = get_llm(settings.llm_provider, model=settings.llm_model, temperature=settings.llm_temperature)
    rag = RAGChain(llm=llm, vectorstore=vectorstore, k=settings.retriever_k)

    for q in test_queries:
        print(f"\n  Query: '{q}'")
        candidates = _extract_candidate_names(q)
        print(f"  Candidate names: {candidates}")
        docs = rag._retrieve(q, 9, original_question=q)
        print(f"  Results ({len(docs)} docs):")
        for i, doc in enumerate(docs):
            meta = doc.metadata
            etype = meta.get("entity_type", "?")
            name = meta.get("name_it", meta.get("name_en", "?"))
            print(f"    #{i+1:2d} [{etype:8s}] {name}")


if __name__ == "__main__":
    main()
