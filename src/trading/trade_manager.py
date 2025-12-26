"""
Trade manager for XAUUSD Gold Trading System.

Manages active trades, monitors price movements,
and handles partial closes and stop loss management.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from ..models.trade import Trade, TradeStatus, ExitReason, PartialClose
from ..models.signal import TradingSignal
from ..database.repositories import TradeRepository
from ..config import get_settings
from ..core import trade_locks, trade_semaphore, signal_queue


class TradeManager:
    """
    Trade manager implementation.

    Handles trade lifecycle management including
    opening, monitoring, and closing trades.
    """

    def __init__(self, session=None):
        """Initialize trade manager."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.trade_repo = TradeRepository(session) if session else None

        # Handlers
        self.trade_handlers: List[Callable] = []

        # Thread-safe active trades
        self.active_trades = trade_locks  # Use resource manager for trades

        # Processing state
        self.is_running = False
        self.last_price_check = datetime.utcnow()

        # Synchronization locks
        self._trade_lock = trade_locks
        self._trade_semaphore = trade_semaphore

    def add_trade_handler(self, handler: Callable):
        """Add handler for trade events."""
        self.trade_handlers.append(handler)

    async def start(self):
        """Start trade management."""
        self.is_running = True
        self.logger.info("Trade manager started")

    async def stop(self):
        """Stop trade management."""
        self.is_running = False
        self.logger.info("Trade manager stopped")

    async def open_trade(self, signal: TradingSignal) -> Optional[Trade]:
        """
        Open a new trade from signal.

        Args:
            signal: Trading signal to execute

        Returns:
            Created trade or None
        """
        try:
            # Use semaphore to limit concurrent trade operations
            async with self._trade_semaphore.acquire(timeout=10.0):
                # Check if we can open new trade
                if not await self._can_open_trade():
                    self.logger.warning("Cannot open new trade - limits reached")
                    return None

                # Acquire exclusive lock for trade creation
                lock_acquired = await self._trade_lock.acquire_resource(
                    f"trade_{signal.signal_id}",
                    "exclusive",
                    "trade_manager",
                    timeout=5.0,
                )

                if not lock_acquired:
                    self.logger.warning(
                        f"Failed to acquire lock for trade {signal.signal_id}"
                    )
                    return None

                try:
                    # Create trade
                    trade = Trade(
                        signal_id=signal.signal_id,
                        instrument=signal.instrument,
                        direction=signal.direction,
                        entry_time=datetime.utcnow(),
                        entry_price=signal.entry_price,
                        stop_loss=signal.stop_loss,
                        take_profit_1=signal.take_profit_1,
                        take_profit_2=signal.take_profit_2,
                        position_size=signal.position_size,
                        status=TradeStatus.PENDING,
                    )

                    # Save to database
                    db_trade = await self.trade_repo.create_trade(trade)

                    # Update signal status
                    signal.update_status(SignalStatus.FILLED)

                    self.logger.info(
                        f"Trade opened: {db_trade.trade_id} for signal {signal.signal_id}"
                    )

                    # Trigger handlers
                    for handler in self.trade_handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(db_trade)
                            else:
                                handler(db_trade)
                        except Exception as e:
                            self.logger.error(f"Error in trade handler: {e}")

                    return db_trade

                finally:
                    # Always release the lock
                    await self._trade_lock.release_resource(
                        f"trade_{signal.signal_id}", "trade_manager"
                    )

        except Exception as e:
            self.logger.error(f"Error opening trade: {e}")
            return None

    async def _can_open_trade(self) -> bool:
        """
        Check if new trade can be opened with thread-safe checks.

        Returns:
            True if trade can be opened
        """
        # Get locked resources to check concurrent trades
        locked_resources = self._trade_lock.get_locked_resources()

        # Count active trades from locks
        active_count = len(
            [
                resource_id
                for resource_id in locked_resources.keys()
                if resource_id.startswith("trade_")
            ]
        )

        if active_count >= self.settings.trading.max_concurrent_trades:
            return False

        # Check trading hours
        current_hour = datetime.utcnow().hour
        if not self.settings.trading.can_trade_now(current_hour):
            return False

        return True

    async def monitor_trades(self):
        """
        Monitor all active trades with thread-safe price updates.
        """
        if not self.is_running:
            return

        # Check if we need to update prices
        current_time = datetime.utcnow()
        if (current_time - self.last_price_check).total_seconds() < 30:
            return

        self.last_price_check = current_time

        # Get current price (would come from market data processor)
        current_price = await self._get_current_price()

        if not current_price:
            return

        # Get all locked trade resources
        locked_resources = self._trade_lock.get_locked_resources()

        # Update each active trade with proper locking
        for resource_id, resource_locks in locked_resources.items():
            if resource_id.startswith("trade_"):
                try:
                    # Acquire read lock for trade update
                    lock_acquired = await self._trade_lock.acquire_resource(
                        resource_id, "read", "monitor", timeout=1.0
                    )

                    if lock_acquired:
                        try:
                            trade_id = int(resource_id.split("_")[1])
                            await self._update_trade_price(trade_id, current_price)
                        finally:
                            await self._trade_lock.release_resource(
                                resource_id, "monitor"
                            )

                except Exception as e:
                    self.logger.error(f"Error monitoring trade {resource_id}: {e}")

    async def _update_trade_price(self, trade_id: int, current_price: Decimal):
        """
        Update trade price and check for exit conditions with proper locking.

        Args:
            trade_id: Trade identifier
            current_price: New current price
        """
        resource_id = f"trade_{trade_id}"

        try:
            # Acquire write lock for trade update
            lock_acquired = await self._trade_lock.acquire_resource(
                resource_id, "write", "price_updater", timeout=2.0
            )

            if not lock_acquired:
                self.logger.warning(
                    f"Failed to acquire lock for trade {trade_id} price update"
                )
                return

            try:
                # Update price in database
                await self.trade_repo.update_trade_price(trade_id, current_price)

                # Check for exit conditions
                await self._check_trade_exit(trade_id, current_price)

            finally:
                await self._trade_lock.release_resource(resource_id, "price_updater")

        except Exception as e:
            self.logger.error(f"Error updating trade {trade_id}: {e}")

    async def _check_trade_exit(self, trade_id: int, current_price: Decimal):
        """
        Check if trade should be closed with proper locking.

        Args:
            trade_id: Trade identifier
            current_price: Current market price
        """
        resource_id = f"trade_{trade_id}"

        try:
            # Acquire exclusive lock for trade exit check
            lock_acquired = await self._trade_lock.acquire_resource(
                resource_id, "exclusive", "exit_checker", timeout=2.0
            )

            if not lock_acquired:
                return

            try:
                # Get trade from database (fresh data)
                trade = await self.trade_repo.get_trade_by_id(trade_id)
                if not trade:
                    return

                # Check stop loss
                if trade.is_price_at_risk_level(current_price):
                    await self._close_trade(trade_id, current_price, ExitReason.SL_HIT)
                    return

                # Check take profit 1
                if not trade.tp1_hit and trade.is_price_at_risk_reward_level(
                    current_price, trade.take_profit_1, 0.5
                ):
                    await self._partial_close_trade(
                        trade_id, trade.take_profit_1, 0.5, "TP1_HIT"
                    )
                    return

                # Check take profit 2
                if not trade.tp2_hit and trade.is_price_at_risk_reward_level(
                    current_price, trade.take_profit_2, 1.0
                ):
                    await self._close_trade(trade_id, current_price, ExitReason.TP2_HIT)
                    return

                # Move stop to breakeven if configured
                if (
                    not trade.breakeven_moved
                    and self.settings.trading.move_to_breakeven_pips > 0
                ):
                    move_to_be_pips = (
                        self.settings.trading.move_to_breakeven_pips / 10000
                    )

                    if trade.is_buy and current_price >= (
                        trade.entry_price + move_to_be_pips
                    ):
                        await self.trade_repo.update_trade_price(
                            trade_id, trade.entry_price
                        )
                        trade.move_stop_to_breakeven()
                        self.logger.info(f"Trade {trade_id} moved to breakeven")
                    elif trade.is_sell and current_price <= (
                        trade.entry_price - move_to_be_pips
                    ):
                        await self.trade_repo.update_trade_price(
                            trade_id, trade.entry_price
                        )
                        trade.move_stop_to_breakeven()
                        self.logger.info(f"Trade {trade_id} moved to breakeven")

            finally:
                await self._trade_lock.release_resource(resource_id, "exit_checker")

        except Exception as e:
            self.logger.error(f"Error checking trade exit {trade_id}: {e}")

    async def _partial_close_trade(
        self, trade: Trade, close_price: Decimal, percentage: float, reason: str
    ):
        """
        Execute partial trade close.

        Args:
            trade: Trade to close partially
            close_price: Close price
            percentage: Percentage to close (0.0 to 1.0)
            reason: Reason for close
        """
        try:
            # Calculate partial close size
            close_size = trade.calculate_partial_close_size(percentage)

            # Calculate profit
            if trade.is_buy:
                profit_pips = close_price - trade.entry_price
            else:
                profit_pips = trade.entry_price - close_price

            profit = profit_pips * close_size * Decimal("10")  # $10 per pip

            # Create partial close record
            partial_close = PartialClose(
                time=datetime.utcnow(),
                price=close_price,
                size=close_size,
                profit=profit,
                reason=reason,
            )

            # Update trade
            trade.partial_closes.append(partial_close)

            # Update TP flags
            if reason == "TP1_HIT":
                trade.tp1_hit = True
            elif reason == "TP2_HIT":
                trade.tp2_hit = True

            # Update remaining position size
            trade.position_size = trade.remaining_position_size

            # Save to database
            await self.trade_repo.close_trade(
                trade.trade_id, close_price, datetime.utcnow(), reason
            )

            self.logger.info(
                f"Partial close: {close_size} at {close_price} for reason {reason}"
            )

        except Exception as e:
            self.logger.error(f"Error in partial close: {e}")

    async def _close_trade(
        self,
        trade: Trade,
        close_price: Decimal,
        close_time: datetime,
        reason: ExitReason,
    ):
        """
        Close trade completely.

        Args:
            trade: Trade to close
            close_price: Close price
            close_time: Close time
            reason: Exit reason
        """
        try:
            # Calculate final profit
            if trade.is_buy:
                profit_pips = close_price - trade.entry_price
            else:
                profit_pips = trade.entry_price - close_price

            profit = profit_pips * trade.position_size * Decimal("10")  # $10 per pip

            # Update trade
            trade.exit_price = close_price
            trade.exit_time = close_time
            trade.status = TradeStatus.CLOSED
            trade.exit_reason = reason
            trade.profit_loss = profit

            # Save to database
            await self.trade_repo.close_trade(
                trade.trade_id, close_price, close_time, reason
            )

            # Remove from active trades
            if trade.signal_id in self.active_trades:
                del self.active_trades[trade.signal_id]

            self.logger.info(f"Trade closed: {trade.trade_id} with P/L {profit}")

        except Exception as e:
            self.logger.error(f"Error closing trade: {e}")

    async def _get_current_price(self) -> Optional[Decimal]:
        """
        Get current market price.

        Returns:
            Current price or None
        """
        # This would connect to market data processor
        # For now, return None
        # In a real implementation, this would:
        # return await self.market_data_processor.get_current_price()
        return None

    async def get_active_trades(self) -> List[Trade]:
        """
        Get all active trades with thread-safe access.

        Returns:
            List of active trades
        """
        try:
            # Use database to get active trades (thread-safe)
            return await self.trade_repo.get_active_trades()
        except Exception as e:
            self.logger.error(f"Error getting active trades: {e}")
            return []

    async def get_trade_by_id(self, trade_id: int) -> Optional[Trade]:
        """
        Get trade by ID with thread-safe access.

        Args:
            trade_id: Trade identifier

        Returns:
            Trade or None
        """
        try:
            # Use database for thread-safe access
            return await self.trade_repo.get_trade_by_id(trade_id)
        except Exception as e:
            self.logger.error(f"Error getting trade {trade_id}: {e}")
            return None

    async def close_trade_manually(
        self, trade_id: int, reason: str = "MANUAL_CLOSE"
    ) -> bool:
        """
        Manually close a trade.

        Args:
            trade_id: Trade identifier
            reason: Close reason

        Returns:
            True if successful
        """
        trade = self.active_trades.get(str(trade_id))
        if not trade:
            self.logger.error(f"Trade {trade_id} not found")
            return False

        current_price = await self._get_current_price()
        if not current_price:
            self.logger.error("Cannot close trade - no current price available")
            return False

        await self._close_trade(
            trade, current_price, datetime.utcnow(), ExitReason(reason)
        )
        return True

    async def get_trade_status(self) -> Dict[str, Any]:
        """
        Get trade manager status.

        Returns:
            Status dictionary
        """
        return {
            "is_running": self.is_running,
            "active_trades": len(self.active_trades),
            "last_price_check": self.last_price_check.isoformat(),
            "active_trade_ids": list(self.active_trades.keys()),
        }
