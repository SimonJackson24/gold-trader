"""
Database configuration for XAUUSD Gold Trading System.

Handles PostgreSQL database connection settings and
connection pool configuration.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """
    Database configuration settings.
    
    Manages PostgreSQL connection parameters
    and connection pool settings.
    """
    
    # Connection settings
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="xauusd_trading", env="DB_NAME")
    username: str = Field(default="trader", env="DB_USER")
    password: str = Field(default="password123", env="DB_PASSWORD")
    
    # Connection pool settings
    pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")  # 1 hour
    
    # SSL settings
    ssl_mode: str = Field(default="prefer", env="DB_SSL_MODE")
    ssl_cert: Optional[str] = Field(default=None, env="DB_SSL_CERT")
    ssl_key: Optional[str] = Field(default=None, env="DB_SSL_KEY")
    ssl_ca: Optional[str] = Field(default=None, env="DB_SSL_CA")
    
    # Query settings
    query_timeout: int = Field(default=30, env="DB_QUERY_TIMEOUT")
    statement_timeout: int = Field(default=30000, env="DB_STATEMENT_TIMEOUT")  # 30 seconds
    
    # Migration settings
    auto_migrate: bool = Field(default=False, env="DB_AUTO_MIGRATE")
    migration_timeout: int = Field(default=300, env="DB_MIGRATION_TIMEOUT")
    
    class Config:
        env_prefix = "DB_"
    
    def get_url(self) -> str:
        """
        Get complete database connection URL.
        
        Returns:
            PostgreSQL connection URL
        """
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )
    
    def get_url_with_ssl(self) -> str:
        """
        Get database URL with SSL parameters.
        
        Returns:
            PostgreSQL connection URL with SSL settings
        """
        base_url = self.get_url()
        ssl_params = []
        
        if self.ssl_mode != "disable":
            ssl_params.append(f"sslmode={self.ssl_mode}")
            
            if self.ssl_cert:
                ssl_params.append(f"sslcert={self.ssl_cert}")
            if self.ssl_key:
                ssl_params.append(f"sslkey={self.ssl_key}")
            if self.ssl_ca:
                ssl_params.append(f"sslrootcert={self.ssl_ca}")
        
        if ssl_params:
            return f"{base_url}?{'&'.join(ssl_params)}"
        
        return base_url
    
    def get_pool_config(self) -> dict:
        """
        Get connection pool configuration.
        
        Returns:
            Dictionary with pool settings
        """
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,
        }
    
    def get_engine_kwargs(self) -> dict:
        """
        Get SQLAlchemy engine keyword arguments.
        
        Returns:
            Dictionary with engine settings
        """
        return {
            "url": self.get_url_with_ssl(),
            **self.get_pool_config(),
            "connect_args": {
                "connect_timeout": self.query_timeout,
                "command_timeout": self.statement_timeout / 1000,  # Convert to seconds
            },
            "echo": False,  # Set to True for SQL logging
        }
    
    def validate(self) -> bool:
        """
        Validate database configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Validate required fields
        if not self.host:
            errors.append("Database host is required")
        
        if not self.database:
            errors.append("Database name is required")
        
        if not self.username:
            errors.append("Database username is required")
        
        if not self.password:
            errors.append("Database password is required")
        
        # Validate port
        if not (1 <= self.port <= 65535):
            errors.append(f"Database port {self.port} is out of valid range (1-65535)")
        
        # Validate pool settings
        if self.pool_size <= 0:
            errors.append("Pool size must be positive")
        
        if self.max_overflow < 0:
            errors.append("Max overflow cannot be negative")
        
        if self.pool_timeout <= 0:
            errors.append("Pool timeout must be positive")
        
        # Validate SSL mode
        valid_ssl_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        if self.ssl_mode not in valid_ssl_modes:
            errors.append(f"SSL mode '{self.ssl_mode}' is not valid. Options: {valid_ssl_modes}")
        
        # Validate timeouts
        if self.query_timeout <= 0:
            errors.append("Query timeout must be positive")
        
        if self.statement_timeout <= 0:
            errors.append("Statement timeout must be positive")
        
        if errors:
            raise ValueError("Database configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful
            
        Note:
            This is a simple test that doesn't require SQLAlchemy
        """
        try:
            import psycopg2
            from psycopg2.extensions import connection
            
            conn: connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                sslmode=self.ssl_mode,
                connect_timeout=self.query_timeout
            )
            
            # Test simple query
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    def get_info(self) -> dict:
        """
        Get database configuration summary.
        
        Returns:
            Dictionary with configuration info (excluding password)
        """
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "ssl_mode": self.ssl_mode,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "query_timeout": self.query_timeout,
            "statement_timeout": self.statement_timeout,
        }