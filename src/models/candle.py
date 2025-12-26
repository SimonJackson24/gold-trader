"""
Candle data model for OHLC price data.

Represents a candlestick with open, high, low, close prices
and volume information for a specific timeframe.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Candle:
    """
    OHLC candle data structure.

    Attributes:
        timestamp: Candle timestamp
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
        timeframe: Timeframe (M1, M5, M15, H1, H4, D1)
        instrument: Trading instrument (e.g., XAUUSD)
        tick_volume: Tick volume
        spread: Spread in points
    """

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Optional[int] = None
    timeframe: Optional[str] = None
    instrument: Optional[str] = None
    tick_volume: Optional[int] = None
    spread: Optional[int] = None

    def __post_init__(self):
        """Validate candle data after initialization."""
        if self.high < self.low:
            raise ValueError(
                f"High price ({self.high}) cannot be less than low price ({self.low})"
            )

        if not (self.low <= self.open <= self.high):
            raise ValueError(
                f"Open price ({self.open}) must be between high ({self.high}) and low ({self.low})"
            )

        if not (self.low <= self.close <= self.high):
            raise ValueError(
                f"Close price ({self.close}) must be between high ({self.high}) and low ({self.low})"
            )

    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish (close > open)."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Check if candle is bearish (close < open)."""
        return self.close < self.open

    @property
    def body_size(self) -> Decimal:
        """Calculate the size of candle body."""
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> Decimal:
        """Calculate upper wick size."""
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> Decimal:
        """Calculate lower wick size."""
        return min(self.open, self.close) - self.low

    @property
    def total_range(self) -> Decimal:
        """Calculate total candle range (high - low)."""
        return self.high - self.low

    @property
    def body_percentage(self) -> float:
        """Calculate body size as percentage of total range."""
        if self.total_range == 0:
            return 0.0
        return float((self.body_size / self.total_range) * 100)

    def is_doji(self, threshold: float = 0.1) -> bool:
        """
        Check if candle is a doji (open and close are very close).

        Args:
            threshold: Body size as percentage of range (default: 0.1%)

        Returns:
            True if candle is a doji
        """
        return self.body_percentage <= threshold

    def is_engulfing(self, previous_candle: "Candle") -> bool:
        """
        Check if this candle engulfs the previous candle.

        Args:
            previous_candle: The previous candle to check against

        Returns:
            True if this candle engulfs the previous candle
        """
        if not previous_candle:
            return False

        # Bullish engulfing
        if (
            previous_candle.is_bearish
            and self.is_bullish
            and self.open < previous_candle.close
            and self.close > previous_candle.open
        ):
            return True

        # Bearish engulfing
        if (
            previous_candle.is_bullish
            and self.is_bearish
            and self.open > previous_candle.close
            and self.close < previous_candle.open
        ):
            return True

        return False

    def to_dict(self) -> dict:
        """Convert candle to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "volume": self.volume,
            "timeframe": self.timeframe,
            "instrument": self.instrument,
            "tick_volume": self.tick_volume,
            "spread": self.spread,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Candle":
        """Create candle from dictionary representation."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            open=Decimal(str(data["open"])),
            high=Decimal(str(data["high"])),
            low=Decimal(str(data["low"])),
            close=Decimal(str(data["close"])),
            volume=data.get("volume"),
            timeframe=data.get("timeframe"),
            instrument=data.get("instrument"),
            tick_volume=data.get("tick_volume"),
            spread=data.get("spread"),
        )
