"""Configuration management for the AML triage system."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM API Keys
    anthropic_api_key: str
    openai_api_key: Optional[str] = None

    # Database
    database_url: str = "postgresql://localhost:5432/aml_triage"
    redis_url: str = "redis://localhost:6379/0"

    # Agent Model Configuration
    supervisor_model: str = "claude-sonnet-4-5-20250929"
    data_enrichment_model: str = "claude-haiku-4-5-20250929"
    risk_scoring_model: str = "claude-sonnet-4-5-20250929"
    context_builder_model: str = "claude-sonnet-4-5-20250929"
    decision_maker_model: str = "claude-opus-4-5-20251101"

    # Decision Thresholds
    auto_clear_threshold: float = 0.85
    escalate_l2_threshold: float = 0.70
    escalate_l3_threshold: float = 0.50
    risk_score_high_threshold: int = 70
    risk_score_severe_threshold: int = 85

    # Performance Settings
    max_concurrent_alerts: int = 10
    agent_timeout_seconds: int = 30
    max_retries: int = 3

    # Monitoring
    prometheus_port: int = 9090
    log_level: str = "INFO"

    # External APIs
    castellum_api_key: Optional[str] = None
    castellum_api_url: str = "https://api.castellum.ai/v1"

    # LLM Settings
    llm_temperature_deterministic: float = 0.05
    llm_temperature_low: float = 0.1
    llm_temperature_medium: float = 0.2
    llm_temperature_high: float = 0.3
    llm_max_tokens: int = 4000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
