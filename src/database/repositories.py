"""
Database repositories for XAUUSD Gold Trading System.

Provides high-level data access methods for all
database entities with proper error handling.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc, text
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Signal, Trade, PerformanceMetric, PriceHistory, SystemConfig, AuditLog
from ..models.signal import TradingSignal, SignalStatus, SessionType
from ..models.trade import Trade as TradeModel, TradeStatus, ExitReason


class BaseRepository:
    """Base repository with common functionality."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def _handle_error(self, error: Exception, operation: str):
        """Handle database errors with secure logging."""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database error during {operation}: {error}")
        # Don't expose sensitive error details to client
        raise Exception("Database operation failed")


class SignalRepository(BaseRepository):
    """Repository for trading signals."""
    
    def create_signal(self, signal: TradingSignal) -> Signal:
        """
        Create a new trading signal.
        
        Args:
            signal: Trading signal model
            
        Returns:
            Created Signal entity
        """
        try:
            db_signal = Signal(
                signal_id=signal.signal_id,
                instrument=signal.instrument,
                direction=signal.direction,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit_1=signal.take_profit_1,
                take_profit_2=signal.take_profit_2,
                risk_reward_ratio=signal.risk_reward_ratio,
                position_size=signal.position_size,
                risk_percentage=signal.risk_percentage,
                setup_type=signal.setup_type,
                market_structure=signal.market_structure,
                confluence_factors=signal.confluence_factors,
                confidence_score=signal.confidence_score,
                h4_context=signal.h4_context,
                h1_context=signal.h1_context,
                m15_context=signal.m15_context,
                session=signal.session.value,
                created_at=signal.created_at,
                updated_at=signal.updated_at,
                expires_at=signal.expires_at,
                status=signal.status.value,
                telegram_message_id=signal.telegram_message_id,
                notes=signal.notes
            )
            
            self.session.add(db_signal)
            self.session.commit()
            self.session.refresh(db_signal)
            return db_signal
            
        except Exception as e:
            self._handle_error(e, "create_signal")
    
    def get_signal_by_id(self, signal_id: str) -> Optional[Signal]:
        """
        Get signal by ID.
        
        Args:
            signal_id: Signal identifier
            
        Returns:
            Signal entity or None
        """
        try:
            stmt = select(Signal).where(Signal.signal_id == signal_id)
            result = self.session.execute(stmt).scalar_one_or_none()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_signal_by_id")
    
    def get_active_signals(self, instrument: Optional[str] = None, limit: int = 50) -> List[Signal]:
        """
        Get all active signals.
        
        Args:
            instrument: Filter by instrument
            limit: Maximum number of signals
            
        Returns:
            List of active signals
        """
        try:
            stmt = select(Signal).where(Signal.status == SignalStatus.ACTIVE.value)
            
            if instrument:
                stmt = stmt.where(Signal.instrument == instrument)
            
            stmt = stmt.order_by(desc(Signal.created_at)).limit(limit)
            result = self.session.execute(stmt).scalars().all()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_active_signals")
    
    def get_signals_by_date_range(self, start_date: datetime, end_date: datetime, 
                              instrument: Optional[str] = None) -> List[Signal]:
        """
        Get signals within date range.
        
        Args:
            start_date: Start date
            end_date: End date
            instrument: Filter by instrument
            
        Returns:
            List of signals
        """
        try:
            stmt = select(Signal).where(
                and_(
                    Signal.created_at >= start_date,
                    Signal.created_at <= end_date
                )
            )
            
            if instrument:
                stmt = stmt.where(Signal.instrument == instrument)
            
            stmt = stmt.order_by(desc(Signal.created_at))
            result = self.session.execute(stmt).scalars().all()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_signals_by_date_range")
    
    def update_signal_status(self, signal_id: str, status: SignalStatus) -> bool:
        """
        Update signal status.
        
        Args:
            signal_id: Signal identifier
            status: New status
            
        Returns:
            True if successful
        """
        try:
            stmt = update(Signal).where(Signal.signal_id == signal_id).values(
                status=status.value,
                updated_at=datetime.utcnow()
            )
            
            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            self._handle_error(e, "update_signal_status")
    
    def delete_signal(self, signal_id: str) -> bool:
        """
        Delete a signal.
        
        Args:
            signal_id: Signal identifier
            
        Returns:
            True if successful
        """
        try:
            stmt = delete(Signal).where(Signal.signal_id == signal_id)
            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            self._handle_error(e, "delete_signal")


class TradeRepository(BaseRepository):
    """Repository for trades."""
    
    def create_trade(self, trade: TradeModel) -> Trade:
        """
        Create a new trade.
        
        Args:
            trade: Trade model
            
        Returns:
            Created Trade entity
        """
        try:
            db_trade = Trade(
                signal_id=trade.signal_id,
                instrument=trade.instrument,
                direction=trade.direction,
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                highest_price=trade.highest_price,
                lowest_price=trade.lowest_price,
                profit_loss=trade.profit_loss,
                profit_loss_pips=trade.profit_loss_pips,
                profit_loss_percentage=trade.profit_loss_percentage,
                position_size=trade.position_size,
                status=trade.status.value,
                partial_closes=trade.partial_closes_json,
                tp1_hit=trade.tp1_hit,
                tp2_hit=trade.tp2_hit,
                sl_hit=trade.sl_hit,
                breakeven_moved=trade.breakeven_moved,
                exit_reason=trade.exit_reason.value if trade.exit_reason else None,
                notes=trade.notes
            )
            
            self.session.add(db_trade)
            self.session.commit()
            self.session.refresh(db_trade)
            return db_trade
            
        except Exception as e:
            self._handle_error(e, "create_trade")
    
    def get_trade_by_id(self, trade_id: int) -> Optional[Trade]:
        """
        Get trade by ID.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            Trade entity or None
        """
        try:
            stmt = select(Trade).where(Trade.trade_id == trade_id)
            result = self.session.execute(stmt).scalar_one_or_none()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_trade_by_id")
    
    def get_active_trades(self, instrument: Optional[str] = None) -> List[Trade]:
        """
        Get all active trades.
        
        Args:
            instrument: Filter by instrument
            
        Returns:
            List of active trades
        """
        try:
            stmt = select(Trade).where(Trade.status == TradeStatus.OPEN.value)
            
            if instrument:
                stmt = stmt.where(Trade.instrument == instrument)
            
            stmt = stmt.order_by(desc(Trade.entry_time))
            result = self.session.execute(stmt).scalars().all()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_active_trades")
    
    def update_trade_price(self, trade_id: int, current_price: Decimal) -> bool:
        """
        Update trade current price.
        
        Args:
            trade_id: Trade identifier
            current_price: New current price
            
        Returns:
            True if successful
        """
        try:
            stmt = update(Trade).where(Trade.trade_id == trade_id).values(
                current_price=current_price,
                updated_at=datetime.utcnow()
            )
            
            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            self._handle_error(e, "update_trade_price")
    
    def close_trade(self, trade_id: int, exit_price: Decimal, 
                 exit_time: datetime, exit_reason: ExitReason) -> bool:
        """
        Close a trade.
        
        Args:
            trade_id: Trade identifier
            exit_price: Exit price
            exit_time: Exit time
            exit_reason: Exit reason
            
        Returns:
            True if successful
        """
        try:
            stmt = update(Trade).where(Trade.trade_id == trade_id).values(
                exit_price=exit_price,
                exit_time=exit_time,
                status=TradeStatus.CLOSED.value,
                exit_reason=exit_reason.value,
                updated_at=datetime.utcnow()
            )
            
            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            self._handle_error(e, "close_trade")


class PerformanceRepository(BaseRepository):
    """Repository for performance metrics."""
    
    def create_daily_metrics(self, instrument: str, metric_date: date, 
                          metrics_data: Dict[str, Any]) -> PerformanceMetric:
        """
        Create daily performance metrics.
        
        Args:
            instrument: Trading instrument
            metric_date: Date for metrics
            metrics_data: Dictionary with metrics
            
        Returns:
            Created PerformanceMetric entity
        """
        try:
            db_metric = PerformanceMetric(
                instrument=instrument,
                metric_date=metric_date,
                total_signals=metrics_data.get('total_signals', 0),
                total_trades=metrics_data.get('total_trades', 0),
                winning_trades=metrics_data.get('winning_trades', 0),
                losing_trades=metrics_data.get('losing_trades', 0),
                win_rate=metrics_data.get('win_rate'),
                average_rr=metrics_data.get('average_rr'),
                total_pips=metrics_data.get('total_pips'),
                total_profit_loss=metrics_data.get('total_profit_loss'),
                calculated_at=datetime.utcnow()
            )
            
            self.session.add(db_metric)
            self.session.commit()
            self.session.refresh(db_metric)
            return db_metric
            
        except Exception as e:
            self._handle_error(e, "create_daily_metrics")
    
    def get_metrics_by_date_range(self, start_date: date, end_date: date,
                                instrument: Optional[str] = None) -> List[PerformanceMetric]:
        """
        Get metrics within date range.
        
        Args:
            start_date: Start date
            end_date: End date
            instrument: Filter by instrument
            
        Returns:
            List of performance metrics
        """
        try:
            stmt = select(PerformanceMetric).where(
                and_(
                    PerformanceMetric.metric_date >= start_date,
                    PerformanceMetric.metric_date <= end_date
                )
            )
            
            if instrument:
                stmt = stmt.where(PerformanceMetric.instrument == instrument)
            
            stmt = stmt.order_by(desc(PerformanceMetric.metric_date))
            result = self.session.execute(stmt).scalars().all()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_metrics_by_date_range")
    
    def get_latest_metrics(self, instrument: str, days: int = 30) -> List[PerformanceMetric]:
        """
        Get latest metrics for instrument.
        
        Args:
            instrument: Trading instrument
            days: Number of days to get
            
        Returns:
            List of recent performance metrics
        """
        try:
            stmt = select(PerformanceMetric).where(
                and_(
                    PerformanceMetric.instrument == instrument,
                    PerformanceMetric.metric_date >= date.today() - datetime.timedelta(days=days)
                )
            ).order_by(desc(PerformanceMetric.metric_date))
            
            result = self.session.execute(stmt).scalars().all()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_latest_metrics")


class ConfigRepository(BaseRepository):
    """Repository for system configuration."""
    
    def get_config_value(self, key: str) -> Optional[str]:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value or None
        """
        try:
            # Use parameterized query to prevent SQL injection
            stmt = select(SystemConfig).where(SystemConfig.key == key)
            result = self.session.execute(stmt).scalar_one_or_none()
            return result.value if result else None
            
        except Exception as e:
            self._handle_error(e, "get_config_value")
    
    def set_config_value(self, key: str, value: str, category: str = "general",
                        description: Optional[str] = None, updated_by: Optional[str] = None) -> bool:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            category: Configuration category
            description: Configuration description
            updated_by: User who updated
            
        Returns:
            True if successful
        """
        try:
            # Check if config exists
            existing = self.get_config_value(key)
            
            if existing:
                # Use parameterized update to prevent SQL injection
                stmt = update(SystemConfig).where(SystemConfig.key == key).values(
                    value=value,
                    updated_at=datetime.utcnow(),
                    updated_by=updated_by
                )
            else:
                # Use parameterized insert to prevent SQL injection
                stmt = update(SystemConfig).values(
                    key=key,
                    value=value,
                    category=category,
                    description=description,
                    data_type="string",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    updated_by=updated_by
                )
            
            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            self._handle_error(e, "set_config_value")
    
    def get_all_configs(self, category: Optional[str] = None) -> List[SystemConfig]:
        """
        Get all configuration values.
        
        Args:
            category: Filter by category
            
        Returns:
            List of configuration entries
        """
        try:
            stmt = select(SystemConfig)
            
            if category:
                stmt = stmt.where(SystemConfig.category == category)
            
            stmt = stmt.order_by(asc(SystemConfig.category), asc(SystemConfig.key))
            result = self.session.execute(stmt).scalars().all()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_all_configs")


class PriceHistoryRepository(BaseRepository):
    """Repository for price history data."""
    
    def save_candles(self, candles: List[Dict[str, Any]]) -> bool:
        """
        Save candle data.
        
        Args:
            candles: List of candle data
            
        Returns:
            True if successful
        """
        try:
            # Validate input data to prevent injection
            for candle in candles:
                # Sanitize and validate each field
                instrument = str(candle.get('instrument', '')).strip()[:20]
                timeframe = str(candle.get('timeframe', '')).strip()[:10]
                
                # Validate instrument and timeframe against allowed values
                if not instrument or not timeframe:
                    continue
                
                db_candle = PriceHistory(
                    instrument=instrument,
                    timeframe=timeframe,
                    timestamp=candle['timestamp'],
                    open_price=Decimal(str(candle['open'])),
                    high_price=Decimal(str(candle['high'])),
                    low_price=Decimal(str(candle['low'])),
                    close_price=Decimal(str(candle['close'])),
                    volume=int(candle.get('volume', 0)),
                    tick_volume=int(candle.get('tick_volume', 0)),
                    spread=int(candle.get('spread', 0))
                )
                self.session.add(db_candle)
            
            self.session.commit()
            return True
            
        except Exception as e:
            self._handle_error(e, "save_candles")
    
    def get_candles_by_timeframe(self, instrument: str, timeframe: str,
                                start_time: datetime, end_time: datetime,
                                limit: int = 1000) -> List[PriceHistory]:
        """
        Get candles by timeframe.
        
        Args:
            instrument: Trading instrument
            timeframe: Candle timeframe
            start_time: Start time
            end_time: End time
            limit: Maximum candles to return
            
        Returns:
            List of price history
        """
        try:
            # Validate inputs to prevent SQL injection
            instrument = str(instrument).strip()[:20]
            timeframe = str(timeframe).strip()[:10]
            
            # Use parameterized query with validated inputs
            stmt = select(PriceHistory).where(
                and_(
                    PriceHistory.instrument == instrument,
                    PriceHistory.timeframe == timeframe,
                    PriceHistory.timestamp >= start_time,
                    PriceHistory.timestamp <= end_time
                )
            ).order_by(desc(PriceHistory.timestamp)).limit(limit)
            
            result = self.session.execute(stmt).scalars().all()
            return result
            
        except Exception as e:
            self._handle_error(e, "get_candles_by_timeframe")