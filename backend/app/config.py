from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Google API (optional — not needed when using Ollama + HuggingFace)
    google_api_key: str = ""

    # LLM
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_fallback_model: str = "gemini-2.5-flash-lite"
    llm_temperature: float = 0.3

    # Embeddings
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # ChromaDB
    chroma_persist_dir: str = "data/chroma_db"
    chroma_collection_name: str = "pokemon_knowledge"

    # Retriever
    retriever_k: int = 12

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Auth
    google_client_id: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_expiry_hours: int = 168  # 7 days

    # Database
    db_path: str = "data/profgecko.db"

    # Credits
    daily_free_credits: int = 10
    anonymous_session_limit: int = 3

    # App
    app_debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
