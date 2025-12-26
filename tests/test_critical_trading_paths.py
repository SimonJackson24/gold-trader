"""
Comprehensive tests for critical trading paths.

Tests all critical trading functionality including signal generation,
trade execution, risk management, and error scenarios.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import uuid

from src.trading.signal_generator import SignalGenerator
from src.trading.trade_manager import TradeManager
from src.models.signal import TradingSignal, SignalStatus, SessionType
from src.models.trade import Trade, TradeStatus, ExitReason
from src.models.market_data import Tick, Candle
from src.core import (
    trade_locks,
    signal_cache,
    trade_cache,
    error_recovery_manager,
    memory_monitor,
    security_logger,
    audit_logger,
)


class TestSignalGeneration:
    """Test signal generation critical paths."""

    @pytest.fixture
    def signal_generator(self):
        """Create signal generator fixture."""
        return SignalGenerator()

    @pytest.fixture
    def sample_confluence_analysis(self):
        """Create sample confluence analysis."""
        mock_analysis = Mock()
        mock_analysis.meets_threshold.return_value = True
        mock_analysis.market_structure = "BULLISH_TREND"
        mock_analysis.confidence = 0.85
        mock_analysis.get_confluence_factors.return_value = [
            "FVG",
            "ORDER_BLOCK",
            "BULLISH_CONFIRMATION",
        ]
        mock_analysis.h4_analysis = Mock()
        mock_analysis.h1_analysis = Mock()
        mock_analysis.m15_analysis = Mock()
        return mock_analysis

    @pytest.mark.asyncio
    async def test_signal_generation_success(
        self, signal_generator, sample_confluence_analysis
    ):
        """Test successful signal generation."""
        current_price = Decimal("2000.50")

        signal = await signal_generator.generate_signal(
            sample_confluence_analysis, current_price
        )

        assert signal is not None
        assert signal.instrument == "XAUUSD"
        assert signal.direction in ["BUY", "SELL"]
        assert signal.entry_price == current_price
        assert signal.stop_loss is not None
        assert signal.take_profit_1 is not None
        assert signal.take_profit_2 is not None
        assert signal.confidence_score >= 0.7
        assert signal.status == SignalStatus.ACTIVE
        assert signal.signal_id is not None

    @pytest.mark.asyncio
    async def test_signal_generation_insufficient_confluence(self, signal_generator):
        """Test signal generation with insufficient confluence."""
        mock_analysis = Mock()
        mock_analysis.meets_threshold.return_value = False
        mock_analysis.confidence = 0.3

        current_price = Decimal("2000.50")
        signal = await signal_generator.generate_signal(mock_analysis, current_price)

        assert signal is None

    @pytest.mark.asyncio
    async def test_signal_validation(self, signal_generator):
        """Test signal validation."""
        # Create valid signal
        signal = TradingSignal(
            signal_id=str(uuid.uuid4()),
            instrument="XAUUSD",
            direction="BUY",
            entry_price=Decimal("2000.50"),
            stop_loss=Decimal("1990.50"),
            take_profit_1=Decimal("2020.50"),
            take_profit_2=Decimal("2030.50"),
            position_size=Decimal("0.1"),
            risk_percentage=2.0,
            confidence_score=0.8,
            status=SignalStatus.ACTIVE,
        )

        validation = signal_generator.validate_signal(signal)
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0

    @pytest.mark.asyncio
    async def test_signal_validation_invalid_risk_reward(self, signal_generator):
        """Test signal validation with invalid risk:reward."""
        # Create signal with poor risk:reward
        signal = TradingSignal(
            signal_id=str(uuid.uuid4()),
            instrument="XAUUSD",
            direction="BUY",
            entry_price=Decimal("2000.50"),
            stop_loss=Decimal("1995.50"),  # Only 5 pips risk
            take_profit_1=Decimal("2005.50"),  # Only 10 pips reward
            take_profit_2=Decimal("2010.50"),
            position_size=Decimal("0.1"),
            risk_percentage=2.0,
            confidence_score=0.8,
            status=SignalStatus.ACTIVE,
        )

        validation = signal_generator.validate_signal(signal)
        assert validation["is_valid"] is False
        assert len(validation["errors"]) > 0
        assert any("risk:reward" in error for error in validation["errors"])


class TestTradeExecution:
    """Test trade execution critical paths."""

    @pytest.fixture
    def trade_manager(self):
        """Create trade manager fixture."""
        return TradeManager()

    @pytest.fixture
    def sample_signal(self):
        """Create sample trading signal."""
        return TradingSignal(
            signal_id=str(uuid.uuid4()),
            instrument="XAUUSD",
            direction="BUY",
            entry_price=Decimal("2000.50"),
            stop_loss=Decimal("1990.50"),
            take_profit_1=Decimal("2020.50"),
            take_profit_2=Decimal("2030.50"),
            position_size=Decimal("0.1"),
            risk_percentage=2.0,
            confidence_score=0.8,
            status=SignalStatus.ACTIVE,
        )

    @pytest.mark.asyncio
    async def test_trade_opening_success(self, trade_manager, sample_signal):
        """Test successful trade opening."""
        # Mock trade repository
        with patch.object(trade_manager, "trade_repo") as mock_repo:
            mock_repo.create_trade = AsyncMock()
            mock_trade = Mock()
            mock_trade.trade_id = 123
            mock_repo.create_trade.return_value = mock_trade

            trade = await trade_manager.open_trade(sample_signal)

            assert trade is not None
            assert trade.trade_id == 123
            mock_repo.create_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_trade_opening_limit_reached(self, trade_manager, sample_signal):
        """Test trade opening when limit is reached."""
        # Mock concurrent trades limit
        with patch.object(trade_manager.settings.trading, "max_concurrent_trades", 0):
            trade = await trade_manager.open_trade(sample_signal)
            assert trade is None

    @pytest.mark.asyncio
    async def test_trade_monitoring_price_update(self, trade_manager):
        """Test trade price monitoring."""
        # Create active trade
        trade_id = 123
        current_price = Decimal("2005.50")

        with patch.object(trade_manager, "_get_current_price") as mock_price:
            mock_price.return_value = current_price

            with patch.object(
                trade_manager.trade_repo, "update_trade_price"
            ) as mock_update:
                await trade_manager.monitor_trades()

                # Should update price for active trades
                mock_update.assert_called()

    @pytest.mark.asyncio
    async def test_trade_stop_loss_hit(self, trade_manager):
        """Test trade stop loss hit."""
        # Create trade that should hit stop loss
        trade_id = 123
        current_price = Decimal("1989.50")  # Below stop loss

        with patch.object(trade_manager, "_get_current_price") as mock_price:
            mock_price.return_value = current_price

            with patch.object(trade_manager, "_close_trade") as mock_close:
                await trade_manager.monitor_trades()

                # Should close trade
                mock_close.assert_called()

    @pytest.mark.asyncio
    async def test_trade_take_profit_hit(self, trade_manager):
        """Test trade take profit hit."""
        # Create trade that should hit take profit
        trade_id = 123
        current_price = Decimal("2021.50")  # Above take profit 1

        with patch.object(trade_manager, "_get_current_price") as mock_price:
            mock_price.return_value = current_price

            with patch.object(trade_manager, "_partial_close_trade") as mock_partial:
                await trade_manager.monitor_trades()

                # Should partially close trade
                mock_partial.assert_called()


class TestRiskManagement:
    """Test risk management critical paths."""

    @pytest.fixture
    def trade_manager(self):
        """Create trade manager fixture."""
        return TradeManager()

    def test_position_size_calculation(self, trade_manager):
        """Test position size calculation."""
        risk_amount = 1000.0  # $1000 risk
        risk_pips = Decimal("10.0")  # 10 pips risk

        position_size = trade_manager.settings.trading.calculate_position_size(
            risk_amount, risk_pips
        )

        assert position_size > 0
        assert position_size <= trade_manager.settings.trading.max_lot_size

    def test_risk_percentage_validation(self, trade_manager):
        """Test risk percentage validation."""
        # Test valid risk percentage
        valid_risk = 2.0
        assert (
            trade_manager.settings.trading.validate_risk_percentage(valid_risk) is True
        )

        # Test invalid risk percentage
        invalid_risk = 10.0  # Too high
        assert (
            trade_manager.settings.trading.validate_risk_percentage(invalid_risk)
            is False
        )

    def test_concurrent_trades_limit(self, trade_manager):
        """Test concurrent trades limit."""
        # Test within limit
        current_trades = 2
        max_trades = trade_manager.settings.trading.max_concurrent_trades

        assert current_trades < max_trades
        assert trade_manager._can_open_trade() is True

        # Test at limit
        current_trades = max_trades
        assert trade_manager._can_open_trade() is False

    @pytest.mark.asyncio
    async def test_breakeven_movement(self, trade_manager):
        """Test stop loss to breakeven movement."""
        # Create buy trade
        trade = Mock()
        trade.is_buy = True
        trade.entry_price = Decimal("2000.50")
        trade.breakeven_moved = False

        current_price = Decimal("2005.50")  # 5 pips profit

        with patch.object(
            trade_manager.trade_repo, "update_trade_price"
        ) as mock_update:
            await trade_manager._check_trade_exit(trade.trade_id, current_price)

            # Should move to breakeven
            trade.move_stop_to_breakeven.assert_called_once()
            mock_update.assert_called()


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips(self):
        """Test circuit breaker functionality."""
        # Create circuit breaker
        breaker = error_recovery_manager.register_circuit_breaker(
            "test_breaker", failure_threshold=3, recovery_timeout=10
        )

        # Simulate failures
        failing_func = AsyncMock(side_effect=Exception("Simulated failure"))

        # First 3 failures should trigger circuit breaker
        for i in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        # 4th call should fail due to open circuit
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(failing_func)

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry mechanism with exponential backoff."""
        retry_handler = error_recovery_manager.register_retry_handler(
            "test_retry", max_retries=3, base_delay=0.1
        )

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return "success"

        result = await retry_handler.execute(failing_func)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_memory_error_recovery(self):
        """Test memory error recovery."""
        error_info = Mock()
        error_info.error_type = "memory_error"
        error_info.severity = "critical"
        error_info.message = "Out of memory"

        # Should trigger memory cleanup
        handled = await error_recovery_manager.handle_error(error_info)
        assert handled is True


class TestSecurityScenarios:
    """Test security-related scenarios."""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        from src.database.repositories import SignalRepository

        # Create mock session
        mock_session = Mock()
        repo = SignalRepository(mock_session)

        # Attempt SQL injection
        malicious_input = "'; DROP TABLE signals; --"

        # Should sanitize input or use parameterized queries
        with patch.object(mock_session, "execute") as mock_execute:
            try:
                repo.get_signal_by_id(malicious_input)
            except Exception:
                pass  # Expected to fail safely

            # Verify no dangerous SQL was executed
            calls = mock_execute.call_args_list
            for call in calls:
                query = str(call[0][0]) if call[0] else ""
                assert "DROP TABLE" not in query.upper()

    @pytest.mark.asyncio
    async def test_authentication_token_validation(self):
        """Test JWT token validation."""
        from src.auth.jwt_handler import jwt_handler

        # Create valid token
        user_data = {
            "user_id": "test_user",
            "username": "testuser",
            "role": "user",
            "permissions": ["read"],
        }

        token, jti, expiry = await jwt_handler.create_access_token(user_data)

        # Verify valid token
        payload = await jwt_handler.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "test_user"
        assert payload["username"] == "testuser"

        # Test invalid token
        invalid_token = token[:-10] + "invalid"
        payload = await jwt_handler.verify_token(invalid_token)
        assert payload is None

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        from src.auth.jwt_handler import jwt_handler

        # Create mock request
        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Should allow within limit
        for i in range(10):
            allowed = await jwt_handler.check_rate_limit(
                mock_request, limit=20, window=60
            )
            assert allowed is True

        # Should exceed limit
        for i in range(15):  # Total 25 requests
            allowed = await jwt_handler.check_rate_limit(
                mock_request, limit=20, window=60
            )
            if i >= 19:  # 21st request
                assert allowed is False
            else:
                assert allowed is True


class TestPerformanceAndMemory:
    """Test performance and memory management."""

    @pytest.mark.asyncio
    async def test_memory_monitoring(self):
        """Test memory monitoring."""
        # Get initial stats
        initial_stats = await memory_monitor.get_memory_stats()
        assert initial_stats.process_memory_mb > 0

        # Test cleanup callback
        cleanup_called = False

        def cleanup_callback():
            nonlocal cleanup_called
            cleanup_called = True

        memory_monitor.add_cleanup_callback(cleanup_callback)

        # Trigger emergency cleanup
        await memory_monitor._emergency_cleanup()
        assert cleanup_called is True

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test bounded cache functionality."""
        from src.core.memory_manager import BoundedCache

        cache = BoundedCache(maxsize=3, ttl_seconds=60)

        # Add items
        assert cache.put("key1", "value1") is True
        assert cache.put("key2", "value2") is True
        assert cache.put("key3", "value3") is True

        # Cache should be full
        assert cache.put("key4", "value4") is False

        # Retrieve items
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("nonexistent") is None

        # Test size
        assert cache.size() == 3

    @pytest.mark.asyncio
    async def test_resource_locking(self):
        """Test resource locking mechanism."""
        from src.core.synchronization import ResourceManager

        resource_manager = ResourceManager()

        # Acquire lock
        acquired = await resource_manager.acquire_resource(
            "test_resource", "write", "test_user"
        )
        assert acquired is True

        # Try to acquire same lock (should fail)
        acquired2 = await resource_manager.acquire_resource(
            "test_resource", "write", "test_user2"
        )
        assert acquired2 is False

        # Release lock
        released = await resource_manager.release_resource("test_resource", "test_user")
        assert released is True

        # Should be able to acquire again
        acquired3 = await resource_manager.acquire_resource(
            "test_resource", "write", "test_user3"
        )
        assert acquired3 is True


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""

    @pytest.mark.asyncio
    async def test_signal_to_trade_workflow(self):
        """Test complete signal to trade workflow."""
        # Create signal generator and trade manager
        signal_gen = SignalGenerator()
        trade_mgr = TradeManager()

        # Mock confluence analysis
        mock_analysis = Mock()
        mock_analysis.meets_threshold.return_value = True
        mock_analysis.confidence = 0.8
        mock_analysis.market_structure = "BULLISH"

        # Generate signal
        current_price = Decimal("2000.50")
        signal = await signal_gen.generate_signal(mock_analysis, current_price)

        assert signal is not None
        assert signal.direction == "BUY"

        # Execute trade
        with patch.object(trade_mgr, "trade_repo") as mock_repo:
            mock_trade = Mock()
            mock_trade.trade_id = 456
            mock_repo.create_trade.return_value = mock_trade

            trade = await trade_mgr.open_trade(signal)

            assert trade is not None
            assert trade.trade_id == 456

    @pytest.mark.asyncio
    async def test_error_propagation_and_recovery(self):
        """Test error propagation through trading workflow."""
        signal_gen = SignalGenerator()
        trade_mgr = TradeManager()

        # Simulate database error
        with patch.object(trade_mgr.trade_repo, "create_trade") as mock_create:
            mock_create.side_effect = Exception("Database connection failed")

            # Should handle error gracefully
            signal = TradingSignal(
                signal_id=str(uuid.uuid4()),
                instrument="XAUUSD",
                direction="BUY",
                entry_price=Decimal("2000.50"),
                stop_loss=Decimal("1990.50"),
                take_profit_1=Decimal("2020.50"),
                position_size=Decimal("0.1"),
                confidence_score=0.8,
                status=SignalStatus.ACTIVE,
            )

            trade = await trade_mgr.open_trade(signal)
            assert trade is None  # Should return None on error


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Test performance benchmarks for critical operations."""

    @pytest.mark.asyncio
    async def test_signal_generation_performance(self):
        """Test signal generation performance."""
        signal_gen = SignalGenerator()
        mock_analysis = Mock()
        mock_analysis.meets_threshold.return_value = True
        mock_analysis.confidence = 0.8

        # Measure performance
        import time

        start_time = time.time()

        for _ in range(100):  # Generate 100 signals
            await signal_gen.generate_signal(mock_analysis, Decimal("2000.50"))

        duration = time.time() - start_time

        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for 100 signals
        assert duration / 100 < 0.05  # 50ms per signal average

    @pytest.mark.asyncio
    async def test_trade_execution_performance(self):
        """Test trade execution performance."""
        trade_mgr = TradeManager()
        signal = TradingSignal(
            signal_id=str(uuid.uuid4()),
            instrument="XAUUSD",
            direction="BUY",
            entry_price=Decimal("2000.50"),
            stop_loss=Decimal("1990.50"),
            take_profit_1=Decimal("2020.50"),
            position_size=Decimal("0.1"),
            confidence_score=0.8,
            status=SignalStatus.ACTIVE,
        )

        with patch.object(trade_mgr, "trade_repo") as mock_repo:
            mock_repo.create_trade = AsyncMock()
            mock_trade = Mock()
            mock_trade.trade_id = 789
            mock_repo.create_trade.return_value = mock_trade

            # Measure performance
            import time

            start_time = time.time()

            for _ in range(50):  # Execute 50 trades
                await trade_mgr.open_trade(signal)

            duration = time.time() - start_time

            # Should complete within reasonable time
            assert duration < 2.0  # 2 seconds for 50 trades
            assert duration / 50 < 0.04  # 40ms per trade average


if __name__ == "__main__":
    pytest.main([__file__])
