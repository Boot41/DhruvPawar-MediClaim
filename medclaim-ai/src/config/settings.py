from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Configuration
    ollama_model: str = Field(default="gemma:7b")
    ollama_base_url: str = Field(default="http://localhost:11434")
    request_timeout: int = Field(default=120)
    
    # Embedding Configuration
    embedding_model: str = Field(default="BAAI/bge-base-en-v1.5")
    
    # Vector Database
    chroma_persist_dir: str = Field(default="data/chroma_db")
    collection_name: str = Field(default="medclaim-docs")
    
    # Retrieval Settings
    top_k: int = Field(default=5)
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    
    # API Settings
    max_file_size_mb: int = Field(default=50)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
