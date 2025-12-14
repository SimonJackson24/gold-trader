"""
Trading module for XAUUSD Gold Trading System.

Contains signal generation, trade management,
and risk management components.
"""

from .signal_generator import SignalGenerator
from .trade_manager import TradeManager
from .risk_manager import RiskManager

__all__ = [
    "SignalGenerator",
    "TradeManager",
    "RiskManager"
]