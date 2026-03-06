"""Index LangChain Documents into ChromaDB."""

import logging
import time

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from tqdm import tqdm

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
MAX_RETRIES = 5
INITIAL_BACKOFF = 4  # seconds, doubles each retry

# Delay between batches — only needed for API-based embeddings (Gemini/OpenAI).
# Set to 0 for local embeddings (HuggingFace).
API_BATCH_DELAY = 2  # seconds


def index_documents(
    documents: list[Document],
    embeddings: Embeddings,
    persist_dir: str,
    collection_name: str,
    use_api_delay: bool = False,
) -> Chroma:
    """Index documents into ChromaDB in batches.

    Args:
        use_api_delay: If True, adds a delay between batches to respect
                       API rate limits (Gemini/OpenAI). Not needed for
                       local embeddings (HuggingFace).
    """
    total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
    delay = API_BATCH_DELAY if use_api_delay else 0

    print(f"\nIndexing {len(documents)} documents into ChromaDB...")
    print(f"  Persist dir: {persist_dir}")
    print(f"  Collection: {collection_name}")
    print(f"  Batch size: {BATCH_SIZE}")
    if delay:
        print(f"  API delay: {delay}s between batches")
        print(f"  Estimated time: ~{total_batches * delay // 60}m {total_batches * delay % 60}s")
    print()

    vectorstore = None

    with tqdm(total=total_batches, desc="Indexing") as pbar:
        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i : i + BATCH_SIZE]

            # Retry with exponential backoff on rate limit errors
            for attempt in range(MAX_RETRIES):
                try:
                    if vectorstore is None:
                        vectorstore = Chroma.from_documents(
                            documents=batch,
                            embedding=embeddings,
                            persist_directory=persist_dir,
                            collection_name=collection_name,
                        )
                    else:
                        vectorstore.add_documents(batch)
                    break  # Success
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        wait = min(INITIAL_BACKOFF * (2 ** attempt), 60)
                        logger.warning(
                            "Rate limit hit (attempt %d/%d). Waiting %ds...",
                            attempt + 1, MAX_RETRIES, wait,
                        )
                        print(f"  ⏳ Rate limit hit, waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})...")
                        time.sleep(wait)
                    else:
                        raise  # Non-rate-limit error, propagate
            else:
                raise RuntimeError(
                    f"Failed batch {i // BATCH_SIZE + 1}/{total_batches} "
                    f"after {MAX_RETRIES} retries (rate limit)"
                )

            pbar.update(1)

            # Delay between batches (only for API-based embeddings)
            if delay and i + BATCH_SIZE < len(documents):
                time.sleep(delay)

    if vectorstore is None:
        # No documents to index, return empty store
        vectorstore = Chroma(
            persist_directory=persist_dir,
            collection_name=collection_name,
            embedding_function=embeddings,
        )

    count = vectorstore._collection.count()
    print(f"\nIndexing complete. Total documents in collection: {count}")

    return vectorstore
