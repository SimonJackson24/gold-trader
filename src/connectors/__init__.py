"""
Connectors module for XAUUSD Gold Trading System.

Provides connectivity to external systems including:
- MetaTrader 5 terminal
- WebSocket server for real-time data
- Telegram notifications
"""

from .mt5_connector import MT5Connector
from .websocket_server import WebSocketServer

__all__ = [
    'MT5Connector',
    'WebSocketServer'
]