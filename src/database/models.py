"""
SQLAlchemy ORM models for XAUUSD Gold Trading System.

Defines all database tables and relationships
matching the database schema specification.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, DECIMAL, Boolean,
    DateTime, Date, JSON, ForeignKey, Index, CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from .connection import Base


class Signal(Base):
    """
    Trading signals table.
    
    Stores all generated trading signals with SMC context
    and risk management information.
    """
    __tablename__ = "signals"
    
    # Primary key
    signal_id = Column(String(50), primary_key=True)
    
    # Basic information
    instrument = Column(String(20), nullable=False, default="XAUUSD")
    direction = Column(String(4), nullable=False)
    
    # Price levels
    entry_price = Column(DECIMAL(10, 5), nullable=False)
    stop_loss = Column(DECIMAL(10, 5), nullable=False)
    take_profit_1 = Column(DECIMAL(10, 5), nullable=True)
    take_profit_2 = Column(DECIMAL(10, 5), nullable=True)
    
    # Risk metrics
    risk_reward_ratio = Column(DECIMAL(5, 2), nullable=True)
    position_size = Column(DECIMAL(8, 2), nullable=True)
    risk_percentage = Column(DECIMAL(5, 2), nullable=True)
    
    # SMC context
    setup_type = Column(String(100), nullable=True)
    market_structure = Column(String(50), nullable=True)
    confluence_factors = Column(JSON, nullable=True)
    confidence_score = Column(DECIMAL(3, 2), nullable=True)
    
    # Timeframe analysis
    h4_context = Column(Text, nullable=True)
    h1_context = Column(Text, nullable=True)
    m15_context = Column(Text, nullable=True)
    
    # Session information
    session = Column(String(20), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False)
    
    # Telegram
    telegram_message_id = Column(BigInteger, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="signal", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("direction IN ('BUY', 'SELL')", name="check_direction"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="check_confidence"),
        CheckConstraint("status IN ('ACTIVE', 'FILLED', 'CANCELLED', 'EXPIRED')", name="check_status"),
        CheckConstraint(
            "(direction = 'BUY' AND entry_price > stop_loss) OR (direction = 'SELL' AND entry_price < stop_loss)",
            name="signals_entry_sl_check"
        ),
        Index('idx_signals_instrument_status', 'instrument', 'status'),
        Index('idx_signals_created_at', 'created_at'),
        Index('idx_signals_confidence', 'confidence_score'),
        Index('idx_signals_session', 'session'),
        Index('idx_signals_setup_type', 'setup_type')
    )


class Trade(Base):
    """
    Trades table.
    
    Stores executed trades with full lifecycle management
    including partial closes and P&L tracking.
    """
    __tablename__ = "trades"
    
    # Primary key
    trade_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    signal_id = Column(String(50), ForeignKey('signals.signal_id', ondelete='CASCADE'), nullable=True)
    
    # Trade timing
    entry_time = Column(DateTime, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    
    # Price information
    entry_price = Column(DECIMAL(10, 5), nullable=True)
    exit_price = Column(DECIMAL(10, 5), nullable=True)
    highest_price = Column(DECIMAL(10, 5), nullable=True)
    lowest_price = Column(DECIMAL(10, 5), nullable=True)
    
    # Profit/Loss
    profit_loss = Column(DECIMAL(10, 2), nullable=True)
    profit_loss_pips = Column(DECIMAL(8, 2), nullable=True)
    profit_loss_percentage = Column(DECIMAL(6, 2), nullable=True)
    
    # Position information
    position_size = Column(DECIMAL(8, 2), nullable=False)
    
    # Trade status
    status = Column(String(20), nullable=False)
    
    # Partial closes
    partial_closes = Column(JSON, default='[]')
    tp1_hit = Column(Boolean, default=False)
    tp2_hit = Column(Boolean, default=False)
    sl_hit = Column(Boolean, default=False)
    breakeven_moved = Column(Boolean, default=False)
    
    # Exit reason
    exit_reason = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    signal = relationship("Signal", back_populates="trades")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'OPEN', 'CLOSED', 'CANCELLED', 'STOPPED_OUT')", name="check_trade_status"),
        Index('idx_trades_signal_id', 'signal_id'),
        Index('idx_trades_status', 'status'),
        Index('idx_trades_entry_time', 'entry_time'),
        Index('idx_trades_profit_loss', 'profit_loss'),
        Index('idx_trades_open', 'entry_time', postgresql_where="status = 'OPEN'")
    )


class PerformanceMetric(Base):
    """
    Performance metrics table.
    
    Stores aggregated performance statistics
    by instrument and date.
    """
    __tablename__ = "performance_metrics"
    
    # Primary key
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Instrument and date
    instrument = Column(String(20), nullable=False)
    metric_date = Column(Date, nullable=False)
    
    # Signal statistics
    total_signals = Column(Integer, default=0)
    signals_filled = Column(Integer, default=0)
    signals_cancelled = Column(Integer, default=0)
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    breakeven_trades = Column(Integer, default=0)
    
    # Performance metrics
    win_rate = Column(DECIMAL(5, 2), nullable=True)
    average_rr = Column(DECIMAL(5, 2), nullable=True)
    profit_factor = Column(DECIMAL(6, 2), nullable=True)
    
    # Profit/Loss
    total_pips = Column(DECIMAL(10, 2), nullable=True)
    total_profit_loss = Column(DECIMAL(12, 2), nullable=True)
    largest_win = Column(DECIMAL(10, 2), nullable=True)
    largest_loss = Column(DECIMAL(10, 2), nullable=True)
    average_win = Column(DECIMAL(10, 2), nullable=True)
    average_loss = Column(DECIMAL(10, 2), nullable=True)
    
    # Risk metrics
    max_drawdown = Column(DECIMAL(10, 2), nullable=True)
    max_drawdown_percentage = Column(DECIMAL(6, 2), nullable=True)
    sharpe_ratio = Column(DECIMAL(6, 3), nullable=True)
    
    # Trade duration
    average_trade_duration_minutes = Column(Integer, nullable=True)
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint and indexes
    __table_args__ = (
        UniqueConstraint('instrument', 'metric_date', name='uq_performance_instrument_date'),
        Index('idx_performance_instrument_date', 'instrument', 'metric_date'),
        Index('idx_performance_win_rate', 'win_rate'),
        Index('idx_performance_profit_loss', 'total_profit_loss')
    )


class PriceHistory(Base):
    """
    Price history table.
    
    Stores historical OHLCV data for backtesting
    and analysis purposes.
    """
    __tablename__ = "price_history"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Instrument and timeframe
    instrument = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    
    # Timestamp and OHLC
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(DECIMAL(10, 5), nullable=False)
    high_price = Column(DECIMAL(10, 5), nullable=False)
    low_price = Column(DECIMAL(10, 5), nullable=False)
    close_price = Column(DECIMAL(10, 5), nullable=False)
    
    # Volume
    volume = Column(BigInteger, nullable=True)
    tick_volume = Column(BigInteger, nullable=True)
    spread = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("timeframe IN ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1')", name="check_timeframe"),
        UniqueConstraint('instrument', 'timeframe', 'timestamp', name='uq_price_history'),
        Index('idx_price_history_instrument_timeframe_timestamp', 'instrument', 'timeframe', 'timestamp'),
        Index('idx_price_history_timestamp', 'timestamp'),
        CheckConstraint('high_price >= low_price', name="check_high_low"),
        CheckConstraint('high_price >= open_price', name="check_high_open"),
        CheckConstraint('high_price >= close_price', name="check_high_close"),
        CheckConstraint('low_price <= open_price', name="check_low_open"),
        CheckConstraint('low_price <= close_price', name="check_low_close")
    )


class SystemConfig(Base):
    """
    System configuration table.
    
    Stores dynamic configuration parameters
    that can be updated at runtime.
    """
    __tablename__ = "system_config"
    
    # Primary key
    config_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Configuration key and value
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    
    # Category and description
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # Data type and validation
    data_type = Column(String(20), nullable=False)
    validation_rule = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String(50), nullable=True)
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("data_type IN ('string', 'integer', 'float', 'boolean', 'json')", name="check_data_type"),
        Index('idx_system_config_category', 'category'),
        Index('idx_system_config_key', 'key')
    )


class AuditLog(Base):
    """
    Audit log table.
    
    Tracks all system changes and actions
    for security and debugging purposes.
    """
    __tablename__ = "audit_log"
    
    # Primary key
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event information
    event_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=True)
    
    # User information
    user_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changes = Column(JSON, nullable=True)
    
    # Additional context
    context = Column(JSON, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_log_timestamp', 'timestamp'),
        Index('idx_audit_log_event_type', 'event_type'),
        Index('idx_audit_log_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_log_user', 'user_id')
    )