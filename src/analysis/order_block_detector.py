"""
Order Block detector for Smart Money Concepts.

Identifies institutional order blocks and accumulation zones
where significant price movements originate.
"""

from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from ..models.candle import Candle
from ..models.market_data import PriceLevel, SwingPoint
from ..config import get_settings


class OrderBlockType:
    """Order block type enumeration."""
    BULLISH = "BULLISH"  # Order block before upward move
    BEARISH = "BEARISH"  # Order block before downward move


class OrderBlock:
    """
    Order block data structure.
    
    Represents an identified order block with its characteristics
    and validation metrics.
    """
    
    def __init__(self, block_type: str, candle: Candle, strength: float = 0.0):
        """
        Initialize order block.
        
        Args:
            block_type: BULLISH or BEARISH
            candle: Order block candle
            strength: Initial strength score
        """
        self.type = block_type
        self.candle = candle
        self.price = candle.close
        self.high = candle.high
        self.low = candle.low
        self.volume = candle.volume
        self.timestamp = candle.timestamp
        self.strength = strength
        self.touches = 0
        self.last_touch = None
        self.respected = False
        self.broken = False
        self.instrument = candle.instrument
        
        # Additional properties
        self.wick_ratio = candle.body_percentage / 100.0
        self.range_size = candle.total_range
        self.is_rejection_candle = self._is_rejection_pattern()
        self.near_round_number = self._is_near_round_number()
        
        # Validate
        self._validate_block()
    
    def _validate_block(self):
        """Validate order block parameters."""
        if self.type not in [OrderBlockType.BULLISH, OrderBlockType.BEARISH]:
            raise ValueError(f"Invalid order block type: {self.type}")
        
        if self.range_size <= 0:
            raise ValueError("Order block range must be positive")
    
    def _is_rejection_pattern(self) -> bool:
        """
        Check if candle shows rejection pattern.
        
        Returns:
            True if candle has rejection characteristics
        """
        # Large wick relative to body (wick > 40% of range)
        if self.wick_ratio > 0.6:
            return True
        
        # Strong rejection at one end
        if self.candle.is_bullish:
            # Bullish rejection: strong upper wick
            return self.candle.upper_wick > (self.candle.body_size * 0.8)
        else:
            # Bearish rejection: strong lower wick
            return self.candle.lower_wick > (self.candle.body_size * 0.8)
    
    def _is_near_round_number(self) -> bool:
        """
        Check if order block is near psychological level.
        
        Returns:
            True if near round number
        """
        settings = get_settings()
        config = settings.smc.order_block
        
        if not config.near_round_numbers:
            return False
        
        # Check if price is within specified pips of round number
        price_float = float(self.price)
        round_numbers = [int(price_float // 100) * 100 + x for x in [0, 50, 100]]
        
        for round_num in round_numbers:
            distance = abs(price_float - round_num)
            if distance <= (config.round_number_pips / 100):
                return True
        
        return False
    
    def calculate_strength(self, avg_volume: float, volume_profile: dict = None) -> float:
        """
        Calculate order block strength based on multiple factors.
        
        Args:
            avg_volume: Average volume over lookback period
            volume_profile: Volume profile data (optional)
            
        Returns:
            Strength score (0.0 to 1.0)
        """
        settings = get_settings()
        config = settings.smc.order_block
        
        strength = 0.0
        
        # Volume-based strength
        volume_strength = 1.0
        if self.volume and avg_volume > 0:
            volume_multiplier = self.volume / avg_volume
            volume_strength = min(1.0, volume_multiplier / config.min_volume_multiplier)
        
        # Range-based strength (significant price movement)
        avg_range = 50.0  # Would calculate from historical data
        range_strength = min(1.0, self.range_size / avg_range)
        
        # Wick-based strength (rejection pattern)
        wick_strength = 1.0
        if config.require_rejection:
            wick_strength = 1.0 if self.is_rejection_candle else 0.5
        
        # Round number proximity strength
        round_number_strength = 1.2 if self.near_round_number else 1.0
        
        # Combine strengths with weights
        strength = (
            (volume_strength * 0.4) +
            (range_strength * 0.3) +
            (wick_strength * 0.2) +
            (round_number_strength * 0.1)
        )
        
        self.strength = min(1.0, max(0.0, strength))
        return self.strength
    
    def add_touch(self, timestamp: datetime):
        """
        Record a price touch at order block level.
        
        Args:
            timestamp: Time of touch
        """
        self.touches += 1
        self.last_touch = timestamp
    
    def mark_respected(self):
        """Mark order block as respected by price."""
        self.respected = True
    
    def mark_broken(self):
        """Mark order block as broken by price."""
        self.broken = True
    
    def is_valid(self, min_strength: float = 0.3) -> bool:
        """
        Check if order block meets minimum requirements.
        
        Args:
            min_strength: Minimum strength threshold
            
        Returns:
            True if order block is valid
        """
        return (
            self.strength >= min_strength and
            self.wick_ratio <= config.wick_ratio_threshold and
            self.range_size >= config.min_candle_range
        )
    
    def get_price_level(self) -> PriceLevel:
        """
        Convert order block to price level for analysis.
        
        Returns:
            PriceLevel representation
        """
        return PriceLevel(
            price=self.price,
            strength=self.strength,
            level_type="ORDER_BLOCK",
            timestamp=self.timestamp,
            touches=self.touches,
            volume_at_level=self.volume,
            instrument=self.instrument
        )
    
    def to_dict(self) -> dict:
        """Convert order block to dictionary representation."""
        return {
            'type': self.type,
            'price': float(self.price),
            'high': float(self.high),
            'low': float(self.low),
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'strength': self.strength,
            'touches': self.touches,
            'last_touch': self.last_touch.isoformat() if self.last_touch else None,
            'respected': self.respected,
            'broken': self.broken,
            'wick_ratio': self.wick_ratio,
            'is_rejection_candle': self.is_rejection_candle,
            'near_round_number': self.near_round_number,
            'candle': self.candle.to_dict()
        }


class OrderBlockDetector:
    """
    Order block detector implementation.
    
    Scans candle sequences to identify institutional order blocks
    and accumulation zones.
    """
    
    def __init__(self):
        """Initialize order block detector."""
        self.settings = get_settings()
        self.config = self.settings.smc.order_block
    
    def detect_order_blocks(self, candles: List[Candle], 
                             swing_points: List[SwingPoint] = None) -> List[OrderBlock]:
        """
        Detect order blocks in candle sequence.
        
        Args:
            candles: List of candles to analyze
            swing_points: Optional swing points for context
            
        Returns:
            List of detected order blocks
        """
        if len(candles) < self.config.lookback_candles:
            return []
        
        order_blocks = []
        avg_volume = self._calculate_avg_volume(candles)
        
        # Scan for order block patterns
        for i in range(self.config.lookback_candles, len(candles)):
            candle = candles[i]
            
            # Check if this could be an order block
            if self._is_potential_order_block(candle, candles, i):
                ob = OrderBlock(
                    block_type=self._determine_block_type(candle, candles, i),
                    candle=candle
                )
                ob.calculate_strength(avg_volume)
                
                if ob.is_valid(self.config.min_candle_range):
                    order_blocks.append(ob)
        
        return order_blocks
    
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
        
        start_idx = max(0, len(candles) - self.config.avg_volume_periods)
        relevant_candles = candles[start_idx:]
        
        volumes = [c.volume for c in relevant_candles if c.volume]
        return sum(volumes) / len(volumes) if volumes else 0.0
    
    def _is_potential_order_block(self, candle: Candle, candles: List[Candle], 
                                index: int) -> bool:
        """
        Check if candle could be an order block.
        
        Args:
            candle: Candle to check
            candles: Full candle sequence
            index: Index of candle in sequence
            
        Returns:
            True if candle could be order block
        """
        # Need previous and next candles for context
        if index == 0 or index >= len(candles) - 1:
            return False
        
        prev_candle = candles[index - 1]
        next_candle = candles[index + 1]
        
        # Check for strong move after this candle
        if not self._has_strong_move(next_candle, candle):
            return False
        
        # Check if this candle has characteristics of order block
        return (
            self._has_significant_range(candle) and
            self._has_volume_spike(candle) and
            self._shows_accumulation(candle, prev_candle, next_candle)
        )
    
    def _has_strong_move(self, next_candle: Candle, current_candle: Candle) -> bool:
        """
        Check if next candle shows strong move away from current.
        
        Args:
            next_candle: Next candle after potential OB
            current_candle: Current candle being evaluated
            
        Returns:
            True if strong move detected
        """
        # Strong move: significant price change in direction away from current
        price_change = abs(next_candle.close - current_candle.close)
        threshold = current_candle.total_range * 0.5  # 50% of current range
        
        return price_change >= threshold
    
    def _has_significant_range(self, candle: Candle) -> bool:
        """
        Check if candle has significant price range.
        
        Args:
            candle: Candle to evaluate
            
        Returns:
            True if range is significant
        """
        return candle.total_range >= self.config.min_candle_range
    
    def _has_volume_spike(self, candle: Candle) -> bool:
        """
        Check if candle has volume spike.
        
        Args:
            candle: Candle to evaluate
            
        Returns:
            True if volume spike detected
        """
        if not candle.volume:
            return False
        
        # Would compare with average volume here
        # For now, assume significant volume if above 0
        return candle.volume > 0
    
    def _shows_accumulation(self, candle: Candle, prev_candle: Candle, 
                           next_candle: Candle) -> bool:
        """
        Check if candle shows accumulation pattern.
        
        Args:
            candle: Current candle
            prev_candle: Previous candle
            next_candle: Next candle
            
        Returns:
            True if accumulation pattern detected
        """
        # Accumulation: price consolidation before breakout
        # Small body with overlapping ranges
        body_overlap = (
            min(candle.high, prev_candle.high) >= max(candle.low, prev_candle.low)
        )
        
        return (
            candle.body_percentage <= 40 and  # Small body
            body_overlap and  # Overlapping ranges
            abs(candle.close - prev_candle.close) < candle.total_range * 0.3
        )
    
    def _determine_block_type(self, candle: Candle, candles: List[Candle], 
                           index: int) -> str:
        """
        Determine order block type based on context.
        
        Args:
            candle: Candle to classify
            candles: Full candle sequence
            index: Index of candle
            
        Returns:
            Order block type
        """
        # Look at next few candles to determine direction
        future_candles = candles[index+1:index+4] if index+4 < len(candles) else []
        
        if not future_candles:
            return OrderBlockType.BULLISH  # Default
        
        # Count bullish vs bearish candles in future
        bullish_count = sum(1 for c in future_candles if c.is_bullish)
        bearish_count = len(future_candles) - bullish_count
        
        # If strong upward move follows, it's a bullish order block
        if bullish_count > bearish_count * 1.5:
            return OrderBlockType.BULLISH
        
        # If strong downward move follows, it's a bearish order block
        elif bearish_count > bullish_count * 1.5:
            return OrderBlockType.BEARISH
        
        # Default based on candle direction
        return OrderBlockType.BULLISH if candle.is_bullish else OrderBlockType.BEARISH
    
    def get_active_order_blocks(self, order_blocks: List[OrderBlock], 
                             current_price: Decimal, max_age_minutes: int = 240) -> List[OrderBlock]:
        """
        Get active (unbroken) order blocks within age limit.
        
        Args:
            order_blocks: List of all detected order blocks
            current_price: Current market price
            max_age_minutes: Maximum age in minutes
            
        Returns:
            List of active order blocks
        """
        active_obs = []
        current_time = datetime.utcnow()
        
        for ob in order_blocks:
            # Check age
            age_minutes = (current_time - ob.timestamp).total_seconds() / 60
            if age_minutes > max_age_minutes:
                continue
            
            # Check if broken
            if ob.broken:
                continue
            
            # Check if price is near
            tolerance = Decimal('0.0010')  # 10 pips tolerance
            if abs(current_price - ob.price) <= tolerance:
                ob.add_touch(current_time)
            
            active_obs.append(ob)
        
        # Sort by strength (strongest first)
        active_obs.sort(key=lambda x: x.strength, reverse=True)
        return active_obs
    
    def validate_order_block_respect(self, order_block: OrderBlock, 
                                  current_price: Decimal) -> bool:
        """
        Validate if an order block has been respected.
        
        Args:
            order_block: Order block to validate
            current_price: Current market price
            
        Returns:
            True if order block is respected
        """
        if not order_block:
            return False
        
        # Check minimum touches
        if order_block.touches < self.config.min_touches:
            return False
        
        # Check for strong reaction away from OB
        tolerance = order_block.range_size * 0.3  # 30% of OB range
        
        if order_block.type == OrderBlockType.BULLISH:
            # Bullish OB respected if price moves up significantly
            return current_price > (order_block.price + tolerance)
        else:
            # Bearish OB respected if price moves down significantly
            return current_price < (order_block.price - tolerance)
    
    def get_order_block_statistics(self, order_blocks: List[OrderBlock]) -> dict:
        """
        Get statistics for detected order blocks.
        
        Args:
            order_blocks: List of order blocks to analyze
            
        Returns:
            Statistics dictionary
        """
        if not order_blocks:
            return {}
        
        total = len(order_blocks)
        bullish = len([ob for ob in order_blocks if ob.type == OrderBlockType.BULLISH])
        bearish = len([ob for ob in order_blocks if ob.type == OrderBlockType.BEARISH])
        respected = len([ob for ob in order_blocks if ob.respected])
        broken = len([ob for ob in order_blocks if ob.broken])
        
        avg_strength = sum(ob.strength for ob in order_blocks) / total
        avg_touches = sum(ob.touches for ob in order_blocks) / total
        
        return {
            'total_order_blocks': total,
            'bullish_blocks': bullish,
            'bearish_blocks': bearish,
            'respected_blocks': respected,
            'broken_blocks': broken,
            'respect_rate': (respected / total * 100) if total > 0 else 0,
            'avg_strength': avg_strength,
            'avg_touches': avg_touches,
            'strongest_block': max(order_blocks, key=lambda x: x.strength) if order_blocks else None,
            'weakest_block': min(order_blocks, key=lambda x: x.strength) if order_blocks else None
        }