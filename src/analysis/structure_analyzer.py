"""
Market structure analyzer for Smart Money Concepts.

Identifies trend direction, swing points, and market structure
breaks (BOS and CHoCH) for context.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta

from ..models.candle import Candle
from ..models.market_data import SwingPoint
from ..config import get_settings


class MarketStructureState:
    """Market structure state enumeration."""

    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    RANGING = "RANGING"


class StructureBreak:
    """Structure break data structure."""

    def __init__(
        self,
        break_type: str,
        price: Decimal,
        timestamp: datetime,
        confirmed: bool = False,
        strength: float = 0.0,
    ):
        """
        Initialize structure break.

        Args:
            break_type: BOS or CHoCH
            price: Break price level
            timestamp: Break time
            confirmed: Whether break is confirmed
            strength: Break strength score
        """
        self.type = break_type
        self.price = price
        self.timestamp = timestamp
        self.confirmed = confirmed
        self.strength = strength
        self.confirmation_candles = 0

        # Validate
        self._validate_break()

    def _validate_break(self):
        """Validate structure break parameters."""
        if self.type not in ["BOS", "CHoCH"]:
            raise ValueError(f"Invalid break type: {self.type}")

        if self.price <= 0:
            raise ValueError("Break price must be positive")

    def add_confirmation_candle(self):
        """Add a confirmation candle."""
        self.confirmation_candles += 1

    def confirm_break(self):
        """Confirm the structure break."""
        self.confirmed = True

    def to_dict(self) -> dict:
        """Convert structure break to dictionary."""
        return {
            "type": self.type,
            "price": float(self.price),
            "timestamp": self.timestamp.isoformat(),
            "confirmed": self.confirmed,
            "strength": self.strength,
            "confirmation_candles": self.confirmation_candles,
        }


class MarketStructure:
    """
    Market structure data structure.

    Contains trend information, swing points,
    and structure breaks for analysis.
    """

    def __init__(self, instrument: str = "XAUUSD"):
        """
        Initialize market structure.

        Args:
            instrument: Trading instrument
        """
        self.instrument = instrument
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []
        self.structure_breaks: List[StructureBreak] = []
        self.current_state = MarketStructureState.RANGING
        self.trend_strength = 0.0
        self.trend_direction = None
        self.last_update = datetime.utcnow()

        # Analysis parameters
        self.min_swing_points = 3
        self.trend_period = 20
        self.structure_break_threshold = 0.8

    def update_with_candle(self, candle: Candle):
        """
        Update market structure with new candle data.

        Args:
            candle: New candle to incorporate
        """
        self.last_update = candle.timestamp

        # Update swing points
        self._update_swing_points(candle)

        # Update trend analysis
        self._update_trend_analysis()

        # Check for structure breaks
        self._check_structure_breaks(candle)

    def _update_swing_points(self, candle: Candle):
        """
        Update swing points with new candle.

        Args:
            candle: New candle data
        """
        settings = get_settings()
        config = settings.smc.structure

        # Check if this candle forms a new swing high
        if self._is_swing_high(candle):
            swing_high = SwingPoint(
                price=candle.high,
                timestamp=candle.timestamp,
                point_type="HIGH",
                strength=self._calculate_swing_strength(candle, "HIGH"),
                instrument=self.instrument,
            )
            self.swing_highs.append(swing_high)

        # Check if this candle forms a new swing low
        elif self._is_swing_low(candle):
            swing_low = SwingPoint(
                price=candle.low,
                timestamp=candle.timestamp,
                point_type="LOW",
                strength=self._calculate_swing_strength(candle, "LOW"),
                instrument=self.instrument,
            )
            self.swing_lows.append(swing_low)

        # Remove old swing points (keep only recent ones)
        max_swing_points = config.trend_period * 2
        if len(self.swing_highs) > max_swing_points:
            self.swing_highs = self.swing_highs[-max_swing_points:]
        if len(self.swing_lows) > max_swing_points:
            self.swing_lows = self.swing_lows[-max_swing_points:]

    def _is_swing_high(self, candle: Candle) -> bool:
        """
        Check if candle forms a swing high.

        Args:
            candle: Candle to evaluate

        Returns:
            True if swing high
        """
        if not self.swing_lows:
            return False

        # Check if this high is higher than recent lows
        recent_lows = self.swing_lows[-self.trend_period :]
        if not recent_lows:
            return False

        max_low_price = max(low.price for low in recent_lows)
        return candle.high > max_low_price

    def _is_swing_low(self, candle: Candle) -> bool:
        """
        Check if candle forms a swing low.

        Args:
            candle: Candle to evaluate

        Returns:
            True if swing low
        """
        if not self.swing_highs:
            return False

        # Check if this low is lower than recent highs
        recent_highs = self.swing_highs[-self.trend_period :]
        if not recent_highs:
            return False

        min_high_price = min(high.price for high in recent_highs)
        return candle.low < min_high_price

    def _calculate_swing_strength(self, candle: Candle, point_type: str) -> float:
        """
        Calculate swing point strength.

        Args:
            candle: Candle containing swing point
            point_type: HIGH or LOW

        Returns:
            Strength score (0.0 to 1.0)
        """
        strength = 0.0

        # Volume-based strength
        if candle.volume and candle.volume > 0:
            avg_volume = self._get_average_volume()
            volume_strength = min(1.0, candle.volume / avg_volume)
            strength += volume_strength * 0.4

        # Range-based strength
        if candle.total_range > 0:
            avg_range = self._get_average_range()
            range_strength = min(1.0, candle.total_range / avg_range)
            strength += range_strength * 0.3

        # Wick-based strength (rejection)
        wick_strength = 1.0 - (candle.body_percentage / 100.0)
        strength += wick_strength * 0.3

        return min(1.0, max(0.0, strength))

    def _get_average_volume(self) -> float:
        """Get average volume of recent swing points."""
        if not self.swing_highs and not self.swing_lows:
            return 0.0

        swing_volumes = []
        for swing in self.swing_highs + self.swing_lows:
            if swing.volume:
                swing_volumes.append(swing.volume)

        return sum(swing_volumes) / len(swing_volumes) if swing_volumes else 0.0

    def _get_average_range(self) -> float:
        """Get average range of recent swing points."""
        if not self.swing_highs and not self.swing_lows:
            return 0.0

        swing_ranges = []
        for swing in self.swing_highs + self.swing_lows:
            if hasattr(swing, "range_size"):
                swing_ranges.append(swing.range_size)

        return sum(swing_ranges) / len(swing_ranges) if swing_ranges else 0.0

    def _update_trend_analysis(self):
        """Update trend direction and strength."""
        if (
            len(self.swing_highs) < self.min_swing_points
            or len(self.swing_lows) < self.min_swing_points
        ):
            self.current_state = MarketStructureState.RANGING
            self.trend_direction = None
            self.trend_strength = 0.0
            return

        # Get recent swing points for trend analysis
        recent_highs = self.swing_highs[-self.trend_period :]
        recent_lows = self.swing_lows[-self.trend_period :]

        if not recent_highs or not recent_lows:
            return

        # Calculate trend direction
        last_high = recent_highs[-1]
        last_low = recent_lows[-1]
        prev_high = recent_highs[-2] if len(recent_highs) >= 2 else None
        prev_low = recent_lows[-2] if len(recent_lows) >= 2 else None

        # Determine trend
        if last_high.price > prev_high.price and last_low.price > prev_low.price:
            # Higher highs and higher lows = uptrend
            self.current_state = MarketStructureState.UPTREND
            self.trend_direction = "BULLISH"
        elif last_high.price < prev_high.price and last_low.price < prev_low.price:
            # Lower highs and lower lows = downtrend
            self.current_state = MarketStructureState.DOWNTREND
            self.trend_direction = "BEARISH"
        else:
            # Mixed or unclear = ranging
            self.current_state = MarketStructureState.RANGING
            self.trend_direction = None

        # Calculate trend strength
        self.trend_strength = self._calculate_trend_strength(recent_highs, recent_lows)

    def _calculate_trend_strength(
        self, highs: List[SwingPoint], lows: List[SwingPoint]
    ) -> float:
        """
        Calculate trend strength based on swing point progression.

        Args:
            highs: Recent swing highs
            lows: Recent swing lows

        Returns:
            Trend strength (0.0 to 1.0)
        """
        if len(highs) < 2 or len(lows) < 2:
            return 0.0

        # Calculate trend consistency
        high_trend_strength = 0.0
        low_trend_strength = 0.0

        # Check high progression
        for i in range(1, len(highs)):
            if highs[i].price > highs[i - 1].price:
                high_trend_strength += 1.0
            elif highs[i].price < highs[i - 1].price:
                high_trend_strength -= 0.5

        # Check low progression
        for i in range(1, len(lows)):
            if lows[i].price < lows[i - 1].price:
                low_trend_strength += 1.0
            elif lows[i].price > lows[i - 1].price:
                low_trend_strength -= 0.5

        # Normalize and combine
        max_possible_strength = max(len(highs), len(lows)) - 1
        high_strength = max(0.0, high_trend_strength / max_possible_strength)
        low_strength = max(0.0, low_trend_strength / max_possible_strength)

        # Overall trend strength
        return (high_strength + low_strength) / 2.0

    def _check_structure_breaks(self, candle: Candle):
        """
        Check for structure breaks with new candle.

        Args:
            candle: New candle data
        """
        settings = get_settings()
        config = settings.smc.structure

        if len(self.swing_highs) < 2 or len(self.swing_lows) < 2:
            return

        # Check for Break of Structure (BOS)
        if self.current_state == MarketStructureState.UPTREND:
            self._check_bos_bullish(candle, config)
        elif self.current_state == MarketStructureState.DOWNTREND:
            self._check_bos_bearish(candle, config)

        # Check for Change of Character (CHoCH)
        elif self.current_state == MarketStructureState.RANGING:
            self._check_choch(candle, config)

    def _check_bos_bullish(self, candle: Candle, config):
        """
        Check for bullish Break of Structure.

        Args:
            candle: Current candle
            config: Structure configuration
        """
        if not self.swing_lows:
            return

        last_low = self.swing_lows[-1]

        # BOS confirmed when price breaks above last swing low
        if candle.close > last_low.price:
            structure_break = StructureBreak(
                break_type="BOS",
                price=last_low.price,
                timestamp=candle.timestamp,
                strength=last_low.strength,
            )
            self.structure_breaks.append(structure_break)

    def _check_bos_bearish(self, candle: Candle, config):
        """
        Check for bearish Break of Structure.

        Args:
            candle: Current candle
            config: Structure configuration
        """
        if not self.swing_highs:
            return

        last_high = self.swing_highs[-1]

        # BOS confirmed when price breaks below last swing high
        if candle.close < last_high.price:
            structure_break = StructureBreak(
                break_type="BOS",
                price=last_high.price,
                timestamp=candle.timestamp,
                strength=last_high.strength,
            )
            self.structure_breaks.append(structure_break)

    def _check_choch(self, candle: Candle, config):
        """
        Check for Change of Character.

        Args:
            candle: Current candle
            config: Structure configuration
        """
        if len(self.swing_highs) < 2 or len(self.swing_lows) < 2:
            return

        last_high = self.swing_highs[-1]
        last_low = self.swing_lows[-1]

        # CHoCH confirmed when structure changes from ranging to trending
        if self.current_state == MarketStructureState.RANGING:
            # Start of uptrend: break above last high
            if candle.close > last_high.price:
                structure_break = StructureBreak(
                    break_type="CHoCH",
                    price=last_high.price,
                    timestamp=candle.timestamp,
                    strength=last_high.strength,
                )
                self.structure_breaks.append(structure_break)
            # Start of downtrend: break below last low
            elif candle.close < last_low.price:
                structure_break = StructureBreak(
                    break_type="CHoCH",
                    price=last_low.price,
                    timestamp=candle.timestamp,
                    strength=last_low.strength,
                )
                self.structure_breaks.append(structure_break)

    def confirm_structure_break(self, break_type: str, price: Decimal):
        """
        Confirm a structure break with additional candles.

        Args:
            break_type: Type of break (BOS/CHoCH)
            price: Price level of break
        """
        for structure_break in self.structure_breaks:
            if structure_break.type == break_type and abs(
                structure_break.price - price
            ) < Decimal("0.0010"):
                structure_break.confirm_break()
                break

    def get_recent_breaks(self, max_age_hours: int = 24) -> List[StructureBreak]:
        """
        Get recent structure breaks.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            List of recent breaks
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        recent_breaks = [
            sb for sb in self.structure_breaks if sb.timestamp >= cutoff_time
        ]

        return sorted(recent_breaks, key=lambda x: x.timestamp, reverse=True)

    def get_trend_line(self, lookback: int = 10) -> Optional[dict]:
        """
        Calculate trend line information.

        Args:
            lookback: Number of points to use

        Returns:
            Trend line data or None
        """
        if len(self.swing_highs) < lookback or len(self.swing_lows) < lookback:
            return None

        # Get recent swing points
        recent_highs = self.swing_highs[-lookback:]
        recent_lows = self.swing_lows[-lookback:]

        if not recent_highs or not recent_lows:
            return None

        # Calculate linear regression for highs
        high_points = [(sp.timestamp.timestamp(), sp.price) for sp in recent_highs]
        low_points = [(sp.timestamp.timestamp(), sp.price) for sp in recent_lows]

        # Simple trend line calculation
        if self.current_state == MarketStructureState.UPTREND and high_points:
            # Uptrend: connect swing lows
            return self._calculate_trend_line(low_points)
        elif self.current_state == MarketStructureState.DOWNTREND and low_points:
            # Downtrend: connect swing highs
            return self._calculate_trend_line(high_points)

        return None

    def _calculate_trend_line(self, points: List[Tuple]) -> dict:
        """
        Calculate linear trend line from points.

        Args:
            points: List of (timestamp, price) tuples

        Returns:
            Trend line information
        """
        if len(points) < 2:
            return None

        # Sort points by time
        sorted_points = sorted(points)

        # Calculate slope and intercept
        x1, y1 = sorted_points[0]
        x2, y2 = sorted_points[1]

        # Convert timestamps to numeric (seconds since epoch)
        x1_num = x1.timestamp()
        x2_num = x2.timestamp()

        # Calculate slope (price per second)
        slope = (y2 - y1) / (x2_num - x1_num)

        # Calculate intercept
        intercept = y1 - (slope * x1_num)

        return {
            "slope": float(slope),
            "intercept": float(intercept),
            "start_point": {"timestamp": x1.isoformat(), "price": float(y1)},
            "end_point": {"timestamp": x2.isoformat(), "price": float(y2)},
            "strength": abs(slope) * 10000,  # Convert to pips per second
        }

    def get_structure_summary(self) -> dict:
        """
        Get comprehensive structure summary.

        Returns:
            Structure analysis dictionary
        """
        return {
            "current_state": self.current_state,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "swing_highs": [sh.to_dict() for sh in self.swing_highs[-10:]],
            "swing_lows": [sl.to_dict() for sl in self.swing_lows[-10:]],
            "structure_breaks": [sb.to_dict() for sb in self.structure_breaks[-10:]],
            "last_update": self.last_update.isoformat(),
            "trend_line": self.get_trend_line(),
        }
