"""
Market data models for real-time price information.

Contains models for tick data, market snapshots, and price updates
received from MT5 connector.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Tick:
    """
    Real-time tick data from MT5.
    
    Represents a single price tick with bid/ask prices and volume.
    """
    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    last: Optional[Decimal] = None
    volume: Optional[int] = None
    spread_points: Optional[int] = None
    
    def __post_init__(self):
        """Validate tick data after initialization."""
        if self.bid >= self.ask:
            raise ValueError(f"Bid price ({self.bid}) cannot be greater than or equal to ask price ({self.ask})")
        
        if self.spread_points is None:
            self.spread_points = int((self.ask - self.bid) * 10000)  # Convert to points
    
    @property
    def mid_price(self) -> Decimal:
        """Calculate mid price (average of bid and ask)."""
        return (self.bid + self.ask) / Decimal('2')
    
    @property
    def spread_pips(self) -> Decimal:
        """Calculate spread in pips."""
        return (self.ask - self.bid) * Decimal('100')
    
    def to_dict(self) -> dict:
        """Convert tick to dictionary representation."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'bid': float(self.bid),
            'ask': float(self.ask),
            'last': float(self.last) if self.last else None,
            'volume': self.volume,
            'spread_points': self.spread_points,
            'mid_price': float(self.mid_price),
            'spread_pips': float(self.spread_pips)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Tick':
        """Create tick from dictionary representation."""
        return cls(
            symbol=data['symbol'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            bid=Decimal(str(data['bid'])),
            ask=Decimal(str(data['ask'])),
            last=Decimal(str(data['last'])) if data.get('last') else None,
            volume=data.get('volume'),
            spread_points=data.get('spread_points')
        )


@dataclass
class MarketSnapshot:
    """
    Complete market snapshot at a point in time.
    
    Combines current tick data with additional market context
    like session information and volatility metrics.
    """
    tick: Tick
    session: str  # ASIAN, LONDON, NY, NY_OVERLAP
    volatility: Optional[float] = None
    atr: Optional[Decimal] = None
    momentum: Optional[float] = None
    trend_direction: Optional[str] = None  # BULLISH, BEARISH, RANGING
    
    @property
    def symbol(self) -> str:
        """Get symbol from tick data."""
        return self.tick.symbol
    
    @property
    def timestamp(self) -> datetime:
        """Get timestamp from tick data."""
        return self.tick.timestamp
    
    @property
    def current_price(self) -> Decimal:
        """Get current mid price."""
        return self.tick.mid_price
    
    def to_dict(self) -> dict:
        """Convert market snapshot to dictionary representation."""
        result = self.tick.to_dict()
        result.update({
            'session': self.session,
            'volatility': self.volatility,
            'atr': float(self.atr) if self.atr else None,
            'momentum': self.momentum,
            'trend_direction': self.trend_direction
        })
        return result


@dataclass
class PriceLevel:
    """
    Price level with associated metadata.
    
    Used for support/resistance levels, order blocks, FVG zones, etc.
    """
    price: Decimal
    strength: float  # 0.0 to 1.0
    level_type: str  # SUPPORT, RESISTANCE, ORDER_BLOCK, FVG_TOP, FVG_BOTTOM
    timestamp: datetime
    touches: int = 0
    last_touch: Optional[datetime] = None
    volume_at_level: Optional[int] = None
    instrument: Optional[str] = None
    
    def __post_init__(self):
        """Validate price level after initialization."""
        if not 0 <= self.strength <= 1:
            raise ValueError(f"Strength must be between 0 and 1, got {self.strength}")
        
        if self.touches < 0:
            raise ValueError(f"Touches cannot be negative, got {self.touches}")
    
    def add_touch(self, timestamp: datetime):
        """Record a price touch at this level."""
        self.touches += 1
        self.last_touch = timestamp
    
    def is_respectable(self, min_touches: int = 2) -> bool:
        """Check if level has been respected enough times."""
        return self.touches >= min_touches
    
    def to_dict(self) -> dict:
        """Convert price level to dictionary representation."""
        return {
            'price': float(self.price),
            'strength': self.strength,
            'level_type': self.level_type,
            'timestamp': self.timestamp.isoformat(),
            'touches': self.touches,
            'last_touch': self.last_touch.isoformat() if self.last_touch else None,
            'volume_at_level': self.volume_at_level,
            'instrument': self.instrument
        }


@dataclass
class SwingPoint:
    """
    Swing point (high/low) in market structure.
    
    Represents significant highs and lows that form market structure.
    """
    price: Decimal
    timestamp: datetime
    point_type: str  # HIGH, LOW
    strength: float  # 0.0 to 1.0 based on surrounding structure
    volume: Optional[int] = None
    instrument: Optional[str] = None
    confirmed: bool = False
    
    def __post_init__(self):
        """Validate swing point after initialization."""
        if self.point_type not in ['HIGH', 'LOW']:
            raise ValueError(f"Point type must be 'HIGH' or 'LOW', got {self.point_type}")
        
        if not 0 <= self.strength <= 1:
            raise ValueError(f"Strength must be between 0 and 1, got {self.strength}")
    
    @property
    def is_high(self) -> bool:
        """Check if this is a swing high."""
        return self.point_type == 'HIGH'
    
    @property
    def is_low(self) -> bool:
        """Check if this is a swing low."""
        return self.point_type == 'LOW'
    
    def to_dict(self) -> dict:
        """Convert swing point to dictionary representation."""
        return {
            'price': float(self.price),
            'timestamp': self.timestamp.isoformat(),
            'point_type': self.point_type,
            'strength': self.strength,
            'volume': self.volume,
            'instrument': self.instrument,
            'confirmed': self.confirmed
        }