"""
Main settings configuration for XAUUSD Gold Trading System.

Central configuration management using Pydantic for validation
and environment variable loading.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

from .database import DatabaseConfig
from .trading import TradingConfig
from .smc import SMCConfig
from .telegram import TelegramConfig


class Settings(BaseSettings):
    """
    Main application settings.
    
    Loads configuration from environment variables and .env file
    with proper validation and default values.
    """
    
    # Application settings
    app_name: str = Field(default="XAUUSD Gold Trading System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Security settings
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, env="JWT_EXPIRE_MINUTES")  # 1 hour for access tokens
    jwt_refresh_expire_minutes: int = Field(default=1440, env="JWT_REFRESH_EXPIRE_MINUTES")  # 24 hours for refresh tokens
    jwt_refresh_token_enabled: bool = Field(default=True, env="JWT_REFRESH_TOKEN_ENABLED")
    
    # API settings
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # WebSocket settings
    ws_port: int = Field(default=8001, env="WS_PORT")
    ws_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    ws_max_connections: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    
    # Redis settings
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Nested configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    smc: SMCConfig = Field(default_factory=SMCConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from nested configs
    
    def get_database_url(self) -> str:
        """Get complete database URL."""
        return self.database.get_url()
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    def validate_configuration(self) -> bool:
        """
        Validate critical configuration settings.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Validate required fields
        if not self.secret_key or len(self.secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters")
        
        # Validate port ranges
        if not (1 <= self.port <= 65535):
            errors.append(f"Port {self.port} is out of valid range (1-65535)")
        
        if not (1 <= self.ws_port <= 65535):
            errors.append(f"WebSocket port {self.ws_port} is out of valid range (1-65535)")
        
        # Validate trading configuration
        try:
            self.trading.validate()
        except ValueError as e:
            errors.append(f"Trading config error: {e}")
        
        # Validate SMC configuration
        try:
            self.smc.validate()
        except ValueError as e:
            errors.append(f"SMC config error: {e}")
        
        # Validate database configuration
        try:
            self.database.validate()
        except ValueError as e:
            errors.append(f"Database config error: {e}")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    def get_cors_origins(self) -> list:
        """Get CORS origins as proper list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    def get_log_config(self) -> dict:
        """Get logging configuration dictionary."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": self.log_format,
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {
                    "level": self.log_level,
                    "handlers": ["console"],
                },
            },
        }
    
    def update_from_dict(self, config_dict: dict):
        """
        Update settings from dictionary.
        
        Args:
            config_dict: Dictionary of configuration updates
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Re-validate after update
        self.validate_configuration()


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance with loaded configuration
    """
    return Settings()


# Global settings instance
settings = get_settings()