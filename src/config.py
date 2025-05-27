"""Configuration management for the Recipe Bot"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Bot configuration"""
    telegram_bot_token: str
    openai_api_key: str
    storage_path: str = "/data/recipes"  # Railway persistent volume path
    storage_type: str = "postgres"  # json, postgres
    database_url: Optional[str] = None
    openai_model: str = "gpt-4.1-mini"
    log_level: str = "INFO"
    webhook_url: Optional[str] = None
    environment: str = "development"  # development, production
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        return cls(
            telegram_bot_token=telegram_token,
            openai_api_key=openai_key,
            storage_path=os.getenv("STORAGE_PATH", "/data/recipes"),
            storage_type="postgres",
            database_url=os.getenv("DATABASE_URL"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            webhook_url=os.getenv("WEBHOOK_URL"),
            environment=os.getenv("ENVIRONMENT", "development")
        )

# Conversation states
class ConversationStates:
    WAITING_FOR_INGREDIENTS = 0
    WAITING_FOR_RECIPE_NAME = 1
    WAITING_FOR_RECIPE_CONTENT = 2
    EDITING_RECIPE = 3
    CHOOSING_EDIT_TYPE = 4
    WAITING_FOR_RECIPE_UPDATE = 5
    VERIFYING_RECIPE = 6