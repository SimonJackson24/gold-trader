"""
Pytest configuration and fixtures for XAUUSD Gold Trading System tests.

Provides test fixtures, configuration, and utilities.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import sqlite3
import json

from src.database import Database, get_database
from src.config import Settings, get_settings
from src.models.signal import Signal
from src.models.trade import Trade
from src.models.market_data import Tick, Candle
from src.smart_money.smart_money_engine import SmartMoneyEngine
from src.signal_generator.signal_generator import SignalGenerator
from src.trade_manager.trade_manager import TradeManager
from src.market_data.market_data_processor import MarketDataProcessor
from src.monitoring.metrics import MetricsRegistry
from tests import TEST_CONFIG


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    db = Database(f"sqlite:///{db_path}")
    asyncio.run(db.connect())
    
    yield db
    
    asyncio.run(db.disconnect())
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        database_url=TEST_CONFIG['database_url'],
        redis_url=TEST_CONFIG['redis_url'],
        debug=True,
        log_level=TEST_CONFIG['log_level'],
        api_secret_key="test_secret_key",
        telegram_bot_token="test_token",
        telegram_admin_id=123456789,
        cors_origins=["http://localhost:3000"]
    )


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setattr("src.config.get_settings", lambda: test_settings())
    return test_settings()


@pytest.fixture
def test_db(mock_settings):
    """Create test database with mocked settings."""
    db = get_database()
    asyncio.run(db.connect())
    
    # Create tables
    asyncio.run(db.create_tables())
    
    yield db
    
    asyncio.run(db.disconnect())


@pytest.fixture
def sample_tick():
    """Create sample tick data."""
    return Tick(
        symbol="XAUUSD",
        timestamp=datetime.utcnow(),
        bid=Decimal("1950.50"),
        ask=Decimal("1950.60"),
        last=Decimal("1950.55"),
        volume=100
    )


@pytest.fixture
def sample_candle():
    """Create sample candle data."""
    return Candle(
        symbol="XAUUSD",
        timeframe="M15",
        timestamp=datetime.utcnow(),
        open=Decimal("1950.00"),
        high=Decimal("1951.00"),
        low=Decimal("1949.50"),
        close=Decimal("1950.75"),
        volume=500
    )


@pytest.fixture
def sample_signal():
    """Create sample trading signal."""
    return Signal(
        symbol="XAUUSD",
        signal_type="BUY",
        entry_price=Decimal("1950.50"),
        stop_loss=Decimal("1948.00"),
        take_profit=Decimal("1955.00"),
        confidence=0.85,
        reasoning="Smart Money Concepts analysis indicates bullish bias",
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def sample_trade():
    """Create sample trade."""
    return Trade(
        symbol="XAUUSD",
        trade_type="BUY",
        volume=Decimal("0.1"),
        price=Decimal("1950.50"),
        stop_loss=Decimal("1948.00"),
        take_profit=Decimal("1955.00"),
        status="PENDING",
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def smart_money_engine():
    """Create Smart Money engine instance."""
    return SmartMoneyEngine()


@pytest.fixture
def signal_generator():
    """Create signal generator instance."""
    return SignalGenerator()


@pytest.fixture
def trade_manager():
    """Create trade manager instance."""
    return TradeManager()


@pytest.fixture
def market_data_processor():
    """Create market data processor instance."""
    return MarketDataProcessor()


@pytest.fixture
def metrics_registry():
    """Create metrics registry for testing."""
    return MetricsRegistry()


@pytest.fixture
def mock_mt5_response():
    """Mock MT5 response data."""
    return {
        'retcode': 10009,  # TRADE_RETCODE_DONE
        'order': 123456,
        'position': 789012,
        'price': 1950.50,
        'volume': 0.1,
        'symbol': 'XAUUSD',
        'type': 0,  # ORDER_TYPE_BUY
        'comment': 'Test trade'
    }


@pytest.fixture
def market_data_samples():
    """Create sample market data for testing."""
    base_time = datetime.utcnow()
    
    ticks = []
    for i in range(10):
        tick = Tick(
            symbol="XAUUSD",
            timestamp=base_time,
            bid=Decimal(f"1950.{i:02d}"),
            ask=Decimal(f"1950.{i+10:02d}"),
            last=Decimal(f"1950.{i+5:02d}"),
            volume=100 + i
        )
        ticks.append(tick)
    
    candles = []
    for i in range(5):
        candle = Candle(
            symbol="XAUUSD",
            timeframe="M15",
            timestamp=base_time,
            open=Decimal(f"1950.{i:02d}"),
            high=Decimal(f"1951.{i:02d}"),
            low=Decimal(f"1949.{i:02d}"),
            close=Decimal(f"1950.{i+5:02d}"),
            volume=500 + i * 100
        )
        candles.append(candle)
    
    return {
        'ticks': ticks,
        'candles': candles
    }


@pytest.fixture
def websocket_test_client():
    """Create WebSocket test client."""
    from unittest.mock import AsyncMock
    
    client = AsyncMock()
    client.remote_address = ('127.0.0.1', 12345)
    client.send = AsyncMock()
    return client


@pytest.fixture
def telegram_test_bot():
    """Create Telegram bot mock for testing."""
    from unittest.mock import AsyncMock
    
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


class AsyncContextManager:
    """Helper for async context managers in tests."""
    
    def __init__(self, async_func):
        self.async_func = async_func
        self.result = None
    
    async def __aenter__(self):
        self.result = await self.async_func()
        return self.result
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def async_cm(async_func):
    """Create async context manager from async function."""
    return AsyncContextManager(async_func)


@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    from unittest.mock import AsyncMock
    
    db = AsyncMock()
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.execute = AsyncMock()
    db.fetch_all = AsyncMock(return_value=[])
    db.fetch_one = AsyncMock(return_value=None)
    db.insert = AsyncMock()
    db.update = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def sample_analysis_result():
    """Sample Smart Money analysis result."""
    return {
        'market_structure': {
            'trend': 'bullish',
            'key_levels': {
                'support': [Decimal('1948.00'), Decimal('1945.00')],
                'resistance': [Decimal('1952.00'), Decimal('1955.00')]
            },
            'market_phase': 'accumulation'
        },
        'smart_money_concepts': {
            'order_blocks': [
                {
                    'price': Decimal('1949.50'),
                    'type': 'buy',
                    'strength': 0.8
                }
            ],
            'liquidity_zones': [
                {
                    'price_range': [Decimal('1951.00'), Decimal('1951.50')],
                    'type': 'sell_side'
                }
            ],
            'fvg': [
                {
                    'price_range': [Decimal('1950.00'), Decimal('1950.25')],
                    'type': 'bullish'
                }
            ]
        },
        'volume_analysis': {
            'volume_profile': 'increasing',
            'buying_pressure': 0.7,
            'selling_pressure': 0.3
        },
        'confidence': 0.85,
        'recommendation': 'BUY'
    }


# Test data helpers
def create_test_signal_data(**kwargs):
    """Create test signal data with overrides."""
    defaults = {
        'symbol': 'XAUUSD',
        'signal_type': 'BUY',
        'entry_price': Decimal('1950.50'),
        'stop_loss': Decimal('1948.00'),
        'take_profit': Decimal('1955.00'),
        'confidence': 0.85,
        'reasoning': 'Test signal',
        'timestamp': datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_test_trade_data(**kwargs):
    """Create test trade data with overrides."""
    defaults = {
        'symbol': 'XAUUSD',
        'trade_type': 'BUY',
        'volume': Decimal('0.1'),
        'price': Decimal('1950.50'),
        'stop_loss': Decimal('1948.00'),
        'take_profit': Decimal('1955.00'),
        'status': 'PENDING',
        'timestamp': datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_test_tick_data(**kwargs):
    """Create test tick data with overrides."""
    defaults = {
        'symbol': 'XAUUSD',
        'timestamp': datetime.utcnow(),
        'bid': Decimal('1950.50'),
        'ask': Decimal('1950.60'),
        'last': Decimal('1950.55'),
        'volume': 100
    }
    defaults.update(kwargs)
    return defaults


# Async test utilities
async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
    """Wait for a condition to become true."""
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if condition_func():
            return True
        
        current_time = asyncio.get_event_loop().time()
        if current_time - start_time > timeout:
            return False
        
        await asyncio.sleep(interval)


# Mock utilities
def create_mock_response(status_code=200, data=None):
    """Create mock HTTP response."""
    from unittest.mock import Mock
    
    response = Mock()
    response.status_code = status_code
    response.json = AsyncMock(return_value=data or {})
    response.text = AsyncMock(return_value=json.dumps(data or {}))
    return response


def create_mock_websocket_message(message_type, data):
    """Create mock WebSocket message."""
    return {
        'type': message_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }