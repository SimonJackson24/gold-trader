# Testing Strategy

Comprehensive testing approach for the XAUUSD Gold Trading System.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Types](#test-types)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [Backtesting](#backtesting)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [Test Coverage](#test-coverage)
9. [Continuous Integration](#continuous-integration)
10. [Test Data Management](#test-data-management)

---

## Testing Philosophy

### Testing Pyramid

```
        /\
       /  \      E2E Tests (10%)
      /────\
     /      \    Integration Tests (30%)
    /────────\
   /          \  Unit Tests (60%)
  /────────────\
```

### Key Principles

1. **Test Early, Test Often**: Write tests before or alongside code
2. **Fast Feedback**: Tests should run quickly
3. **Isolated Tests**: Each test should be independent
4. **Readable Tests**: Tests are documentation
5. **Maintainable**: Easy to update as code changes

---

## Test Types

### 1. Unit Tests
- Test individual functions/methods
- Fast execution (<1ms per test)
- No external dependencies
- 60% of test suite

### 2. Integration Tests
- Test component interactions
- Use test database/services
- Moderate speed (10-100ms per test)
- 30% of test suite

### 3. End-to-End Tests
- Test complete workflows
- Use production-like environment
- Slower execution (1-10s per test)
- 10% of test suite

### 4. Backtesting
- Test trading strategy on historical data
- Validate SMC logic
- Performance metrics

---

## Unit Testing

### Setup

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock faker

# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html
```

### Test Structure

```python
# tests/unit/test_fvg_detector.py
import pytest
from src.analysis.fvg_detector import FVGDetector

class TestFVGDetector:
    """Test Fair Value Gap detection"""
    
    @pytest.fixture
    def detector(self):
        """Create FVG detector instance"""
        return FVGDetector()
    
    @pytest.fixture
    def sample_candles(self):
        """Sample candle data for testing"""
        return [
            {'open': 2040, 'high': 2042, 'low': 2038, 'close': 2041},
            {'open': 2041, 'high': 2050, 'low': 2041, 'close': 2049},
            {'open': 2049, 'high': 2051, 'low': 2048, 'close': 2050}
        ]
    
    def test_detect_bullish_fvg(self, detector, sample_candles):
        """Test bullish FVG detection"""
        fvgs = detector.detect_bullish_fvg(sample_candles)
        
        assert len(fvgs) == 1
        assert fvgs[0]['type'] == 'BULLISH'
        assert fvgs[0]['size_pips'] > 5
    
    def test_no_fvg_when_gap_too_small(self, detector):
        """Test that small gaps are not detected"""
        candles = [
            {'open': 2040, 'high': 2041, 'low': 2039, 'close': 2040},
            {'open': 2040, 'high': 2042, 'low': 2040, 'close': 2041},
            {'open': 2041, 'high': 2042, 'low': 2040, 'close': 2041}
        ]
        
        fvgs = detector.detect_bullish_fvg(candles)
        assert len(fvgs) == 0
    
    @pytest.mark.parametrize("gap_size,expected", [
        (3, False),  # Too small
        (5, True),   # Minimum size
        (10, True),  # Large gap
    ])
    def test_fvg_size_threshold(self, detector, gap_size, expected):
        """Test FVG size threshold"""
        # Create candles with specific gap size
        candles = self.create_candles_with_gap(gap_size)
        fvgs = detector.detect_bullish_fvg(candles)
        
        if expected:
            assert len(fvgs) > 0
        else:
            assert len(fvgs) == 0
```

### Testing SMC Components

```python
# tests/unit/test_order_block_detector.py
class TestOrderBlockDetector:
    """Test Order Block detection"""
    
    def test_identify_bullish_ob(self, detector, candles_with_ob):
        """Test bullish order block identification"""
        obs = detector.identify_bullish_ob(candles_with_ob)
        
        assert len(obs) == 1
        assert obs[0]['type'] == 'BULLISH'
        assert obs[0]['quality'] >= 70
    
    def test_ob_volume_requirement(self, detector):
        """Test that OB requires high volume"""
        low_volume_candles = self.create_low_volume_candles()
        obs = detector.identify_bullish_ob(low_volume_candles)
        
        assert len(obs) == 0  # No OB without volume spike
    
    def test_ob_at_round_number(self, detector):
        """Test OB detection at psychological levels"""
        candles_at_2000 = self.create_candles_at_level(2000)
        obs = detector.identify_bullish_ob(candles_at_2000)
        
        assert len(obs) > 0
        assert obs[0]['at_round_number'] == True
```

### Testing Signal Generation

```python
# tests/unit/test_signal_generator.py
class TestSignalGenerator:
    """Test trading signal generation"""
    
    @pytest.fixture
    def generator(self):
        return SignalGenerator()
    
    def test_generate_signal_with_high_confluence(self, generator):
        """Test signal generation with 85% confluence"""
        analysis = {
            'fvg': {'strength': 85, 'type': 'BULLISH'},
            'order_block': {'quality': 80, 'type': 'BULLISH'},
            'structure': {'trend': 'UPTREND'}
        }
        
        signal = generator.evaluate_setup(analysis)
        
        assert signal is not None
        assert signal.direction == 'BUY'
        assert signal.confidence_score >= 0.85
    
    def test_no_signal_with_low_confluence(self, generator):
        """Test that low confluence doesn't generate signal"""
        analysis = {
            'fvg': {'strength': 60, 'type': 'BULLISH'},
            'order_block': None,
            'structure': {'trend': 'RANGING'}
        }
        
        signal = generator.evaluate_setup(analysis)
        assert signal is None
    
    def test_risk_reward_validation(self, generator):
        """Test that signals meet minimum R:R"""
        signal = generator.create_signal({
            'entry': 2045,
            'stop_loss': 2040,
            'take_profit': 2048
        })
        
        # R:R = 3/5 = 0.6 (less than 2:1)
        assert signal is None  # Should reject
```

### Async Testing

```python
# tests/unit/test_telegram_notifier.py
import pytest
import asyncio

class TestTelegramNotifier:
    """Test Telegram notification system"""
    
    @pytest.mark.asyncio
    async def test_send_signal_notification(self, notifier, mock_bot):
        """Test sending signal notification"""
        signal = create_test_signal()
        
        await notifier.broadcast_signal(signal)
        
        mock_bot.send_message.assert_called_once()
        args = mock_bot.send_message.call_args
        assert 'XAUUSD' in args[1]['text']
        assert 'BUY' in args[1]['text']
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, notifier, failing_bot):
        """Test retry logic on send failure"""
        signal = create_test_signal()
        
        with pytest.raises(TelegramError):
            await notifier.broadcast_signal(signal)
        
        # Should have retried 3 times
        assert failing_bot.send_message.call_count == 3
```

---

## Integration Testing

### Database Integration Tests

```python
# tests/integration/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="module")
def test_db():
    """Create test database"""
    engine = create_engine("postgresql://trader:test@localhost:5432/test_db")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

class TestSignalRepository:
    """Test signal database operations"""
    
    def test_create_signal(self, test_db):
        """Test creating signal in database"""
        signal = Signal(
            signal_id="TEST_001",
            instrument="XAUUSD",
            direction="BUY",
            entry_price=2045.50
        )
        
        test_db.add(signal)
        test_db.commit()
        
        retrieved = test_db.query(Signal).filter_by(signal_id="TEST_001").first()
        assert retrieved is not None
        assert retrieved.instrument == "XAUUSD"
    
    def test_query_active_signals(self, test_db):
        """Test querying active signals"""
        # Create test signals
        for i in range(5):
            signal = Signal(signal_id=f"TEST_{i}", status="ACTIVE")
            test_db.add(signal)
        test_db.commit()
        
        active = test_db.query(Signal).filter_by(status="ACTIVE").all()
        assert len(active) == 5
```

### API Integration Tests

```python
# tests/integration/test_api.py
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestSignalsAPI:
    """Test signals API endpoints"""
    
    def test_get_active_signals(self):
        """Test GET /api/v1/signals/active"""
        response = client.get(
            "/api/v1/signals/active",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert isinstance(data["signals"], list)
    
    def test_get_signal_by_id(self):
        """Test GET /api/v1/signals/{id}"""
        response = client.get(
            "/api/v1/signals/TEST_001",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        signal = response.json()
        assert signal["signal_id"] == "TEST_001"
    
    def test_unauthorized_access(self):
        """Test API without authentication"""
        response = client.get("/api/v1/signals/active")
        assert response.status_code == 401
```

### WebSocket Integration Tests

```python
# tests/integration/test_websocket.py
import pytest
import websockets

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection"""
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        # Send authentication
        await websocket.send(json.dumps({
            "type": "auth",
            "token": test_token
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        assert data["type"] == "auth_success"

@pytest.mark.asyncio
async def test_price_tick_subscription():
    """Test subscribing to price ticks"""
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to XAUUSD
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channel": "prices",
            "instrument": "XAUUSD"
        }))
        
        # Wait for price tick
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        data = json.loads(response)
        
        assert data["type"] == "price_tick"
        assert data["data"]["instrument"] == "XAUUSD"
```

---

## Backtesting

### Backtesting Framework

```python
# tests/backtesting/test_strategy.py
import pandas as pd
from src.backtesting.backtest_engine import BacktestEngine

class TestStrategyBacktest:
    """Backtest trading strategy on historical data"""
    
    @pytest.fixture
    def historical_data(self):
        """Load historical XAUUSD data"""
        return pd.read_csv('tests/data/XAUUSD_2023.csv')
    
    def test_backtest_2023(self, historical_data):
        """Backtest strategy on 2023 data"""
        engine = BacktestEngine()
        results = engine.run_backtest(
            data=historical_data,
            start_date='2023-01-01',
            end_date='2023-12-31',
            initial_balance=10000
        )
        
        # Assertions
        assert results['total_trades'] > 0
        assert results['win_rate'] >= 0.50  # At least 50%
        assert results['profit_factor'] >= 1.5
        assert results['max_drawdown'] <= 0.15  # Max 15%
        assert results['final_balance'] > results['initial_balance']
    
    def test_walk_forward_optimization(self, historical_data):
        """Test walk-forward optimization"""
        engine = BacktestEngine()
        
        # Split data into training and testing periods
        train_data = historical_data['2023-01':'2023-06']
        test_data = historical_data['2023-07':'2023-12']
        
        # Optimize on training data
        best_params = engine.optimize(train_data)
        
        # Test on out-of-sample data
        results = engine.run_backtest(test_data, params=best_params)
        
        assert results['win_rate'] >= 0.45  # Should still be profitable
    
    def test_monte_carlo_simulation(self, historical_data):
        """Test Monte Carlo simulation"""
        engine = BacktestEngine()
        
        # Run 1000 simulations
        simulations = engine.monte_carlo(
            data=historical_data,
            num_simulations=1000
        )
        
        # Check confidence intervals
        assert simulations['win_rate_95_ci'][0] >= 0.45
        assert simulations['max_drawdown_95_ci'][1] <= 0.20
```

### Performance Metrics

```python
def calculate_backtest_metrics(trades):
    """Calculate comprehensive backtest metrics"""
    return {
        'total_trades': len(trades),
        'winning_trades': len([t for t in trades if t.profit > 0]),
        'losing_trades': len([t for t in trades if t.profit < 0]),
        'win_rate': calculate_win_rate(trades),
        'profit_factor': calculate_profit_factor(trades),
        'average_rr': calculate_average_rr(trades),
        'max_drawdown': calculate_max_drawdown(trades),
        'sharpe_ratio': calculate_sharpe_ratio(trades),
        'sortino_ratio': calculate_sortino_ratio(trades),
        'calmar_ratio': calculate_calmar_ratio(trades),
        'total_return': calculate_total_return(trades),
        'cagr': calculate_cagr(trades),
        'max_consecutive_wins': calculate_max_streak(trades, 'win'),
        'max_consecutive_losses': calculate_max_streak(trades, 'loss')
    }
```

---

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py
import asyncio
from locust import HttpUser, task, between

class TradingSystemUser(HttpUser):
    """Simulate user load on trading system"""
    wait_time = between(1, 3)
    
    @task(3)
    def get_active_signals(self):
        """Get active signals (most common operation)"""
        self.client.get(
            "/api/v1/signals/active",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def get_performance(self):
        """Get performance metrics"""
        self.client.get(
            "/api/v1/performance/daily",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test",
            "password": "test"
        })
        self.token = response.json()["access_token"]

# Run: locust -f tests/performance/test_load.py --host=http://localhost:8000
```

### Stress Testing

```python
# tests/performance/test_stress.py
import pytest
import asyncio

@pytest.mark.performance
async def test_concurrent_signal_generation():
    """Test system under high signal generation load"""
    async def generate_signals():
        for _ in range(100):
            await signal_generator.evaluate_setup(test_analysis)
    
    # Run 10 concurrent generators
    tasks = [generate_signals() for _ in range(10)]
    
    start_time = time.time()
    await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    # Should handle 1000 signals in under 10 seconds
    assert duration < 10
    
@pytest.mark.performance
def test_database_query_performance():
    """Test database query performance"""
    # Insert 10,000 test signals
    for i in range(10000):
        db.add(Signal(signal_id=f"TEST_{i}"))
    db.commit()
    
    # Query should be fast
    start_time = time.time()
    results = db.query(Signal).filter_by(status="ACTIVE").limit(100).all()
    duration = time.time() - start_time
    
    # Should complete in under 100ms
    assert duration < 0.1
```

---

## Security Testing

### Vulnerability Scanning

```bash
# Scan dependencies for vulnerabilities
safety check

# Scan code for security issues
bandit -r src/

# Check for secrets in code
trufflehog --regex --entropy=False .
```

### Penetration Testing

```python
# tests/security/test_api_security.py
class TestAPISecurity:
    """Test API security"""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection protection"""
        malicious_input = "'; DROP TABLE signals; --"
        
        response = client.get(
            f"/api/v1/signals?instrument={malicious_input}"
        )
        
        # Should not execute SQL injection
        assert response.status_code in [400, 422]  # Bad request
    
    def test_xss_prevention(self):
        """Test XSS protection"""
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post(
            "/api/v1/signals",
            json={"setup_type": xss_payload}
        )
        
        # Should sanitize input
        signal = response.json()
        assert "<script>" not in signal["setup_type"]
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        # Make 101 requests (limit is 100/minute)
        for i in range(101):
            response = client.get("/api/v1/signals/active")
        
        # Last request should be rate limited
        assert response.status_code == 429
```

---

## Test Coverage

### Coverage Goals

- **Overall**: 80%+ coverage
- **Critical paths**: 95%+ coverage
- **SMC algorithms**: 90%+ coverage
- **API endpoints**: 85%+ coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check coverage threshold
pytest --cov=src --cov-fail-under=80
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Test Data Management

### Test Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_candles():
    """Sample candle data"""
    return [
        {'open': 2040, 'high': 2042, 'low': 2038, 'close': 2041, 'volume': 1000},
        {'open': 2041, 'high': 2050, 'low': 2041, 'close': 2049, 'volume': 2500},
        {'open': 2049, 'high': 2051, 'low': 2048, 'close': 2050, 'volume': 1200}
    ]

@pytest.fixture
def test_signal():
    """Sample trading signal"""
    return Signal(
        signal_id="TEST_001",
        instrument="XAUUSD",
        direction="BUY",
        entry_price=2045.50,
        stop_loss=2040.00,
        take_profit_1=2055.00,
        take_profit_2=2065.00
    )
```

### Mock Data Generation

```python
from faker import Faker
import random

fake = Faker()

def generate_test_candles(count=100):
    """Generate realistic test candle data"""
    candles = []
    price = 2000.0
    
    for _ in range(count):
        change = random.uniform(-10, 10)
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.uniform(0, 5)
        low_price = min(open_price, close_price) - random.uniform(0, 5)
        
        candles.append({
            'timestamp': fake.date_time_this_year(),
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': random.randint(500, 3000)
        })
        
        price = close_price
    
    return candles
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-02-05