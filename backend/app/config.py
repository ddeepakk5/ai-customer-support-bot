"""
Configuration settings for the application
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # App Settings
    APP_NAME: str = "AI Customer Support Bot"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./support_bot.db"
    )

    # LLM Configuration - OpenRouter (GPT-OSS 20B)
    LLM_TYPE: str = os.getenv("LLM_TYPE", "openai").lower()
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT", "30"))
    MAX_MESSAGES_PER_SESSION: int = int(os.getenv("MAX_MESSAGES_PER_SESSION", "100"))

    # Escalation Configuration
    ESCALATION_THRESHOLD: float = 0.5
    ESCALATION_KEYWORDS: list = [
        "urgent", "emergency", "critical", "problem", "bug", "error",
        "broken", "not working", "complaint", "refund", "cancel", "angry",
    ]

    # Conversation Configuration
    MAX_CONTEXT_MESSAGES: int = 10
    CONVERSATION_TIMEOUT_MINUTES: int = 60

    # Embeddings Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # FAQ Configuration
    MAX_FAQ_RESULTS: int = 5
    MIN_FAQ_SIMILARITY: float = 0.3

    # LLM Parameters
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 500
    LLM_TOP_P: float = 0.9

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
