"""
Core configuration module for Zero Realm Social Agent.
Handles environment variables, settings, and configuration management.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./agent.db", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/agent.log", env="LOG_FILE")
    
    # Agent Configuration
    agent_name: str = Field("cascade", env="AGENT_NAME")
    agent_mode: str = Field("development", env="AGENT_MODE")
    max_memory_size: int = Field(1000, env="MAX_MEMORY_SIZE")
    
    # Server Configuration
    host: str = Field("localhost", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # Project Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    core_dir: Path = Field(default_factory=lambda: Path(__file__).parent)
    
    # Zero Realm Specific Configuration
    zero_realm_api_endpoint: str = Field("https://api.zero-realm.com", env="ZERO_REALM_API_ENDPOINT")
    zero_realm_auth_token: Optional[str] = Field(None, env="ZERO_REALM_AUTH_TOKEN")
    challenge_timeout: int = Field(300, env="CHALLENGE_TIMEOUT")  # 5 minutes
    max_concurrent_challenges: int = Field(5, env="MAX_CONCURRENT_CHALLENGES")
    
    # Agent Strategy Configuration
    strategy_timeout: int = Field(300, env="STRATEGY_TIMEOUT")  # 5 minutes
    max_concurrent_tasks: int = Field(10, env="MAX_CONCURRENT_TASKS")
    
    # Memory Configuration
    memory_retention_days: int = Field(30, env="MEMORY_RETENTION_DAYS")
    shared_memory_size: int = Field(500, env="SHARED_MEMORY_SIZE")
    strategy_cache_size: int = Field(100, env="STRATEGY_CACHE_SIZE")
    
    # Social Strategy Configuration
    social_mode: str = Field("aggressive", env="SOCIAL_MODE")
    influence_targets: int = Field(10, env="INFLUENCE_TARGETS")
    reputation_threshold: float = Field(0.7, env="REPUTATION_THRESHOLD")
    monitoring_interval: int = Field(60, env="MONITORING_INTERVAL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_project_paths() -> dict:
    """Get all important project paths."""
    return {
        "root": settings.project_root,
        "core": settings.core_dir,
        "logs": settings.project_root / "logs",
        "data": settings.project_root / "data",
        "config": settings.project_root / "config",
    }


def ensure_directories():
    """Ensure all necessary directories exist."""
    paths = get_project_paths()
    for path in paths.values():
        if isinstance(path, Path) and not path.exists():
            path.mkdir(parents=True, exist_ok=True)


# Initialize directories on import
ensure_directories()
