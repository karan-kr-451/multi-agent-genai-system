import os
from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis host address")
    REDIS_PORT: int = Field(default=6379, description="Redis port number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    
    # Ollama Configuration
    OLLAMA_HOST: str = Field(default="http://localhost:11434", description="Ollama host URL")
    OLLAMA_MODEL: str = Field(default="llama3", description="Ollama model name")
    
    # Application Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    WORKSPACE_DIR: str = Field(default="workspace", description="Workspace directory path")
    MAX_RETRIES: int = Field(default=3, description="Maximum number of retries")
    POLLING_INTERVAL: int = Field(default=2000, description="Polling interval in milliseconds")
    
    # API Configuration
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    
    # Security Configuration
    API_KEY: Optional[str] = Field(default=None, description="API key for authentication")
    ENABLE_AUTH: bool = Field(default=False, description="Enable authentication")
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def get_redis_url(self) -> str:
        """Generate Redis URL from configuration."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

def load_settings() -> Settings:
    """
    Load settings from environment variables and validate them.
    Will also create necessary directories if they don't exist.
    """
    try:
        settings = Settings()
        
        # Create workspace directory if it doesn't exist
        workspace_path = os.path.abspath(settings.WORKSPACE_DIR)
        if not os.path.exists(workspace_path):
            os.makedirs(workspace_path)
            logger.info("Created workspace directory at %s", workspace_path)
        
        # Set up logging level
        logging.getLogger().setLevel(settings.LOG_LEVEL)
        logger.info("Settings loaded successfully")
        
        # Log non-sensitive settings
        logger.debug("Current settings: %s", {
            k: v for k, v in settings.dict().items()
            if k not in {"REDIS_PASSWORD", "API_KEY"}
        })
        
        return settings
        
    except Exception as e:
        logger.critical("Failed to load settings: %s", str(e), exc_info=True)
        raise

def get_settings() -> Settings:
    """Cached settings instance."""
    if not hasattr(get_settings, "_settings"):
        get_settings._settings = load_settings()
    return get_settings._settings