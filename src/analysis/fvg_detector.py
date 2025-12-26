"""
Fair Value Gap (FVG) detector for Smart Money Concepts.

Identifies price imbalances between three-candle patterns
that indicate potential reversal zones.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from ..models.candle import Candle
from ..models.market_data import PriceLevel
from ..config import get_settings


class FairValueGapType:
    """FVG type enumeration."""

    BULLISH = "BULLISH"  # Gap up - potential buy setup
    BEARISH = "BEARISH"  # Gap down - potential sell setup


class FairValueGap:
    """
    Fair Value Gap data structure.

    Represents an identified FVG with its characteristics
    and validation metrics.
    """

    def __init__(
        self,
        gap_type: str,
        top_price: Decimal,
        bottom_price: Decimal,
        start_candle: Candle,
        end_candle: Candle,
    ):
        """
        Initialize FVG.

        Args:
            gap_type: BULLISH or BEARISH
            top_price: Top of the gap
            bottom_price: Bottom of the gap
            start_candle: First candle of the pattern
            end_candle: Third candle of the pattern
        """
        self.type = gap_type
        self.top_price = top_price
        self.bottom_price = bottom_price
        self.start_candle = start_candle
        self.end_candle = end_candle
        self.middle_candle = None  # Will be set when pattern is complete

        # Calculate gap properties
        self.size = abs(top_price - bottom_price)
        self.mid_price = (top_price + bottom_price) / Decimal("2")
        self.timestamp = end_candle.timestamp
        self.strength = 0.0
        self.filled = False
        self.fill_time = None
        self.touches = 0

        # Validation
        self._validate_gap()

    def _validate_gap(self):
        """Validate FVG parameters."""
        if self.top_price <= self.bottom_price:
            raise ValueError("Top price must be greater than bottom price")

        if self.size <= 0:
            raise ValueError("Gap size must be positive")

    def add_middle_candle(self, candle: Candle):
        """
        Add the middle candle to complete the pattern.

        Args:
            candle: Middle candle of the three-candle pattern
        """
        self.middle_candle = candle

        # Validate pattern
        if self.type == FairValueGapType.BULLISH:
            # Bullish FVG: middle candle should close below gap
            if candle.close >= self.bottom_price:
                raise ValueError("Invalid bullish FVG pattern")
        else:  # BEARISH
            # Bearish FVG: middle candle should close above gap
            if candle.close <= self.top_price:
                raise ValueError("Invalid bearish FVG pattern")

    def calculate_strength(self, avg_volume: float, current_volume: float) -> float:
        """
        Calculate FVG strength based on multiple factors.

        Args:
            avg_volume: Average volume over lookback period
            current_volume: Volume of the gap candle

        Returns:
            Strength score (0.0 to 1.0)
        """
        settings = get_settings()
        config = settings.smc.fvg

        strength = 0.0

        # Size-based strength (optimal size is 10-30 pips)
        size_pips = float(self.size * 10000)  # Convert to pips
        if config.min_size_pips <= size_pips <= config.max_size_pips:
            size_strength = 1.0
        elif size_pips < config.min_size_pips:
            size_strength = 0.2
        else:
            size_strength = 0.5

        # Volume-based strength
        volume_strength = 1.0
        if config.require_volume_spike:
            volume_multiplier = current_volume / avg_volume if avg_volume > 0 else 1.0
            volume_strength = min(1.0, volume_multiplier / config.volume_multiplier)

        # Wick-based strength (small wicks in middle candle)
        wick_strength = 1.0
        if self.middle_candle:
            wick_ratio = self.middle_candle.body_percentage / 100.0
            wick_strength = max(0.3, 1.0 - wick_ratio)

        # Combine strengths
        strength = (
            (size_strength * 0.4) + (volume_strength * 0.3) + (wick_strength * 0.3)
        )

        self.strength = min(1.0, max(0.0, strength))
        return self.strength

    def is_valid(self, min_strength: float = 0.3) -> bool:
        """
        Check if FVG meets minimum strength requirements.

        Args:
            min_strength: Minimum strength threshold

        Returns:
            True if FVG is valid
        """
        return self.strength >= min_strength

    def is_filled(
        self, current_price: Decimal, tolerance_pips: Decimal = Decimal("2")
    ) -> bool:
        """
        Check if FVG has been filled by price action.

        Args:
            current_price: Current market price
            tolerance_pips: Tolerance for gap fill

        Returns:
            True if gap is considered filled
        """
        if self.filled:
            return True

        tolerance = tolerance_pips / Decimal("10000")

        if self.type == FairValueGapType.BULLISH:
            # Bullish gap is filled when price enters gap from above
            return current_price <= (self.bottom_price + tolerance)
        else:  # BEARISH
            # Bearish gap is filled when price enters gap from below
            return current_price >= (self.top_price - tolerance)

    def mark_filled(self, fill_time: datetime, fill_price: Decimal):
        """
        Mark FVG as filled.

        Args:
            fill_time: Time when gap was filled
            fill_price: Price at which gap was filled
        """
        self.filled = True
        self.fill_time = fill_time
        self.touches += 1

    def add_touch(self):
        """Record a price touch at the gap boundary."""
        self.touches += 1

    def get_price_level(self) -> PriceLevel:
        """
        Convert FVG to price level for analysis.

        Returns:
            PriceLevel representation
        """
        return PriceLevel(
            price=self.mid_price,
            strength=self.strength,
            level_type=f"FVG_{self.type}_TOP"
            if self.type == FairValueGapType.BULLISH
            else f"FVG_{self.type}_BOTTOM",
            timestamp=self.timestamp,
            touches=self.touches,
            instrument=self.start_candle.instrument,
        )

    def to_dict(self) -> dict:
        """Convert FVG to dictionary representation."""
        return {
            "type": self.type,
            "top_price": float(self.top_price),
            "bottom_price": float(self.bottom_price),
            "size": float(self.size),
            "mid_price": float(self.mid_price),
            "strength": self.strength,
            "timestamp": self.timestamp.isoformat(),
            "filled": self.filled,
            "fill_time": self.fill_time.isoformat() if self.fill_time else None,
            "touches": self.touches,
            "start_candle": self.start_candle.to_dict(),
            "middle_candle": self.middle_candle.to_dict()
            if self.middle_candle
            else None,
            "end_candle": self.end_candle.to_dict(),
        }


class FairValueGapDetector:
    """
    Fair Value Gap detector implementation.

    Scans candle sequences to identify three-candle patterns
    that create price imbalances.
    """

    def __init__(self):
        """Initialize FVG detector."""
        self.settings = get_settings()
        self.config = self.settings.smc.fvg

    def detect_fvgs(
        self, candles: List[Candle], avg_volume: float = 0
    ) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps in candle sequence.

        Args:
            candles: List of candles to analyze
            avg_volume: Average volume for strength calculation

        Returns:
            List of detected FVGs
        """
        if len(candles) < 3:
            return []

        fvgs = []

        # Scan for three-candle patterns
        for i in range(len(candles) - 2):
            pattern_candles = candles[i : i + 3]

            # Check if we have a valid pattern
            if len(pattern_candles) < 3:
                continue

            fvg = self._analyze_pattern(pattern_candles, avg_volume)
            if fvg and fvg.is_valid(self.config.min_strength):
                fvgs.append(fvg)

        return fvgs

    def _analyze_pattern(
        self, candles: List[Candle], avg_volume: float
    ) -> Optional[FairValueGap]:
        """
        Analyze three-candle pattern for FVG.

        Args:
            candles: Three consecutive candles
            avg_volume: Average volume for context

        Returns:
            Detected FVG or None
        """
        if len(candles) != 3:
            return None

        first, second, third = candles

        # Check for bullish FVG (gap up)
        if second.low > first.high and third.low > second.high:
            gap_top = min(first.high, second.high)
            gap_bottom = max(second.low, third.low)

            if gap_bottom > gap_top:
                return None  # Invalid gap

            fvg = FairValueGap(
                gap_type=FairValueGapType.BULLISH,
                top_price=gap_bottom,
                bottom_price=gap_top,
                start_candle=first,
                end_candle=third,
            )
            fvg.add_middle_candle(second)

            # Calculate strength
            current_volume = third.volume if third.volume else avg_volume
            fvg.calculate_strength(avg_volume, current_volume)

            return fvg

        # Check for bearish FVG (gap down)
        elif second.high < first.low and third.high < second.low:
            gap_top = max(first.low, second.low)
            gap_bottom = min(second.high, third.high)

            if gap_bottom >= gap_top:
                return None  # Invalid gap

            fvg = FairValueGap(
                gap_type=FairValueGapType.BEARISH,
                top_price=gap_top,
                bottom_price=gap_bottom,
                start_candle=first,
                end_candle=third,
            )
            fvg.add_middle_candle(second)

            # Calculate strength
            current_volume = third.volume if third.volume else avg_volume
            fvg.calculate_strength(avg_volume, current_volume)

            return fvg

        return None

    def get_active_fvgs(
        self,
        fvgs: List[FairValueGap],
        current_price: Decimal,
        max_age_minutes: int = 240,
    ) -> List[FairValueGap]:
        """
        Get active (unfilled) FVGs within age limit.

        Args:
            fvgs: List of all detected FVGs
            current_price: Current market price
            max_age_minutes: Maximum age in minutes

        Returns:
            List of active FVGs
        """
        active_fvgs = []
        current_time = datetime.utcnow()

        for fvg in fvgs:
            # Check age
            age_minutes = (current_time - fvg.timestamp).total_seconds() / 60
            if age_minutes > max_age_minutes:
                continue

            # Check if filled
            if fvg.is_filled(current_price):
                continue

            # Filter by size if configured
            size_pips = float(fvg.size * 10000)
            if self.config.ignore_small_fvgs and size_pips < self.config.min_size_pips:
                continue

            active_fvgs.append(fvg)

        # Sort by strength (strongest first)
        active_fvgs.sort(key=lambda x: x.strength, reverse=True)
        return active_fvgs

    def validate_fvg_fill(
        self,
        fvg: FairValueGap,
        current_price: Decimal,
        fill_candle: Optional[Candle] = None,
    ) -> bool:
        """
        Validate if an FVG has been properly filled.

        Args:
            fvg: FVG to validate
            current_price: Current market price
            fill_candle: Candle that potentially filled the gap

        Returns:
            True if FVG is considered filled
        """
        if not fvg:
            return False

        # Check if price is in gap range
        if fvg.type == FairValueGapType.BULLISH:
            # Bullish gap filled when price enters from above
            if current_price <= fvg.bottom_price:
                return True
        else:  # BEARISH
            # Bearish gap filled when price enters from below
            if current_price >= fvg.top_price:
                return True

        return False

    def get_fvg_statistics(self, fvgs: List[FairValueGap]) -> dict:
        """
        Get statistics for detected FVGs.

        Args:
            fvgs: List of FVGs to analyze

        Returns:
            Statistics dictionary
        """
        if not fvgs:
            return {}

        total = len(fvgs)
        bullish = len([fvg for fvg in fvgs if fvg.type == FairValueGapType.BULLISH])
        bearish = len([fvg for fvg in fvgs if fvg.type == FairValueGapType.BEARISH])
        filled = len([fvg for fvg in fvgs if fvg.filled])

        avg_strength = sum(fvg.strength for fvg in fvgs) / total if total > 0 else 0
        avg_size = sum(fvg.size for fvg in fvgs) / total if total > 0 else 0

        return {
            "total_fvgs": total,
            "bullish_fvgs": bullish,
            "bearish_fvgs": bearish,
            "filled_fvgs": filled,
            "fill_rate": (filled / total * 100) if total > 0 else 0,
            "avg_strength": avg_strength,
            "avg_size_pips": float(avg_size * 10000),
            "strongest_fvg": max(fvgs, key=lambda x: x.strength) if fvgs else None,
            "weakest_fvg": min(fvgs, key=lambda x: x.strength) if fvgs else None,
        }
