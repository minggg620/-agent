"""
Core configuration module for Zero Realm Social Agent.
Handles environment variables, settings, and configuration management.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # ====================== API Keys ======================
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    minimax_api_key: Optional[str] = Field(None, env="MINIMAX_API_KEY")

    # ====================== Database ======================
    database_url: str = Field("sqlite:///./zero_realm_agent.db", env="DATABASE_URL")

    # ====================== Logging ======================
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/zero_realm_agent.log", env="LOG_FILE")

    # ====================== Agent Configuration ======================
    agent_name: str = Field("zero-realm-social-agent", env="AGENT_NAME")
    agent_mode: str = Field("development", env="AGENT_MODE")
    max_memory_size: int = Field(1000, env="MAX_MEMORY_SIZE")
    shared_memory_size: int = Field(500, env="SHARED_MEMORY_SIZE")     # ← 新增

    # ====================== Project Paths ======================
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    # ====================== Server Configuration ======================
    host: str = Field("localhost", env="HOST")
    port: int = Field(8000, env="PORT")

    # ====================== Strategy & Memory ======================
    challenge_timeout: int = Field(300, env="CHALLENGE_TIMEOUT")
    strategy_timeout: int = Field(300, env="STRATEGY_TIMEOUT")
    max_concurrent_tasks: int = Field(10, env="MAX_CONCURRENT_TASKS")
    memory_retention_days: int = Field(30, env="MEMORY_RETENTION_DAYS")

    # ====================== Social Strategy ======================
    social_mode: str = Field("aggressive", env="SOCIAL_MODE")
    influence_targets: int = Field(10, env="INFLUENCE_TARGETS")
    reputation_threshold: float = Field(0.7, env="REPUTATION_THRESHOLD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"           # 允许 .env 中有额外字段
        case_sensitive = False


# Global settings instance
settings = Settings()
