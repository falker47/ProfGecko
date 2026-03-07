from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings


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
