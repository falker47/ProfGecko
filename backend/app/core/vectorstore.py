from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever


def get_vectorstore(
    persist_dir: str,
    collection_name: str,
    embeddings: Embeddings,
) -> Chroma:
    return Chroma(
        persist_directory=persist_dir,
        collection_name=collection_name,
        embedding_function=embeddings,
    )


def get_retriever(
    vectorstore: Chroma,
    k: int = 5,
    generation: int | None = None,
) -> VectorStoreRetriever:
    search_kwargs: dict = {"k": k}
    if generation is not None:
        search_kwargs["filter"] = {"generation": generation}

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )
