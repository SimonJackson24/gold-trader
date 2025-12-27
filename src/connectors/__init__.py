"""
Connectors module for XAUUSD Gold Trading System.

Provides connectivity to external systems including:
- MetaTrader 5 terminal
- WebSocket server for real-time data
- Telegram notifications
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

try:
    from .mt5_connector import MT5Connector
    MT5_AVAILABLE = True
except ImportError:
    MT5Connector = None
    MT5_AVAILABLE = False

from .websocket_server import WebSocketServer

__all__ = ["MT5Connector", "WebSocketServer", "MT5_AVAILABLE"]
