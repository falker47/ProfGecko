"""Index LangChain Documents into ChromaDB."""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from tqdm import tqdm

BATCH_SIZE = 100


def index_documents(
    documents: list[Document],
    embeddings: Embeddings,
    persist_dir: str,
    collection_name: str,
) -> Chroma:
    """Index documents into ChromaDB in batches."""
    print(f"\nIndexing {len(documents)} documents into ChromaDB...")
    print(f"  Persist dir: {persist_dir}")
    print(f"  Collection: {collection_name}")
    print(f"  Batch size: {BATCH_SIZE}")

    vectorstore = None

    for i in tqdm(range(0, len(documents), BATCH_SIZE), desc="Indexing"):
        batch = documents[i : i + BATCH_SIZE]

        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=persist_dir,
                collection_name=collection_name,
            )
        else:
            vectorstore.add_documents(batch)

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
