"""
Data models for the XAUUSD Gold Trading System.

Contains all data structures and models used throughout the application
including signals, trades, candles, and market data.
"""

from .signal import TradingSignal
from .trade import Trade
from .candle import Candle
from .market_data import Tick, MarketSnapshot

__all__ = [
    "TradingSignal",
    "Trade", 
    "Candle",
    "Tick",
    "MarketSnapshot"
]