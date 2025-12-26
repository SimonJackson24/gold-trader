"""
Database module for XAUUSD Gold Trading System.

Handles database connections, models, repositories,
and database operations for PostgreSQL.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from .connection import Database, get_db, get_async_db
from .models import (
    Base,
    Signal,
    Trade,
    PerformanceMetric,
    PriceHistory,
    SystemConfig,
    AuditLog,
)
from .repositories import (
    SignalRepository,
    TradeRepository,
    PerformanceRepository,
    ConfigRepository,
)

__all__ = [
    "Database",
    "get_db",
    "get_async_db",
    "Base",
    "Signal",
    "Trade",
    "PerformanceMetric",
    "PriceHistory",
    "SystemConfig",
    "AuditLog",
    "SignalRepository",
    "TradeRepository",
    "PerformanceRepository",
    "ConfigRepository",
]
