from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Configuration
    ollama_model: str = Field(default="gemma:2b-instruct-q4_K_M")
    ollama_base_url: str = Field(default="http://localhost:11434")
    request_timeout: int = Field(default=120)
    
    ollama_keep_alive: str = Field(default="5m")
    num_ctx: int = Field(default=8192)
    num_threads: int = Field(default=16)

    temperature: float = Field(default=0.2)
    max_tokens: int = Field(default=1024)
    streaming: bool = Field(default=False)
    # Embedding Configuration
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    
    # Vector Database
    chroma_persist_dir: str = Field(default="data/chroma_db")
    collection_name: str = Field(default="medclaim-docs")
    
    # Retrieval Settings
    top_k: int = Field(default=3)
    chunk_size: int = Field(default=700)
    chunk_overlap: int = Field(default=150)
    
    # API Settings
    max_file_size_mb: int = Field(default=100)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
