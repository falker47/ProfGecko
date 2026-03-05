from langchain_core.embeddings import Embeddings


def get_embeddings(provider: str = "gemini", **kwargs) -> Embeddings:
    if provider == "gemini":
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
