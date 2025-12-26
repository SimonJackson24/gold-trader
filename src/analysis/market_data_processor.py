"""
Market data processor for XAUUSD Gold Trading System.

Processes real-time tick data, maintains candle windows,
and triggers SMC analysis on new candle closes.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from collections import deque
import logging

from ..models.candle import Candle
from ..models.market_data import Tick, MarketSnapshot
from ..models.signal import TradingSignal
from .confluence_analyzer import ConfluenceAnalyzer
from ..config import get_settings


class RollingWindow:
    """Rolling window for candle data."""

    def __init__(self, size: int):
        """
        Initialize rolling window.

        Args:
            size: Window size
        """
        self.size = size
        self.data = deque(maxlen=size)
        self.is_full = False

    def add(self, candle: Candle):
        """
        Add candle to rolling window.

        Args:
            candle: Candle to add
        """
        self.data.append(candle)
        if len(self.data) >= self.size:
            self.is_full = True
        else:
            self.is_full = False

    def get_latest(self, count: int = 1) -> List[Candle]:
        """
        Get latest candles from window.

        Args:
            count: Number of candles to get

        Returns:
            List of latest candles
        """
        return list(self.data)[-count:] if self.data else []


class MarketDataProcessor:
    """
    Market data processor implementation.

    Handles real-time tick processing, candle aggregation,
    and SMC analysis triggering.
    """

    def __init__(self):
        """Initialize market data processor."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

        # Initialize rolling windows for different timeframes
        self.m15_window = RollingWindow(size=200)
        self.h1_window = RollingWindow(size=200)
        self.h4_window = RollingWindow(size=200)

        # Current candles
        self.current_m15 = None
        self.current_h1 = None
        self.current_h4 = None

        # Tick processing
        self.pending_ticks = deque(maxlen=1000)
        self.current_tick = None
        self.last_tick_time = None

        # SMC analyzer
        self.confluence_analyzer = ConfluenceAnalyzer()

        # Event callbacks
        self.on_new_candle_callbacks: List[Callable[[Candle], None]] = []
        self.on_signal_callbacks: List[Callable[[TradingSignal], None]] = []
        self.on_trade_update_callbacks: List[Callable[[Dict], None]] = []

        # Processing state
        self.is_running = False
        self.processed_ticks = 0

        # Initialize last update time
        self.last_m15_update = datetime.utcnow()
        self.last_h1_update = datetime.utcnow()
        self.last_h4_update = datetime.utcnow()

    def add_new_candle_callback(self, callback: Callable[[Candle], None]):
        """
        Add callback for new candle events.

        Args:
            callback: Callback function
        """
        self.on_new_candle_callbacks.append(callback)

    def add_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """
        Add callback for signal generation events.

        Args:
            callback: Callback function
        """
        self.on_signal_callbacks.append(callback)

    def add_trade_update_callback(self, callback: Callable[[Dict], None]):
        """
        Add callback for trade update events.

        Args:
            callback: Callback function
        """
        self.on_trade_update_callbacks.append(callback)

    async def start(self):
        """Start market data processing."""
        self.is_running = True
        self.logger.info("Market data processor started")

    async def stop(self):
        """Stop market data processing."""
        self.is_running = False
        self.logger.info("Market data processor stopped")

    async def process_tick(self, tick: Tick):
        """
        Process incoming tick data.

        Args:
            tick: New tick data
        """
        if not self.is_running:
            return

        self.current_tick = tick
        self.last_tick_time = tick.timestamp
        self.processed_ticks += 1

        # Add to pending ticks for processing
        self.pending_ticks.append(tick)

        # Process tick batch if window is full
        if len(self.pending_ticks) >= 10:
            await self._process_tick_batch()

    async def _process_tick_batch(self):
        """
        Process batch of pending ticks.
        """
        if not self.pending_ticks:
            return

        # Get ticks to process
        ticks_to_process = list(self.pending_ticks)
        self.pending_ticks.clear()

        # Group ticks by symbol
        symbol_ticks = {}
        for tick in ticks_to_process:
            if tick.symbol not in symbol_ticks:
                symbol_ticks[tick.symbol] = []
            symbol_ticks[tick.symbol].append(tick)

        # Process each symbol
        for symbol, ticks in symbol_ticks.items():
            await self._process_symbol_ticks(symbol, ticks)

    async def _process_symbol_ticks(self, symbol: str, ticks: List[Tick]):
        """
        Process ticks for a specific symbol.

        Args:
            symbol: Trading symbol
            ticks: List of ticks to process
        """
        if not ticks:
            return

        # Sort ticks by timestamp
        ticks.sort(key=lambda t: t.timestamp)

        # Process ticks to update candles
        for tick in ticks:
            await self._update_candles_from_tick(tick)

        # Trigger analysis on new candle closes
        await self._check_and_trigger_analysis()

    async def _update_candles_from_tick(self, tick: Tick):
        """
        Update candle windows from tick data.

        Args:
            tick: Current tick data
        """
        timestamp = tick.timestamp

        # Update M15 candles (1-minute aggregation)
        new_m15 = await self._update_timeframe_candle(
            self.m15_window, tick, self.current_m15, timedelta(minutes=1)
        )
        if new_m15:
            self.current_m15 = new_m15
            self.last_m15_update = timestamp

            # Trigger callbacks
            for callback in self.on_new_candle_callbacks:
                try:
                    await callback(new_m15)
                except Exception as e:
                    self.logger.error(f"Error in new M15 candle callback: {e}")

        # Update H1 candles (1-hour aggregation)
        new_h1 = await self._update_timeframe_candle(
            self.h1_window, tick, self.current_h1, timedelta(hours=1)
        )
        if new_h1:
            self.current_h1 = new_h1
            self.last_h1_update = timestamp

        # Update H4 candles (4-hour aggregation)
        new_h4 = await self._update_timeframe_candle(
            self.h4_window, tick, self.current_h4, timedelta(hours=4)
        )
        if new_h4:
            self.current_h4 = new_h4
            self.last_h4_update = timestamp

    async def _update_timeframe_candle(
        self,
        window: RollingWindow,
        tick: Tick,
        current_candle: Optional[Candle],
        period: timedelta,
    ) -> Optional[Candle]:
        """
        Update candle for specific timeframe.

        Args:
            window: Rolling window for timeframe
            tick: Current tick data
            current_candle: Current candle for timeframe
            period: Time period for candle

        Returns:
            Updated candle or None
        """
        # Get OHLC from tick
        ohlc = {
            "open": tick.bid,
            "high": tick.bid,
            "low": tick.bid,
            "close": tick.bid,
            "volume": tick.volume,
        }

        # If no current candle, create new one
        if not current_candle:
            candle = Candle(
                timestamp=tick.timestamp,
                open=ohlc["open"],
                high=ohlc["high"],
                low=ohlc["low"],
                close=ohlc["close"],
                volume=ohlc["volume"],
                instrument=tick.symbol,
                timeframe=self._get_timeframe_from_period(period),
            )
            window.add(candle)
            return candle

        # Update existing candle
        candle = current_candle
        candle.high = max(candle.high, tick.bid)
        candle.low = min(candle.low, tick.bid)
        candle.volume = (candle.volume or 0) + (tick.volume or 0)
        candle.close = tick.bid

        # Check if candle period is complete
        if tick.timestamp >= candle.timestamp + period:
            # Add to window and create new candle
            window.add(candle)
            new_candle = Candle(
                timestamp=candle.timestamp + period,
                open=ohlc["close"],
                high=ohlc["high"],
                low=ohlc["low"],
                close=ohlc["close"],
                volume=0,  # Will be updated with ticks
                instrument=tick.symbol,
                timeframe=self._get_timeframe_from_period(period),
            )
            return new_candle

        return None

    def _get_timeframe_from_period(self, period: timedelta) -> str:
        """
        Get timeframe string from period.

        Args:
            period: Time period

        Returns:
            Timeframe string
        """
        total_minutes = period.total_seconds() / 60

        if total_minutes < 30:
            return "M15"
        elif total_minutes < 240:
            return "H1"
        elif total_minutes < 1440:
            return "H4"
        else:
            return "D1"

    async def _check_and_trigger_analysis(self):
        """
        Check for new candles and trigger SMC analysis.
        """
        current_time = datetime.utcnow()

        # Check M15 timeframe
        if self.last_m15_update and current_time >= self.last_m15_update + timedelta(
            minutes=1
        ):
            await self._trigger_smc_analysis("M15")

        # Check H1 timeframe
        if self.last_h1_update and current_time >= self.last_h1_update + timedelta(
            hours=1
        ):
            await self._trigger_smc_analysis("H1")

        # Check H4 timeframe
        if self.last_h4_update and current_time >= self.last_h4_update + timedelta(
            hours=4
        ):
            await self._trigger_smc_analysis("H4")

    async def _trigger_smc_analysis(self, timeframe: str):
        """
        Trigger SMC analysis for specific timeframe.

        Args:
            timeframe: Timeframe that triggered analysis
        """
        try:
            # Get candles for analysis
            if timeframe == "M15":
                candles = self.m15_window.get_latest(50)
                current_candle = self.current_m15
            elif timeframe == "H1":
                candles = self.h1_window.get_latest(50)
                current_candle = self.current_h1
            elif timeframe == "H4":
                candles = self.h4_window.get_latest(50)
                current_candle = self.current_h4
            else:
                self.logger.warning(f"Unknown timeframe for analysis: {timeframe}")
                return

            if not candles or len(candles) < 20:
                self.logger.warning(f"Insufficient candles for {timeframe} analysis")
                return

            # Get current price
            current_price = self.current_tick.mid_price if self.current_tick else None

            # Perform confluence analysis
            analysis = self.confluence_analyzer.analyze_confluence(
                h4_candles=candles,
                h1_candles=candles,
                m15_candles=candles,
                current_price=current_price,
            )

            # Check if signal should be generated
            if analysis.meets_threshold(self.settings.smc.confluence_threshold):
                # Generate trading signal
                signal = await self._generate_signal(analysis, current_price)

                if signal:
                    self.logger.info(
                        f"Signal generated: {signal.signal_id} - "
                        f"{signal.direction} {signal.instrument} at {signal.entry_price}"
                    )

                    # Trigger signal callbacks
                    for callback in self.on_signal_callbacks:
                        try:
                            await callback(signal)
                        except Exception as e:
                            self.logger.error(f"Error in signal callback: {e}")
            else:
                self.logger.debug(
                    f"Analysis completed for {timeframe} - "
                    f"Score: {analysis.overall_score:.2f}%"
                )

        except Exception as e:
            self.logger.error(f"Error in SMC analysis for {timeframe}: {e}")

    async def _generate_signal(
        self, analysis, current_price: Decimal
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal from analysis.

        Args:
            analysis: Confluence analysis results
            current_price: Current market price

        Returns:
            Trading signal or None
        """
        # Import here to avoid circular import
        from ..trading.signal_generator import SignalGenerator

        generator = SignalGenerator()
        return await generator.generate_signal(analysis, current_price)

    def get_status(self) -> Dict[str, Any]:
        """
        Get processor status information.

        Returns:
            Status dictionary
        """
        return {
            "is_running": self.is_running,
            "processed_ticks": self.processed_ticks,
            "m15_window_size": len(self.m15_window.data),
            "h1_window_size": len(self.h1_window.data),
            "h4_window_size": len(self.h4_window.data),
            "last_m15_update": self.last_m15_update.isoformat()
            if self.last_m15_update
            else None,
            "last_h1_update": self.last_h1_update.isoformat()
            if self.last_h1_update
            else None,
            "last_h4_update": self.last_h4_update.isoformat()
            if self.last_h4_update
            else None,
            "current_tick": self.current_tick.to_dict() if self.current_tick else None,
            "current_m15": self.current_m15.to_dict() if self.current_m15 else None,
            "current_h1": self.current_h1.to_dict() if self.current_h1 else None,
            "current_h4": self.current_h4.to_dict() if self.current_h4 else None,
        }
