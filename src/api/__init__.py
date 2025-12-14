"""
API module for XAUUSD Gold Trading System.

Provides REST API endpoints for:
- System status and health checks
- Trading signals
- Trade management
- Market data
- Account information
"""

from .main import app

__all__ = ['app']