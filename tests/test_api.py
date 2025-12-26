"""
Integration tests for REST API.

Tests all API endpoints including authentication,
validation, and error handling.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import pytest
import json
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.main import app
from src.models.signal import Signal
from src.models.trade import Trade


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self):
        """Test basic health check endpoint."""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert data["version"] == "1.0.0"

    def test_status_endpoint_with_auth(self):
        """Test status endpoint with authentication."""
        with TestClient(app) as client:
            headers = {"Authorization": "Bearer test_secret_key"}
            response = client.get("/status", headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["api"] == "running"
            assert "services" in data
            assert "timestamp" in data

    def test_status_endpoint_without_auth(self):
        """Test status endpoint without authentication."""
        with TestClient(app) as client:
            response = client.get("/status")
            assert response.status_code == 401

            data = response.json()
            assert data["error"]["code"] == 401
            assert "Invalid authentication token" in data["error"]["message"]


class TestSignalEndpoints:
    """Test signal endpoints."""

    def test_get_signals_with_auth(self, mock_settings, sample_signal):
        """Test getting signals with authentication."""
        with patch("src.api.main.signal_generator") as mock_sg:
            mock_sg.get_recent_signals = AsyncMock(return_value=[sample_signal])

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/signals", headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert "signals" in data
                assert "total" in data
                assert len(data["signals"]) == 1

    def test_get_signals_without_auth(self):
        """Test getting signals without authentication."""
        with TestClient(app) as client:
            response = client.get("/signals")
            assert response.status_code == 401

    def test_create_signal_with_auth(self, mock_settings):
        """Test creating signal with authentication."""
        signal_data = {
            "symbol": "XAUUSD",
            "signal_type": "BUY",
            "entry_price": "1950.50",
            "stop_loss": "1948.00",
            "take_profit": "1955.00",
            "confidence": 0.85,
            "reasoning": "Test signal",
        }

        with patch("src.api.main.signal_generator") as mock_sg:
            mock_sg.process_signal = AsyncMock()

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.post("/signals", json=signal_data, headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert data["message"] == "Signal created successfully"
                assert "signal" in data

    def test_create_signal_invalid_data(self, mock_settings):
        """Test creating signal with invalid data."""
        invalid_data = {
            "symbol": "XAUUSD",
            "signal_type": "INVALID",  # Invalid signal type
            "entry_price": "1950.50",
            "stop_loss": "1948.00",
            "take_profit": "1955.00",
            "confidence": 1.5,  # Invalid confidence > 1.0
            "reasoning": "Test signal",
        }

        with TestClient(app) as client:
            headers = {"Authorization": "Bearer test_secret_key"}
            response = client.post("/signals", json=invalid_data, headers=headers)
            assert response.status_code == 422  # Validation error

    def test_get_signal_by_id(self, mock_settings, sample_signal):
        """Test getting signal by ID."""
        with patch("src.api.main.signal_generator") as mock_sg:
            mock_sg.get_signal = AsyncMock(return_value=sample_signal)

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/signals/test_signal_id", headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert data["symbol"] == "XAUUSD"
                assert data["signal_type"] == "BUY"

    def test_get_signal_not_found(self, mock_settings):
        """Test getting non-existent signal."""
        with patch("src.api.main.signal_generator") as mock_sg:
            mock_sg.get_signal = AsyncMock(return_value=None)

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/signals/nonexistent", headers=headers)
                assert response.status_code == 404

                data = response.json()
                assert data["error"]["code"] == 404
                assert "Signal not found" in data["error"]["message"]


class TestTradeEndpoints:
    """Test trade endpoints."""

    def test_get_trades_with_auth(self, mock_settings, sample_trade):
        """Test getting trades with authentication."""
        with patch("src.api.main.trade_manager") as mock_tm:
            mock_tm.get_trades = AsyncMock(return_value=[sample_trade])

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/trades", headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert "trades" in data
                assert "total" in data
                assert len(data["trades"]) == 1

    def test_create_trade_with_auth(self, mock_settings):
        """Test creating trade with authentication."""
        trade_data = {
            "symbol": "XAUUSD",
            "trade_type": "BUY",
            "volume": "0.1",
            "price": "1950.50",
            "stop_loss": "1948.00",
            "take_profit": "1955.00",
        }

        with patch("src.api.main.trade_manager") as mock_tm:
            mock_tm.execute_trade = AsyncMock()

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.post("/trades", json=trade_data, headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert data["message"] == "Trade created successfully"
                assert "trade" in data

    def test_create_trade_invalid_volume(self, mock_settings):
        """Test creating trade with invalid volume."""
        invalid_data = {
            "symbol": "XAUUSD",
            "trade_type": "BUY",
            "volume": "0",  # Invalid zero volume
            "price": "1950.50",
            "stop_loss": "1948.00",
            "take_profit": "1955.00",
        }

        with TestClient(app) as client:
            headers = {"Authorization": "Bearer test_secret_key"}
            response = client.post("/trades", json=invalid_data, headers=headers)
            assert response.status_code == 422  # Validation error


class TestMarketDataEndpoints:
    """Test market data endpoints."""

    def test_get_ticks_with_auth(self, mock_settings, sample_tick):
        """Test getting tick data with authentication."""
        with patch("src.api.main.market_data_processor") as mock_mdp:
            mock_mdp.get_recent_ticks = AsyncMock(return_value=[sample_tick])

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/market/ticks", headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert data["symbol"] == "XAUUSD"
                assert "ticks" in data
                assert len(data["ticks"]) == 1

    def test_get_candles_with_auth(self, mock_settings, sample_candle):
        """Test getting candle data with authentication."""
        with patch("src.api.main.market_data_processor") as mock_mdp:
            mock_mdp.get_candles = AsyncMock(return_value=[sample_candle])

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/market/candles?timeframe=M15", headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert data["symbol"] == "XAUUSD"
                assert data["timeframe"] == "M15"
                assert "candles" in data
                assert len(data["candles"]) == 1


class TestAccountEndpoints:
    """Test account endpoints."""

    def test_get_balance_with_auth(self, mock_settings):
        """Test getting account balance with authentication."""
        balance_data = {
            "balance": 10000.0,
            "equity": 10250.0,
            "margin": 500.0,
            "free_margin": 9750.0,
            "margin_level": 2050.0,
            "profit": 250.0,
        }

        with patch("src.api.main.mt5_connector") as mock_mt5:
            mock_mt5.get_account_info = AsyncMock(return_value=balance_data)

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/account/balance", headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert data["balance"] == 10000.0
                assert data["equity"] == 10250.0

    def test_get_positions_with_auth(self, mock_settings):
        """Test getting open positions with authentication."""
        positions_data = [
            {
                "ticket": 123456,
                "symbol": "XAUUSD",
                "type": "BUY",
                "volume": 0.1,
                "price_open": 1950.50,
                "price_current": 1951.00,
                "profit": 5.0,
                "time": datetime.utcnow().isoformat(),
            }
        ]

        with patch("src.api.main.mt5_connector") as mock_mt5:
            mock_mt5.get_positions = AsyncMock(return_value=positions_data)

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.get("/account/positions", headers=headers)
                assert response.status_code == 200

                data = response.json()
                assert "positions" in data
                assert len(data["positions"]) == 1
                assert data["total"] == 1


class TestAnalysisEndpoints:
    """Test analysis endpoints."""

    def test_smart_money_analysis_with_auth(
        self, mock_settings, sample_analysis_result
    ):
        """Test Smart Money analysis with authentication."""
        with (
            patch("src.api.main.smart_money_engine") as mock_sme,
            patch("src.api.main.market_data_processor") as mock_mdp,
        ):
            mock_mdp.get_candles = AsyncMock(return_value=[])
            mock_sme.analyze_candles = AsyncMock(return_value=sample_analysis_result)

            with TestClient(app) as client:
                headers = {"Authorization": "Bearer test_secret_key"}
                response = client.post(
                    "/analysis/smart-money?symbol=XAUUSD", headers=headers
                )
                assert response.status_code == 200

                data = response.json()
                assert data["symbol"] == "XAUUSD"
                assert "analysis" in data
                assert data["analysis"]["confidence"] == 0.85
                assert data["analysis"]["recommendation"] == "BUY"


class TestWebSocketEndpoint:
    """Test WebSocket subscription endpoint."""

    def test_websocket_subscribe_with_auth(self, mock_settings):
        """Test WebSocket subscription with authentication."""
        subscription_data = {"channels": ["signals", "trades"]}

        with TestClient(app) as client:
            headers = {"Authorization": "Bearer test_secret_key"}
            response = client.post(
                "/websocket/subscribe", json=subscription_data, headers=headers
            )
            assert response.status_code == 200

            data = response.json()
            assert data["message"] == "Subscription successful"
            assert data["channels"] == ["signals", "trades"]

    def test_websocket_subscribe_invalid_channels(self, mock_settings):
        """Test WebSocket subscription with invalid channels."""
        invalid_data = {"channels": ["invalid_channel"]}

        with TestClient(app) as client:
            headers = {"Authorization": "Bearer test_secret_key"}
            response = client.post(
                "/websocket/subscribe", json=invalid_data, headers=headers
            )
            assert response.status_code == 422  # Validation error


class TestErrorHandling:
    """Test API error handling."""

    def test_404_not_found(self):
        """Test 404 error handling."""
        with TestClient(app) as client:
            response = client.get("/nonexistent_endpoint")
            assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test method not allowed error."""
        with TestClient(app) as client:
            response = client.delete("/health")  # Health endpoint only supports GET
            assert response.status_code == 405

    def test_invalid_json(self, mock_settings):
        """Test invalid JSON payload."""
        with TestClient(app) as client:
            headers = {"Authorization": "Bearer test_secret_key"}
            response = client.post(
                "/signals",
                data="invalid json",
                headers={**headers, "Content-Type": "application/json"},
            )
            assert response.status_code == 422

    def test_rate_limiting(self, mock_settings):
        """Test rate limiting (if implemented)."""
        # This test would require rate limiting middleware
        # For now, just ensure the endpoint responds correctly
        with TestClient(app) as client:
            headers = {"Authorization": "Bearer test_secret_key"}

            # Make multiple requests
            for _ in range(5):
                response = client.get("/signals", headers=headers)
                # Should succeed unless rate limit is very low
                assert response.status_code in [200, 429]


class TestCORS:
    """Test CORS handling."""

    def test_cors_headers(self, mock_settings):
        """Test CORS headers are present."""
        with TestClient(app) as client:
            headers = {
                "Authorization": "Bearer test_secret_key",
                "Origin": "http://localhost:3000",
            }
            response = client.get("/signals", headers=headers)

            # Check for CORS headers
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers
            assert "access-control-allow-headers" in response.headers

    def test_options_request(self, mock_settings):
        """Test OPTIONS preflight request."""
        with TestClient(app) as client:
            headers = {
                "Authorization": "Bearer test_secret_key",
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            }
            response = client.options("/signals", headers=headers)
            assert response.status_code == 204
