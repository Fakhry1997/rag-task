from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./data/retrieval.db"

    # Vector store: "faiss" or "chroma"
    VECTOR_STORE_BACKEND: str = "faiss"
    VECTOR_STORE_PATH: str = "./data/vector_store"

    # Google / Gemini
    GOOGLE_API_KEY: str = ""
    GEMINI_LLM_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Chunking
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # Vector search
    VECTOR_TOP_K: int = 5


settings = Settings()
