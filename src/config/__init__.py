"""
Configuration management for XAUUSD Gold Trading System.

Handles loading, validation, and management of all system
configuration parameters including trading, SMC, and API settings.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from .settings import Settings, get_settings
from .database import DatabaseConfig
from .trading import TradingConfig
from .smc import SMCConfig
from .telegram import TelegramConfig

__all__ = [
    "Settings",
    "get_settings",
    "DatabaseConfig",
    "TradingConfig",
    "SMCConfig",
    "TelegramConfig",
]
