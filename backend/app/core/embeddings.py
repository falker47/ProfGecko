from langchain_core.embeddings import Embeddings

DEFAULT_HF_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def get_embeddings(provider: str = "huggingface", **kwargs) -> Embeddings:
    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=kwargs.get("model", DEFAULT_HF_MODEL),
        )
    elif provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model=kwargs.get("model", "models/gemini-embedding-001"),
        )
    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=kwargs.get("model", "text-embedding-3-small"),
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
