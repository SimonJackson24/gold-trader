"""
Trade model for XAUUSD Gold Trading System.

Represents an executed trade with full lifecycle management
including partial closes, profit/loss tracking, and status updates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Literal, Dict, Any
from enum import Enum
import json


class TradeStatus(Enum):
    """Trade status enumeration."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    STOPPED_OUT = "STOPPED_OUT"


class ExitReason(Enum):
    """Trade exit reason enumeration."""
    TP1_HIT = "TP1_HIT"
    TP2_HIT = "TP2_HIT"
    SL_HIT = "SL_HIT"
    MANUAL_CLOSE = "MANUAL_CLOSE"
    SIGNAL_CANCELLED = "SIGNAL_CANCELLED"
    EXPIRED = "EXPIRED"
    MARGIN_CALL = "MARGIN_CALL"


@dataclass
class PartialClose:
    """
    Partial close information for trade management.
    
    Records details of each partial close including
    size, price, and profit/loss.
    """
    time: datetime
    price: Decimal
    size: Decimal
    profit: Decimal
    reason: str
    
    def to_dict(self) -> dict:
        """Convert partial close to dictionary."""
        return {
            'time': self.time.isoformat(),
            'price': float(self.price),
            'size': float(self.size),
            'profit': float(self.profit),
            'reason': self.reason
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PartialClose':
        """Create partial close from dictionary."""
        return cls(
            time=datetime.fromisoformat(data['time']),
            price=Decimal(str(data['price'])),
            size=Decimal(str(data['size'])),
            profit=Decimal(str(data['profit'])),
            reason=data['reason']
        )


@dataclass
class Trade:
    """
    Complete trade lifecycle management.
    
    Tracks trade from entry to exit with all intermediate
    states, partial closes, and performance metrics.
    """
    # Trade details
    direction: Literal["BUY", "SELL"]
    position_size: Decimal
    profit_loss: Decimal
    profit_loss_pips: Decimal
    profit_loss_percentage: Decimal

    # Fields with default values or Optional
    trade_id: Optional[int] = None
    signal_id: Optional[str] = None
    instrument: str = "XAUUSD"
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    entry_price: Optional[Decimal] = None
    exit_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit_1: Optional[Decimal] = None
    take_profit_2: Optional[Decimal] = None
    highest_price: Optional[Decimal] = None
    lowest_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    status: TradeStatus = TradeStatus.PENDING
    exit_reason: Optional[ExitReason] = None
    partial_closes: List[PartialClose] = field(default_factory=list)
    tp1_hit: bool = False
    tp2_hit: bool = False
    sl_hit: bool = False
    breakeven_moved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate trade after initialization."""
        if self.direction not in ["BUY", "SELL"]:
            raise ValueError(f"Direction must be 'BUY' or 'SELL', got {self.direction}")
        
        if self.position_size < 0:
            raise ValueError(f"Position size cannot be negative, got {self.position_size}")
        
        # Validate price relationships if all prices are set
        if all([self.entry_price, self.stop_loss, self.take_profit_1]):
            self._validate_price_levels()
    
    def _validate_price_levels(self):
        """Validate price level relationships."""
        if self.direction == "BUY":
            if not (self.take_profit_1 > self.entry_price > self.stop_loss):
                raise ValueError("For BUY: TP1 > Entry > SL")
            if self.take_profit_2 and not (self.take_profit_2 > self.take_profit_1):
                raise ValueError("For BUY: TP2 > TP1")
        else:  # SELL
            if not (self.take_profit_1 < self.entry_price < self.stop_loss):
                raise ValueError("For SELL: TP1 < Entry < SL")
            if self.take_profit_2 and not (self.take_profit_2 < self.take_profit_1):
                raise ValueError("For SELL: TP2 < TP1")
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy trade."""
        return self.direction == "BUY"
    
    @property
    def is_sell(self) -> bool:
        """Check if this is a sell trade."""
        return self.direction == "SELL"
    
    @property
    def is_open(self) -> bool:
        """Check if trade is currently open."""
        return self.status == TradeStatus.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if trade is closed."""
        return self.status == TradeStatus.CLOSED
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate trade duration in minutes."""
        if not self.entry_time:
            return None
        
        end_time = self.exit_time or datetime.utcnow()
        return (end_time - self.entry_time).total_seconds() / 60
    
    @property
    def risk_pips(self) -> Optional[Decimal]:
        """Calculate risk in pips."""
        if not self.entry_price or not self.stop_loss:
            return None
        
        if self.is_buy:
            return self.entry_price - self.stop_loss
        else:
            return self.stop_loss - self.entry_price
    
    @property
    def current_pips(self) -> Optional[Decimal]:
        """Calculate current P&L in pips."""
        if not self.entry_price or not self.current_price:
            return None
        
        if self.is_buy:
            return self.current_price - self.entry_price
        else:
            return self.entry_price - self.current_price
    
    @property
    def current_profit_loss(self) -> Optional[Decimal]:
        """Calculate current P&L in monetary value."""
        if not self.current_pips or self.position_size == 0:
            return None
        
        # Simplified P&L calculation (would need lot size and pip value in real system)
        return self.current_pips * self.position_size * Decimal('10')  # Assuming $10 per pip per lot
    
    @property
    def remaining_position_size(self) -> Decimal:
        """Calculate remaining position size after partial closes."""
        closed_size = sum(pc.size for pc in self.partial_closes)
        return max(Decimal('0'), self.position_size - closed_size)
    
    @property
    def partial_closes_json(self) -> str:
        """Get partial closes as JSON string."""
        return json.dumps([pc.to_dict() for pc in self.partial_closes])
    
    def open_trade(self, entry_price: Decimal, entry_time: datetime):
        """
        Mark trade as opened with entry details.
        
        Args:
            entry_price: Actual entry price
            entry_time: Entry timestamp
        """
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.current_price = entry_price
        self.highest_price = entry_price
        self.lowest_price = entry_price
        self.status = TradeStatus.OPEN
        self.updated_at = datetime.utcnow()
    
    def update_price(self, current_price: Decimal):
        """
        Update current price and track extremes.
        
        Args:
            current_price: New current price
        """
        self.current_price = current_price
        self.updated_at = datetime.utcnow()
        
        # Update price extremes
        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price
        
        if self.lowest_price is None or current_price < self.lowest_price:
            self.lowest_price = current_price
        
        # Calculate current P&L
        self._calculate_current_pl()
    
    def _calculate_current_pl(self):
        """Calculate current profit/loss."""
        if not self.entry_price or not self.current_price:
            return
        
        if self.is_buy:
            self.profit_loss_pips = self.current_price - self.entry_price
        else:
            self.profit_loss_pips = self.entry_price - self.current_price
        
        # Convert to monetary value (simplified)
        self.profit_loss = self.profit_loss_pips * self.remaining_position_size * Decimal('10')
        
        # Calculate percentage
        if self.position_size > 0:
            self.profit_loss_percentage = (self.profit_loss / (self.position_size * Decimal('1000'))) * 100
    
    def partial_close(self, size: Decimal, price: Decimal, reason: str):
        """
        Execute a partial close.
        
        Args:
            size: Size to close
            price: Close price
            reason: Reason for close
        """
        if size > self.remaining_position_size:
            raise ValueError(f"Cannot close {size}, remaining position is {self.remaining_position_size}")
        
        # Calculate profit for this partial close
        if self.is_buy:
            profit_pips = price - self.entry_price
        else:
            profit_pips = self.entry_price - price
        
        profit = profit_pips * size * Decimal('10')
        
        # Record partial close
        partial = PartialClose(
            time=datetime.utcnow(),
            price=price,
            size=size,
            profit=profit,
            reason=reason
        )
        self.partial_closes.append(partial)
        self.updated_at = datetime.utcnow()
        
        # Update flags
        if reason == "TP1_HIT":
            self.tp1_hit = True
        elif reason == "TP2_HIT":
            self.tp2_hit = True
    
    def close_trade(self, exit_price: Decimal, exit_time: datetime, reason: ExitReason):
        """
        Close the trade completely.
        
        Args:
            exit_price: Exit price
            exit_time: Exit timestamp
            reason: Exit reason
        """
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = reason
        self.status = TradeStatus.CLOSED
        self.updated_at = datetime.utcnow()
        
        # Calculate final P&L
        if self.is_buy:
            self.profit_loss_pips = exit_price - self.entry_price
        else:
            self.profit_loss_pips = self.entry_price - exit_price
        
        # Include partial closes in final P&L
        partial_profit = sum(pc.profit for pc in self.partial_closes)
        remaining_size = self.remaining_position_size
        
        if remaining_size > 0:
            final_profit = self.profit_loss_pips * remaining_size * Decimal('10')
            self.profit_loss = partial_profit + final_profit
        else:
            self.profit_loss = partial_profit
        
        # Update flags
        if reason == ExitReason.SL_HIT:
            self.sl_hit = True
        elif reason == ExitReason.TP1_HIT:
            self.tp1_hit = True
        elif reason == ExitReason.TP2_HIT:
            self.tp2_hit = True
    
    def move_stop_to_breakeven(self):
        """Move stop loss to breakeven (entry price)."""
        if self.entry_price and not self.breakeven_moved:
            self.stop_loss = self.entry_price
            self.breakeven_moved = True
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert trade to dictionary representation."""
        return {
            'trade_id': self.trade_id,
            'signal_id': self.signal_id,
            'instrument': self.instrument,
            'direction': self.direction,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'duration_minutes': self.duration_minutes,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'exit_price': float(self.exit_price) if self.exit_price else None,
            'highest_price': float(self.highest_price) if self.highest_price else None,
            'lowest_price': float(self.lowest_price) if self.lowest_price else None,
            'current_price': float(self.current_price) if self.current_price else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit_1': float(self.take_profit_1) if self.take_profit_1 else None,
            'take_profit_2': float(self.take_profit_2) if self.take_profit_2 else None,
            'position_size': float(self.position_size),
            'profit_loss': float(self.profit_loss),
            'profit_loss_pips': float(self.profit_loss_pips),
            'profit_loss_percentage': float(self.profit_loss_percentage),
            'status': self.status.value,
            'exit_reason': self.exit_reason.value if self.exit_reason else None,
            'partial_closes': [pc.to_dict() for pc in self.partial_closes],
            'tp1_hit': self.tp1_hit,
            'tp2_hit': self.tp2_hit,
            'sl_hit': self.sl_hit,
            'breakeven_moved': self.breakeven_moved,
            'remaining_position_size': float(self.remaining_position_size),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Trade':
        """Create trade from dictionary representation."""
        # Handle enum conversions
        status = TradeStatus(data['status']) if isinstance(data.get('status'), str) else data.get('status')
        exit_reason = ExitReason(data['exit_reason']) if data.get('exit_reason') and isinstance(data['exit_reason'], str) else data.get('exit_reason')
        
        # Convert timestamps
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow()
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.utcnow()
        entry_time = datetime.fromisoformat(data['entry_time']) if data.get('entry_time') else None
        exit_time = datetime.fromisoformat(data['exit_time']) if data.get('exit_time') else None
        
        # Convert partial closes
        partial_closes = []
        for pc_data in data.get('partial_closes', []):
            partial_closes.append(PartialClose.from_dict(pc_data))
        
        return cls(
            trade_id=data.get('trade_id'),
            signal_id=data.get('signal_id'),
            instrument=data.get('instrument', 'XAUUSD'),
            direction=data['direction'],
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=Decimal(str(data['entry_price'])) if data.get('entry_price') else None,
            exit_price=Decimal(str(data['exit_price'])) if data.get('exit_price') else None,
            stop_loss=Decimal(str(data['stop_loss'])) if data.get('stop_loss') else None,
            take_profit_1=Decimal(str(data['take_profit_1'])) if data.get('take_profit_1') else None,
            take_profit_2=Decimal(str(data['take_profit_2'])) if data.get('take_profit_2') else None,
            highest_price=Decimal(str(data['highest_price'])) if data.get('highest_price') else None,
            lowest_price=Decimal(str(data['lowest_price'])) if data.get('lowest_price') else None,
            current_price=Decimal(str(data['current_price'])) if data.get('current_price') else None,
            position_size=Decimal(str(data['position_size'])),
            profit_loss=Decimal(str(data['profit_loss'])),
            profit_loss_pips=Decimal(str(data['profit_loss_pips'])),
            profit_loss_percentage=Decimal(str(data['profit_loss_percentage'])),
            status=status,
            exit_reason=exit_reason,
            partial_closes=partial_closes,
            tp1_hit=data.get('tp1_hit', False),
            tp2_hit=data.get('tp2_hit', False),
            sl_hit=data.get('sl_hit', False),
            breakeven_moved=data.get('breakeven_moved', False),
            created_at=created_at,
            updated_at=updated_at,
            notes=data.get('notes')
        )