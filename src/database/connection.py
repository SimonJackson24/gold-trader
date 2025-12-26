"""
Database connection management for XAUUSD Gold Trading System.

Handles PostgreSQL connection pooling, session management,
and async database operations.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.config import get_settings


# Base class for all ORM models
Base = declarative_base()
metadata = MetaData()


class Database:
    """
    Database connection manager.

    Handles both synchronous and asynchronous database
    operations with connection pooling.
    """

    def __init__(self):
        """Initialize database connections."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self._sync_engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None

    def get_sync_engine(self):
        """Get synchronous SQLAlchemy engine."""
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self.settings.get_database_url(),
                poolclass=QueuePool,
                pool_pre_ping=True,
                echo=self.settings.debug,
                pool_size=self.settings.db_pool_size,
                max_overflow=self.settings.db_max_overflow,
                pool_timeout=self.settings.db_pool_timeout,
                pool_recycle=self.settings.db_pool_recycle,
            )
        return self._sync_engine

    def get_async_engine(self):
        """Get asynchronous SQLAlchemy engine with secure connection pooling."""
        if self._async_engine is None:
            db_url = self.settings.get_database_url()
            # Convert to async URL
            if db_url.startswith("postgresql://"):
                async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            else:
                async_url = db_url

            print(
                f"DEBUG: async_url={async_url.replace(self.settings.db_password, '***')}"
            )

            # Enhanced connection pool configuration for security and performance
            self._async_engine = create_async_engine(
                async_url,
                # Connection pool settings
                pool_size=self.settings.db_pool_size,
                max_overflow=self.settings.db_max_overflow,
                pool_timeout=self.settings.db_pool_timeout,
                pool_recycle=self.settings.db_pool_recycle,
                pool_pre_ping=True,  # Validate connections before use
                pool_reset_on_return="commit",  # Reset connection state
                # Security settings
                connect_args={
                    "command_timeout": 30,
                },
                # Query optimization
                echo=self.settings.debug,
                echo_pool=self.settings.debug,
                future=True,
                # Connection validation
                isolation_level="READ_COMMITTED",  # Prevent dirty reads
            )
        return self._async_engine

    def get_session_factory(self):
        """Get synchronous session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.get_sync_engine(), autocommit=False, autoflush=False
            )
        return self._session_factory

    def get_async_session_factory(self):
        """Get asynchronous session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.get_async_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._async_session_factory

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get synchronous database session.

        Yields:
            SQLAlchemy Session instance
        """
        session = self.get_session_factory()()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get asynchronous database session with enhanced security.

        Yields:
            SQLAlchemy AsyncSession instance
        """
        session = self.get_async_session_factory()()
        try:
            # Set session configuration for security
            await session.execute(text("SET SESSION statement_timeout = '60s'"))
            await session.execute(text("SET SESSION lock_timeout = '30s'"))
            await session.execute(
                text("SET SESSION idle_in_transaction_session_timeout = '10min'")
            )

            yield session
            await session.commit()

        except Exception as e:
            await session.rollback()
            # Log the error for security monitoring
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def connect(self):
        """Connect to database and test connection."""
        if not await self.test_connection():
            raise RuntimeError("Failed to connect to database")
        self.logger.info("Database connection established")

    async def disconnect(self):
        """Alias for close()."""
        await self.close()

    async def close(self):
        """Close all database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()

    async def create_tables(self):
        """Create all database tables."""
        async with self.get_async_session() as session:
            # Import all models to ensure they're registered
            from .models import (
                Signal,
                Trade,
                PerformanceMetric,
                PriceHistory,
                SystemConfig,
                AuditLog,
            )

            # Create tables
            async with self.get_async_engine().begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all database tables."""
        async with self.get_async_engine().begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is successful
        """
        try:
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False


# Global database instance
db = Database()


def get_db() -> Generator[Session, None, None]:
    """
    Get synchronous database session.

    Dependency injection function for FastAPI.

    Yields:
        SQLAlchemy Session instance
    """
    with db.get_session() as session:
        yield session


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get asynchronous database session.

    Dependency injection function for FastAPI.

    Yields:
        SQLAlchemy AsyncSession instance
    """
    async with db.get_async_session() as session:
        yield session


async def init_database():
    """Initialize database tables and connections."""
    # Test connection first
    if not await db.test_connection():
        raise RuntimeError("Failed to connect to database")

    # Create tables if they don't exist
    await db.create_tables()

    print("Database initialized successfully")


async def close_database():
    """Close database connections."""
    await db.close()


def get_database_info() -> dict:
    """
    Get database connection information.

    Returns:
        Dictionary with database info
    """
    settings = get_settings()
    return {
        "url": settings.get_database_url().replace(settings.db_password, "***"),
        "host": settings.db_host,
        "port": settings.db_port,
        "database": settings.db_name,
        "username": settings.db_user,
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "ssl_mode": settings.db_ssl_mode,
    }


# Database health check with enhanced security monitoring
async def check_database_health() -> dict:
    """
    Check database health status with comprehensive security checks.

    Returns:
        Dictionary with health information
    """
    try:
        async with db.get_async_session() as session:
            # Test basic query with parameterized statement to prevent injection
            result = await session.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()

            # Check connection pool
            engine = db.get_async_engine()
            pool = engine.pool

            # Test table access with parameterized query
            tables_result = await session.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            table_count = tables_result.scalar()

            # Check for long-running queries
            long_queries_result = await session.execute(
                text("""
                SELECT count(*) FROM pg_stat_activity
                WHERE state = 'active'
                AND query_start < now() - interval '30 seconds'
                AND query != '<IDLE>'
            """)
            )
            long_queries = long_queries_result.scalar()

            return {
                "status": "healthy",
                "connection_test": "passed",
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "table_count": table_count,
                "long_running_queries": long_queries,
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection_test": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
