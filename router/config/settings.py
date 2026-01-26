"""
Application settings using Pydantic Settings.

Settings are loaded from environment variables and .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Server
    host: str = "0.0.0.0"
    port: int = 9090

    # Ollama
    ollama_host: str = "host.docker.internal"
    ollama_port: int = 11434
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: int = 30

    # Cache
    cache_max_size: int = 1000
    cache_similarity_threshold: float = 0.85

    # Circuit Breaker
    cb_failure_threshold: int = 3
    cb_recovery_timeout: int = 30

    # Paths
    mcp_servers_config: str = "configs/mcp-servers.json"
    enhancement_rules_config: str = "configs/enhancement-rules.json"

    # Logging
    log_level: str = "info"

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
