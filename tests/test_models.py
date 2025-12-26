"""
Unit tests for data models.

Tests all model classes including validation,
serialization, and business logic.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.models.signal import Signal
from src.models.trade import Trade
from src.models.market_data import Tick, Candle


class TestSignal:
    """Test Signal model."""

    def test_signal_creation(self, sample_signal):
        """Test signal creation."""
        assert sample_signal.symbol == "XAUUSD"
        assert sample_signal.signal_type == "BUY"
        assert sample_signal.entry_price == Decimal("1950.50")
        assert sample_signal.stop_loss == Decimal("1948.00")
        assert sample_signal.take_profit == Decimal("1955.00")
        assert sample_signal.confidence == 0.85
        assert (
            sample_signal.reasoning
            == "Smart Money Concepts analysis indicates bullish bias"
        )
        assert isinstance(sample_signal.timestamp, datetime)

    def test_signal_validation(self):
        """Test signal validation."""
        # Valid signal
        signal = Signal(
            symbol="XAUUSD",
            signal_type="BUY",
            entry_price=Decimal("1950.50"),
            stop_loss=Decimal("1948.00"),
            take_profit=Decimal("1955.00"),
            confidence=0.85,
            reasoning="Test signal",
            timestamp=datetime.utcnow(),
        )
        assert signal.is_valid()

        # Invalid signal type
        invalid_signal = Signal(
            symbol="XAUUSD",
            signal_type="INVALID",
            entry_price=Decimal("1950.50"),
            stop_loss=Decimal("1948.00"),
            take_profit=Decimal("1955.00"),
            confidence=0.85,
            reasoning="Test signal",
            timestamp=datetime.utcnow(),
        )
        assert not invalid_signal.is_valid()

        # Invalid confidence
        invalid_signal = Signal(
            symbol="XAUUSD",
            signal_type="BUY",
            entry_price=Decimal("1950.50"),
            stop_loss=Decimal("1948.00"),
            take_profit=Decimal("1955.00"),
            confidence=1.5,  # Invalid: > 1.0
            reasoning="Test signal",
            timestamp=datetime.utcnow(),
        )
        assert not invalid_signal.is_valid()

    def test_signal_risk_reward(self, sample_signal):
        """Test risk/reward calculation."""
        risk_reward = sample_signal.calculate_risk_reward()

        # Risk = entry_price - stop_loss = 1950.50 - 1948.00 = 2.50
        # Reward = take_profit - entry_price = 1955.00 - 1950.50 = 4.50
        # Risk/Reward = 4.50 / 2.50 = 1.8

        assert abs(risk_reward - 1.8) < 0.01

    def test_signal_to_dict(self, sample_signal):
        """Test signal serialization."""
        signal_dict = sample_signal.to_dict()

        assert signal_dict["symbol"] == "XAUUSD"
        assert signal_dict["signal_type"] == "BUY"
        assert signal_dict["entry_price"] == "1950.50"
        assert signal_dict["stop_loss"] == "1948.00"
        assert signal_dict["take_profit"] == "1955.00"
        assert signal_dict["confidence"] == 0.85
        assert "timestamp" in signal_dict

    def test_signal_from_dict(self):
        """Test signal deserialization."""
        signal_data = {
            "symbol": "XAUUSD",
            "signal_type": "SELL",
            "entry_price": "1950.50",
            "stop_loss": "1952.00",
            "take_profit": "1948.00",
            "confidence": 0.75,
            "reasoning": "Test sell signal",
            "timestamp": datetime.utcnow().isoformat(),
        }

        signal = Signal.from_dict(signal_data)

        assert signal.symbol == "XAUUSD"
        assert signal.signal_type == "SELL"
        assert signal.entry_price == Decimal("1950.50")
        assert signal.stop_loss == Decimal("1952.00")
        assert signal.take_profit == Decimal("1948.00")
        assert signal.confidence == 0.75


class TestTrade:
    """Test Trade model."""

    def test_trade_creation(self, sample_trade):
        """Test trade creation."""
        assert sample_trade.symbol == "XAUUSD"
        assert sample_trade.trade_type == "BUY"
        assert sample_trade.volume == Decimal("0.1")
        assert sample_trade.price == Decimal("1950.50")
        assert sample_trade.stop_loss == Decimal("1948.00")
        assert sample_trade.take_profit == Decimal("1955.00")
        assert sample_trade.status == "PENDING"
        assert isinstance(sample_trade.timestamp, datetime)

    def test_trade_validation(self):
        """Test trade validation."""
        # Valid trade
        trade = Trade(
            symbol="XAUUSD",
            trade_type="BUY",
            volume=Decimal("0.1"),
            price=Decimal("1950.50"),
            stop_loss=Decimal("1948.00"),
            take_profit=Decimal("1955.00"),
            status="PENDING",
            timestamp=datetime.utcnow(),
        )
        assert trade.is_valid()

        # Invalid volume
        invalid_trade = Trade(
            symbol="XAUUSD",
            trade_type="BUY",
            volume=Decimal("0"),  # Invalid: zero volume
            price=Decimal("1950.50"),
            stop_loss=Decimal("1948.00"),
            take_profit=Decimal("1955.00"),
            status="PENDING",
            timestamp=datetime.utcnow(),
        )
        assert not invalid_trade.is_valid()

        # Invalid status
        invalid_trade = Trade(
            symbol="XAUUSD",
            trade_type="BUY",
            volume=Decimal("0.1"),
            price=Decimal("1950.50"),
            stop_loss=Decimal("1948.00"),
            take_profit=Decimal("1955.00"),
            status="INVALID",  # Invalid status
            timestamp=datetime.utcnow(),
        )
        assert not invalid_trade.is_valid()

    def test_trade_profit_loss(self, sample_trade):
        """Test profit/loss calculation."""
        # No profit/loss initially
        assert sample_trade.calculate_profit_loss() == Decimal("0")

        # Set current price for profit
        sample_trade.current_price = Decimal("1955.00")
        profit_loss = sample_trade.calculate_profit_loss()
        assert profit_loss == Decimal("4.50")  # 1955.00 - 1950.50

        # Set current price for loss
        sample_trade.current_price = Decimal("1948.00")
        profit_loss = sample_trade.calculate_profit_loss()
        assert profit_loss == Decimal("-2.50")  # 1948.00 - 1950.50

    def test_trade_is_open(self, sample_trade):
        """Test trade open status."""
        # Pending trade should be open
        assert sample_trade.is_open()

        # Executed trade should be open
        sample_trade.status = "EXECUTED"
        assert sample_trade.is_open()

        # Closed trade should not be open
        sample_trade.status = "CLOSED"
        assert not sample_trade.is_open()

        # Cancelled trade should not be open
        sample_trade.status = "CANCELLED"
        assert not sample_trade.is_open()

    def test_trade_to_dict(self, sample_trade):
        """Test trade serialization."""
        trade_dict = sample_trade.to_dict()

        assert trade_dict["symbol"] == "XAUUSD"
        assert trade_dict["trade_type"] == "BUY"
        assert trade_dict["volume"] == "0.1"
        assert trade_dict["price"] == "1950.50"
        assert trade_dict["stop_loss"] == "1948.00"
        assert trade_dict["take_profit"] == "1955.00"
        assert trade_dict["status"] == "PENDING"
        assert "timestamp" in trade_dict


class TestTick:
    """Test Tick model."""

    def test_tick_creation(self, sample_tick):
        """Test tick creation."""
        assert sample_tick.symbol == "XAUUSD"
        assert sample_tick.bid == Decimal("1950.50")
        assert sample_tick.ask == Decimal("1950.60")
        assert sample_tick.last == Decimal("1950.55")
        assert sample_tick.volume == 100
        assert isinstance(sample_tick.timestamp, datetime)

    def test_tick_spread(self, sample_tick):
        """Test spread calculation."""
        spread = sample_tick.calculate_spread()
        assert spread == Decimal("0.10")  # 1950.60 - 1950.50

    def test_tick_mid_price(self, sample_tick):
        """Test mid price calculation."""
        mid_price = sample_tick.calculate_mid_price()
        expected_mid = (sample_tick.bid + sample_tick.ask) / 2
        assert mid_price == expected_mid

    def test_tick_to_dict(self, sample_tick):
        """Test tick serialization."""
        tick_dict = sample_tick.to_dict()

        assert tick_dict["symbol"] == "XAUUSD"
        assert tick_dict["bid"] == "1950.50"
        assert tick_dict["ask"] == "1950.60"
        assert tick_dict["last"] == "1950.55"
        assert tick_dict["volume"] == 100
        assert "timestamp" in tick_dict


class TestCandle:
    """Test Candle model."""

    def test_candle_creation(self, sample_candle):
        """Test candle creation."""
        assert sample_candle.symbol == "XAUUSD"
        assert sample_candle.timeframe == "M15"
        assert sample_candle.open == Decimal("1950.00")
        assert sample_candle.high == Decimal("1951.00")
        assert sample_candle.low == Decimal("1949.50")
        assert sample_candle.close == Decimal("1950.75")
        assert sample_candle.volume == 500
        assert isinstance(sample_candle.timestamp, datetime)

    def test_candle_range(self, sample_candle):
        """Test range calculation."""
        candle_range = sample_candle.calculate_range()
        expected_range = sample_candle.high - sample_candle.low
        assert candle_range == expected_range

    def test_candle_body_size(self, sample_candle):
        """Test body size calculation."""
        body_size = sample_candle.calculate_body_size()
        expected_body = abs(sample_candle.close - sample_candle.open)
        assert body_size == expected_body

    def test_candle_is_bullish(self, sample_candle):
        """Test bullish candle detection."""
        # Bullish candle
        sample_candle.open = Decimal("1950.00")
        sample_candle.close = Decimal("1950.75")
        assert sample_candle.is_bullish()

        # Bearish candle
        sample_candle.open = Decimal("1950.75")
        sample_candle.close = Decimal("1950.00")
        assert not sample_candle.is_bullish()

    def test_candle_is_bearish(self, sample_candle):
        """Test bearish candle detection."""
        # Bearish candle
        sample_candle.open = Decimal("1950.75")
        sample_candle.close = Decimal("1950.00")
        assert sample_candle.is_bearish()

        # Bullish candle
        sample_candle.open = Decimal("1950.00")
        sample_candle.close = Decimal("1950.75")
        assert not sample_candle.is_bearish()

    def test_candle_upper_shadow(self, sample_candle):
        """Test upper shadow calculation."""
        upper_shadow = sample_candle.calculate_upper_shadow()
        expected_shadow = sample_candle.high - max(
            sample_candle.open, sample_candle.close
        )
        assert upper_shadow == expected_shadow

    def test_candle_lower_shadow(self, sample_candle):
        """Test lower shadow calculation."""
        lower_shadow = sample_candle.calculate_lower_shadow()
        expected_shadow = (
            min(sample_candle.open, sample_candle.close) - sample_candle.low
        )
        assert lower_shadow == expected_shadow

    def test_candle_to_dict(self, sample_candle):
        """Test candle serialization."""
        candle_dict = sample_candle.to_dict()

        assert candle_dict["symbol"] == "XAUUSD"
        assert candle_dict["timeframe"] == "M15"
        assert candle_dict["open"] == "1950.00"
        assert candle_dict["high"] == "1951.00"
        assert candle_dict["low"] == "1949.50"
        assert candle_dict["close"] == "1950.75"
        assert candle_dict["volume"] == 500
        assert "timestamp" in candle_dict


class TestModelValidation:
    """Test model validation edge cases."""

    def test_signal_with_invalid_prices(self):
        """Test signal with invalid price relationships."""
        # Stop loss above entry price for BUY signal
        with pytest.raises(ValueError):
            Signal(
                symbol="XAUUSD",
                signal_type="BUY",
                entry_price=Decimal("1950.50"),
                stop_loss=Decimal("1951.00"),  # Above entry
                take_profit=Decimal("1955.00"),
                confidence=0.85,
                reasoning="Test signal",
                timestamp=datetime.utcnow(),
            )

        # Take profit below entry price for BUY signal
        with pytest.raises(ValueError):
            Signal(
                symbol="XAUUSD",
                signal_type="BUY",
                entry_price=Decimal("1950.50"),
                stop_loss=Decimal("1948.00"),
                take_profit=Decimal("1949.00"),  # Below entry
                confidence=0.85,
                reasoning="Test signal",
                timestamp=datetime.utcnow(),
            )

        # Stop loss below entry price for SELL signal
        with pytest.raises(ValueError):
            Signal(
                symbol="XAUUSD",
                signal_type="SELL",
                entry_price=Decimal("1950.50"),
                stop_loss=Decimal("1949.00"),  # Below entry
                take_profit=Decimal("1948.00"),
                confidence=0.85,
                reasoning="Test signal",
                timestamp=datetime.utcnow(),
            )

    def test_trade_with_invalid_prices(self):
        """Test trade with invalid price relationships."""
        # Stop loss above entry price for BUY trade
        with pytest.raises(ValueError):
            Trade(
                symbol="XAUUSD",
                trade_type="BUY",
                volume=Decimal("0.1"),
                price=Decimal("1950.50"),
                stop_loss=Decimal("1951.00"),  # Above entry
                take_profit=Decimal("1955.00"),
                status="PENDING",
                timestamp=datetime.utcnow(),
            )

    def test_candle_with_invalid_prices(self):
        """Test candle with invalid price relationships."""
        # High lower than low
        with pytest.raises(ValueError):
            Candle(
                symbol="XAUUSD",
                timeframe="M15",
                timestamp=datetime.utcnow(),
                open=Decimal("1950.00"),
                high=Decimal("1949.00"),  # Lower than low
                low=Decimal("1949.50"),
                close=Decimal("1950.75"),
                volume=500,
            )

        # Close outside high-low range
        with pytest.raises(ValueError):
            Candle(
                symbol="XAUUSD",
                timeframe="M15",
                timestamp=datetime.utcnow(),
                open=Decimal("1950.00"),
                high=Decimal("1951.00"),
                low=Decimal("1949.50"),
                close=Decimal("1951.50"),  # Above high
                volume=500,
            )
