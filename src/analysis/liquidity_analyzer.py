"""
Liquidity analyzer for Smart Money Concepts.

Identifies liquidity pools, stop hunts, and liquidity sweeps
that indicate institutional activity.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from ..models.candle import Candle
from ..models.market_data import PriceLevel, SwingPoint
from ..config import get_settings


class LiquidityPool:
    """
    Liquidity pool data structure.

    Represents an identified liquidity pool with
    its characteristics and touch history.
    """

    def __init__(
        self,
        price: Decimal,
        strength: float,
        pool_type: str,
        timestamp: datetime,
        instrument: str = "XAUUSD",
    ):
        """
        Initialize liquidity pool.

        Args:
            price: Pool price level
            strength: Pool strength score
            pool_type: Type of liquidity pool
            timestamp: Creation timestamp
            instrument: Trading instrument
        """
        self.price = price
        self.strength = strength
        self.type = pool_type
        self.timestamp = timestamp
        self.instrument = instrument
        self.touches = 0
        self.last_touch = None
        self.swept = False
        self.sweep_time = None
        self.sweep_price = None

        # Validate
        self._validate_pool()

    def _validate_pool(self):
        """Validate liquidity pool parameters."""
        if self.strength < 0 or self.strength > 1:
            raise ValueError(
                f"Pool strength must be between 0 and 1, got {self.strength}"
            )

        if self.price <= 0:
            raise ValueError(f"Pool price must be positive, got {self.price}")

    def add_touch(self, timestamp: datetime):
        """
        Record a touch at liquidity pool.

        Args:
            timestamp: Time of touch
        """
        self.touches += 1
        self.last_touch = timestamp

    def mark_swept(self, sweep_time: datetime, sweep_price: Decimal):
        """
        Mark liquidity pool as swept.

        Args:
            sweep_time: Time of sweep
            sweep_price: Price at which sweep occurred
        """
        self.swept = True
        self.sweep_time = sweep_time
        self.sweep_price = sweep_price

    def is_within_range(
        self, price: Decimal, tolerance_pips: Decimal = Decimal("5")
    ) -> bool:
        """
        Check if price is within liquidity pool range.

        Args:
            price: Price to check
            tolerance_pips: Tolerance in pips

        Returns:
            True if price is within range
        """
        tolerance = tolerance_pips / Decimal("10000")
        return abs(price - self.price) <= tolerance

    def get_price_level(self) -> PriceLevel:
        """
        Convert liquidity pool to price level.

        Returns:
            PriceLevel representation
        """
        return PriceLevel(
            price=self.price,
            strength=self.strength,
            level_type=f"LIQUIDITY_{self.type}",
            timestamp=self.timestamp,
            touches=self.touches,
            instrument=self.instrument,
        )

    def to_dict(self) -> dict:
        """Convert liquidity pool to dictionary representation."""
        return {
            "price": float(self.price),
            "strength": self.strength,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "touches": self.touches,
            "last_touch": self.last_touch.isoformat() if self.last_touch else None,
            "swept": self.swept,
            "sweep_time": self.sweep_time.isoformat() if self.sweep_time else None,
            "sweep_price": float(self.sweep_price) if self.sweep_price else None,
        }


class LiquiditySweep:
    """
    Liquidity sweep data structure.

    Represents a detected liquidity sweep with
    its characteristics and reversal potential.
    """

    def __init__(
        self,
        sweep_type: str,
        pool_price: Decimal,
        sweep_price: Decimal,
        sweep_time: datetime,
        reversal_price: Optional[Decimal] = None,
    ):
        """
        Initialize liquidity sweep.

        Args:
            sweep_type: Type of sweep (BUY_SIDE/SELL_SIDE)
            pool_price: Price of swept liquidity pool
            sweep_price: Price at which sweep occurred
            sweep_time: Time of sweep
            reversal_price: Expected reversal price
        """
        self.type = sweep_type
        self.pool_price = pool_price
        self.sweep_price = sweep_price
        self.sweep_time = sweep_time
        self.reversal_price = reversal_price
        self.extension_pips = abs(sweep_price - pool_price)
        self.strength = 0.0
        self.confirmed = False

        # Validate
        self._validate_sweep()

    def _validate_sweep(self):
        """Validate liquidity sweep parameters."""
        if self.pool_price <= 0 or self.sweep_price <= 0:
            raise ValueError("Pool and sweep prices must be positive")

        if self.sweep_time <= self.pool_price.timestamp:
            raise ValueError("Sweep time must be after pool creation")

    def calculate_strength(self, volume_at_sweep: float, avg_volume: float) -> float:
        """
        Calculate sweep strength based on volume and extension.

        Args:
            volume_at_sweep: Volume during sweep
            avg_volume: Average volume for context

        Returns:
            Strength score (0.0 to 1.0)
        """
        settings = get_settings()
        config = settings.smc.liquidity

        strength = 0.0

        # Volume-based strength
        volume_strength = 1.0
        if avg_volume > 0:
            volume_multiplier = volume_at_sweep / avg_volume
            volume_strength = min(
                1.0, volume_multiplier / config.volume_spike_multiplier
            )

        # Extension-based strength (optimal extension is 5-15 pips)
        extension_pips = float(self.extension_pips * 10000)
        if (
            config.sweep_extension_pips
            <= extension_pips
            <= config.sweep_extension_pips * 3
        ):
            extension_strength = 1.0
        elif extension_pips < config.sweep_extension_pips:
            extension_strength = 0.5
        else:
            extension_strength = 0.3

        # Combine strengths
        strength = (volume_strength * 0.6) + (extension_strength * 0.4)

        self.strength = min(1.0, max(0.0, strength))
        return self.strength

    def confirm_reversal(self, reversal_price: Decimal):
        """
        Confirm the sweep reversal.

        Args:
            reversal_price: Price where reversal confirmed
        """
        self.reversal_price = reversal_price
        self.confirmed = True

    def to_dict(self) -> dict:
        """Convert liquidity sweep to dictionary representation."""
        return {
            "type": self.type,
            "pool_price": float(self.pool_price),
            "sweep_price": float(self.sweep_price),
            "extension_pips": float(self.extension_pips),
            "sweep_time": self.sweep_time.isoformat(),
            "reversal_price": float(self.reversal_price)
            if self.reversal_price
            else None,
            "strength": self.strength,
            "confirmed": self.confirmed,
        }


class LiquidityAnalyzer:
    """
    Liquidity analyzer implementation.

    Identifies liquidity pools, detects sweeps,
    and analyzes liquidity flow patterns.
    """

    def __init__(self):
        """Initialize liquidity analyzer."""
        self.settings = get_settings()
        self.config = self.settings.smc.liquidity

    def identify_liquidity_pools(
        self, swing_points: List[SwingPoint], current_price: Decimal
    ) -> List[LiquidityPool]:
        """
        Identify liquidity pools from swing points.

        Args:
            swing_points: List of swing points
            current_price: Current market price

        Returns:
            List of liquidity pools
        """
        if len(swing_points) < 2:
            return []

        pools = []

        # Group nearby swing points
        for i in range(len(swing_points) - 1):
            current_sp = swing_points[i]
            next_sp = swing_points[i + 1]

            # Check if points form a liquidity pool
            if self._forms_liquidity_pool(current_sp, next_sp, current_price):
                pool = LiquidityPool(
                    price=current_sp.price,
                    strength=self._calculate_pool_strength(current_sp, next_sp),
                    pool_type=self._determine_pool_type(
                        current_sp, next_sp, current_price
                    ),
                    timestamp=current_sp.timestamp,
                    instrument=current_sp.instrument,
                )
                pools.append(pool)

        return pools

    def _forms_liquidity_pool(
        self, sp1: SwingPoint, sp2: SwingPoint, current_price: Decimal
    ) -> bool:
        """
        Check if two swing points form a liquidity pool.

        Args:
            sp1: First swing point
            sp2: Second swing point
            current_price: Current market price

        Returns:
            True if points form liquidity pool
        """
        # Pool forms if:
        # 1. Points are within configured range
        price_range = abs(sp2.price - sp1.price)
        range_pips = float(price_range * 10000)

        if range_pips > self.config.pool_range_pips:
            return False

        # 2. Current price is near the pool
        tolerance = self.config.pool_range_pips / Decimal("10000")
        near_pool = (
            abs(current_price - sp1.price) <= tolerance
            or abs(current_price - sp2.price) <= tolerance
        )

        return near_pool

    def _calculate_pool_strength(self, sp1: SwingPoint, sp2: SwingPoint) -> float:
        """
        Calculate liquidity pool strength.

        Args:
            sp1: First swing point
            sp2: Second swing point

        Returns:
            Pool strength score
        """
        # Strength based on:
        # 1. Number of touches at each point
        touches_strength = min(
            1.0, (sp1.touches + sp2.touches) / (self.config.min_pool_touches * 2)
        )

        # 2. Time since last touch (more recent = stronger)
        current_time = datetime.utcnow()
        sp1_age = (current_time - sp1.timestamp).total_seconds() / 3600  # Hours
        sp2_age = (current_time - sp2.timestamp).total_seconds() / 3600

        recency_strength = 1.0 - min(sp1_age, sp2_age) / 24.0  # Decay over 24 hours

        # 3. Strength of swing points
        point_strength = (sp1.strength + sp2.strength) / 2.0

        # Combine strengths
        total_strength = (
            (touches_strength * 0.4) + (recency_strength * 0.3) + (point_strength * 0.3)
        )

        return min(1.0, max(0.0, total_strength))

    def _determine_pool_type(
        self, sp1: SwingPoint, sp2: SwingPoint, current_price: Decimal
    ) -> str:
        """
        Determine liquidity pool type.

        Args:
            sp1: First swing point
            sp2: Second swing point
            current_price: Current market price

        Returns:
            Pool type string
        """
        # Determine if this is a high or low pool
        if sp1.is_high and sp2.is_high:
            return "HIGH"
        elif sp1.is_low and sp2.is_low:
            return "LOW"
        else:
            return "SIDE"

    def detect_liquidity_sweeps(
        self, pools: List[LiquidityPool], candles: List[Candle], current_price: Decimal
    ) -> List[LiquiditySweep]:
        """
        Detect liquidity sweeps from pools and price action.

        Args:
            pools: Identified liquidity pools
            candles: Recent candles for context
            current_price: Current market price

        Returns:
            List of detected sweeps
        """
        sweeps = []

        for pool in pools:
            if pool.swept:
                continue

            # Check for sweep pattern
            sweep = self._analyze_sweep_pattern(pool, candles, current_price)
            if sweep:
                sweeps.append(sweep)

        return sweeps

    def _analyze_sweep_pattern(
        self, pool: LiquidityPool, candles: List[Candle], current_price: Decimal
    ) -> Optional[LiquiditySweep]:
        """
        Analyze if a liquidity sweep has occurred.

        Args:
            pool: Liquidity pool to check
            candles: Recent candles for analysis
            current_price: Current market price

        Returns:
            Detected sweep or None
        """
        # Check if price has extended beyond pool
        extension_beyond_pool = False
        sweep_type = None
        sweep_price = None

        if pool.type == "HIGH":
            # High pool sweep: price breaks above high
            if current_price > pool.price:
                extension_beyond_pool = True
                sweep_type = "BUY_SIDE"
                sweep_price = current_price
        elif pool.type == "LOW":
            # Low pool sweep: price breaks below low
            if current_price < pool.price:
                extension_beyond_pool = True
                sweep_type = "SELL_SIDE"
                sweep_price = current_price

        if not extension_beyond_pool:
            return None

        # Check extension requirements
        extension_pips = abs(sweep_price - pool.price)
        if extension_pips < self.config.sweep_extension_pips:
            return None

        # Create sweep object
        sweep = LiquiditySweep(
            sweep_type=sweep_type,
            pool_price=pool.price,
            sweep_price=sweep_price,
            sweep_time=datetime.utcnow(),
        )

        # Calculate strength
        avg_volume = self._calculate_avg_volume(candles)
        current_candle = candles[-1] if candles else None
        volume_at_sweep = current_candle.volume if current_candle else 0

        sweep.calculate_strength(volume_at_sweep, avg_volume)

        return sweep

    def _calculate_avg_volume(self, candles: List[Candle]) -> float:
        """
        Calculate average volume over lookback period.

        Args:
            candles: List of candles

        Returns:
            Average volume
        """
        if not candles:
            return 0.0

        start_idx = max(0, len(candles) - self.config.avg_volume_period)
        relevant_candles = candles[start_idx:]

        volumes = [c.volume for c in relevant_candles if c.volume]
        return sum(volumes) / len(volumes) if volumes else 0.0

    def analyze_liquidity_flow(
        self,
        pools: List[LiquidityPool],
        sweeps: List[LiquiditySweep],
        current_price: Decimal,
    ) -> dict:
        """
        Analyze overall liquidity flow and patterns.

        Args:
            pools: Current liquidity pools
            sweeps: Recent liquidity sweeps
            current_price: Current market price

        Returns:
            Liquidity analysis dictionary
        """
        # Pool statistics
        total_pools = len(pools)
        high_pools = len([p for p in pools if p.type == "HIGH"])
        low_pools = len([p for p in pools if p.type == "LOW"])
        side_pools = len([p for p in pools if p.type == "SIDE"])

        # Sweep statistics
        total_sweeps = len(sweeps)
        buy_sweeps = len([s for s in sweeps if s.type == "BUY_SIDE"])
        sell_sweeps = len([s for s in sweeps if s.type == "SELL_SIDE"])
        confirmed_sweeps = len([s for s in sweeps if s.confirmed])

        # Current liquidity context
        nearest_high = None
        nearest_low = None
        nearest_high_dist = float("inf")
        nearest_low_dist = float("inf")

        for pool in pools:
            if pool.type == "HIGH":
                dist = abs(current_price - pool.price)
                if dist < nearest_high_dist:
                    nearest_high_dist = dist
                    nearest_high = pool
            elif pool.type == "LOW":
                dist = abs(current_price - pool.price)
                if dist < nearest_low_dist:
                    nearest_low_dist = dist
                    nearest_low = pool

        return {
            "total_pools": total_pools,
            "high_pools": high_pools,
            "low_pools": low_pools,
            "side_pools": side_pools,
            "total_sweeps": total_sweeps,
            "buy_sweeps": buy_sweeps,
            "sell_sweeps": sell_sweeps,
            "confirmed_sweeps": confirmed_sweeps,
            "sweep_rate": (confirmed_sweeps / total_sweeps * 100)
            if total_sweeps > 0
            else 0,
            "nearest_high_pool": nearest_high.to_dict() if nearest_high else None,
            "nearest_low_pool": nearest_low.to_dict() if nearest_low else None,
            "liquidity_score": self._calculate_liquidity_score(pools, sweeps),
        }

    def _calculate_liquidity_score(
        self, pools: List[LiquidityPool], sweeps: List[LiquiditySweep]
    ) -> float:
        """
        Calculate overall liquidity score.

        Args:
            pools: Liquidity pools
            sweeps: Liquidity sweeps

        Returns:
            Liquidity score (0.0 to 1.0)
        """
        if not pools:
            return 0.0

        # Pool strength component
        avg_pool_strength = sum(p.strength for p in pools) / len(pools)

        # Sweep activity component
        sweep_strength = 0.0
        if sweeps:
            avg_sweep_strength = sum(s.strength for s in sweeps) / len(sweeps)
            sweep_activity = min(1.0, len(sweeps) / 5.0)  # More sweeps = higher score
            sweep_strength = avg_sweep_strength * sweep_activity

        # Combine scores
        liquidity_score = (avg_pool_strength * 0.6) + (sweep_strength * 0.4)

        return min(1.0, max(0.0, liquidity_score))
