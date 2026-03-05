from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Google API
    google_api_key: str

    # LLM
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = 0.7

    # Embeddings
    embedding_provider: str = "gemini"
    embedding_model: str = "models/gemini-embedding-001"

    # ChromaDB
    chroma_persist_dir: str = "data/chroma_db"
    chroma_collection_name: str = "pokemon_knowledge"

    # Retriever
    retriever_k: int = 5

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # App
    app_debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
