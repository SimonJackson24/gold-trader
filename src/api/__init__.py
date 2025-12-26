"""
API module for XAUUSD Gold Trading System.

Provides REST API endpoints for:
- System status and health checks
- Trading signals
- Trade management
- Market data
- Account information
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from .main import app

__all__ = ["app"]
