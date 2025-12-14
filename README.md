# XAUUSD Gold Trading System

A sophisticated automated trading system for XAUUSD (Gold) that implements Smart Money Concepts analysis, real-time market data processing, and intelligent trade execution.

## 🚀 Features

- **Smart Money Concepts Analysis**: Advanced market structure analysis including order blocks, liquidity zones, and fair value gaps
- **Real-time Market Data**: WebSocket-based tick data processing with multiple timeframe support
- **Intelligent Signal Generation**: AI-powered trading signals with confidence scoring
- **Automated Trade Management**: Risk-managed trade execution with MT5 integration
- **Telegram Notifications**: Real-time alerts and trade updates via Telegram bot
- **REST API**: Comprehensive API for system integration and monitoring
- **Health Monitoring**: System health checks and metrics collection
- **Docker Support**: Containerized deployment with orchestration

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Contributing](#contributing)

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- MetaTrader 5 (for trading execution)
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/xauusd-trading-system.git
   cd xauusd-trading-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

### Docker Setup

1. **Build and start services**
   ```bash
   docker-compose up -d
   ```

2. **Initialize database**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/gold_trader
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-here

# WebSocket Configuration
WS_HOST=0.0.0.0
WS_PORT=8001
WS_HEARTBEAT_INTERVAL=30

# MT5 Configuration
MT5_LOGIN=your-mt5-login
MT5_PASSWORD=your-mt5-password
MT5_SERVER=your-mt5-server

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_ADMIN_ID=your-telegram-user-id

# Trading Configuration
DEFAULT_SYMBOL=XAUUSD
DEFAULT_TIMEFRAME=M15
MAX_POSITION_SIZE=0.1
RISK_PER_TRADE=0.02

# Smart Money Concepts
ORDER_BLOCK_MIN_STRENGTH=0.7
LIQUIDITY_ZONE_MIN_SIZE=5
FVG_MIN_SIZE=0.5

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading.log
JSON_LOGS=false
```

### Advanced Configuration

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration options.

## 🚀 Quick Start

### Running the Application

1. **Development mode**
   ```bash
   python main.py --reload
   ```

2. **Production mode**
   ```bash
   python main.py --host 0.0.0.0 --port 8000
   ```

3. **Docker mode**
   ```bash
   docker-compose up -d
   ```

### First Run

1. **Start the system**
   ```bash
   python main.py
   ```

2. **Verify health**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check API status**
   ```bash
   curl -H "Authorization: Bearer your-secret-key" \
        http://localhost:8000/status
   ```

4. **Test Telegram bot**
   - Send `/start` to your bot
   - Check for welcome message

## 📚 API Documentation

### Authentication

All API endpoints (except `/health`) require Bearer token authentication:

```http
Authorization: Bearer your-secret-key
```

### Main Endpoints

#### Health Checks
- `GET /health` - Basic health check (no auth required)
- `GET /status` - System status with authentication

#### Signals
- `GET /signals` - Get recent trading signals
- `POST /signals` - Create new trading signal
- `GET /signals/{signal_id}` - Get specific signal

#### Trades
- `GET /trades` - Get recent trades
- `POST /trades` - Create new trade
- `GET /trades/{trade_id}` - Get specific trade

#### Market Data
- `GET /market/ticks` - Get recent tick data
- `GET /market/candles` - Get candle data

#### Account
- `GET /account/balance` - Get account balance
- `GET /account/positions` - Get open positions

#### Analysis
- `POST /analysis/smart-money` - Perform Smart Money analysis

#### WebSocket
- `POST /websocket/subscribe` - Subscribe to WebSocket channels

### Example API Usage

```python
import requests

# Get signals
headers = {"Authorization": "Bearer your-secret-key"}
response = requests.get("http://localhost:8000/signals", headers=headers)
signals = response.json()

# Create signal
signal_data = {
    "symbol": "XAUUSD",
    "signal_type": "BUY",
    "entry_price": "1950.50",
    "stop_loss": "1948.00",
    "take_profit": "1955.00",
    "confidence": 0.85,
    "reasoning": "Smart Money analysis"
}
response = requests.post(
    "http://localhost:8000/signals",
    json=signal_data,
    headers=headers
)
```

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MT5 Terminal │    │  Trading API    │    │  Telegram Bot   │
│   (Connector)  │◄──►│   (FastAPI)     │◄──►│  (Notifier)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Market Data   │    │   Signal Gen    │    │   Trade Mgr    │
│  Processor     │◄──►│   (Smart Money) │◄──►│   (Risk Mgmt)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WebSocket    │    │   Database       │    │   Monitoring     │
│   Server       │    │  (PostgreSQL)    │    │   (Health/Met)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Market Data Ingestion**: Real-time tick data from MT5
2. **Smart Money Analysis**: Identify market structures and patterns
3. **Signal Generation**: Create trading signals with confidence scores
4. **Risk Management**: Validate signals and calculate position sizes
5. **Trade Execution**: Send orders to MT5 terminal
6. **Notification**: Alert users via Telegram bot
7. **Monitoring**: Track system health and performance

### Smart Money Concepts

The system implements several Smart Money Concepts:

- **Order Blocks**: Identify large institutional orders
- **Liquidity Zones**: Detect areas of high liquidity
- **Fair Value Gaps (FVG)**: Find price inefficiencies
- **Market Structure**: Analyze trend and consolidation phases
- **Volume Profile**: Understand buying/selling pressure

## 🛠️ Development

### Project Structure

```
xauusd-trading-system/
├── src/                    # Source code
│   ├── api/               # REST API
│   ├── connectors/         # External system connectors
│   ├── models/             # Data models
│   ├── smart_money/         # Smart Money analysis
│   ├── signal_generator/    # Signal generation logic
│   ├── trade_manager/       # Trade execution
│   ├── market_data/        # Market data processing
│   ├── notifications/       # Notification services
│   ├── monitoring/          # Health & metrics
│   ├── database/           # Database layer
│   └── config.py           # Configuration
├── tests/                  # Test suite
├── docs/                   # Documentation
├── nginx/                  # Nginx configuration
├── monitoring/              # Monitoring configs
├── docker-compose.yml        # Docker orchestration
├── Dockerfile              # Container definition
├── requirements.txt         # Dependencies
└── main.py                # Application entry
```

### Development Workflow

1. **Feature Development**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   ```

2. **Testing**
   ```bash
   pytest tests/ -v --cov=src
   ```

3. **Code Quality**
   ```bash
   flake8 src/
   black src/
   isort src/
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

### Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **Type Hints**: All functions should have type hints
- **Documentation**: Docstrings for all public functions
- **Testing**: Minimum 80% test coverage required

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/ -m unit

# Integration tests
pytest tests/ -m integration

# API tests
pytest tests/ -m api

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Structure

```
tests/
├── conftest.py            # Test configuration
├── test_models.py          # Model tests
├── test_api.py             # API tests
├── test_smart_money.py     # Smart Money tests
├── test_trade_manager.py    # Trade manager tests
└── test_integration.py     # Integration tests
```

### Mock Data

Test fixtures provide sample data for testing:

- Sample ticks, candles, signals, trades
- Mock MT5 responses
- Test market scenarios

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Set production environment variables
   export DATABASE_URL=postgresql://prod_user:prod_pass@db:5432/gold_trader
   export API_SECRET_KEY=production-secret-key
   ```

2. **Docker Deployment**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Health Check**
   ```bash
   curl https://your-domain.com/health
   ```

### Monitoring Setup

1. **Prometheus**: Metrics collection on port 9090
2. **Grafana**: Visualization on port 3000
3. **ELK Stack**: Log aggregation (optional)

### SSL Configuration

1. **Generate certificates**
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
   ```

2. **Configure Nginx**
   ```bash
   cp key.pem nginx/ssl/
   cp cert.pem nginx/ssl/
   ```

## 📊 Monitoring

### Health Checks

System health is monitored via:

- **Database Connectivity**: PostgreSQL connection status
- **Redis Connectivity**: Cache connection status
- **MT5 Connection**: Trading terminal status
- **WebSocket Server**: Real-time data server status
- **System Resources**: CPU, memory, disk usage

### Metrics

Key metrics collected:

- **Trading Metrics**: Signals generated, trades executed, P&L
- **Performance Metrics**: API response times, processing delays
- **System Metrics**: Resource utilization, error rates
- **Business Metrics**: Win rate, average profit, risk metrics

### Alerts

The system provides alerts for:

- **System Failures**: Service downtime, connection issues
- **Trading Errors**: Failed executions, risk breaches
- **Performance Issues**: Slow responses, high latency
- **Business Events**: Large losses, unusual patterns

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL in .env
   - Verify PostgreSQL is running
   - Check network connectivity

2. **MT5 Connection Issues**
   - Verify MT5 terminal is running
   - Check login credentials
   - Ensure MT5 allows DLL imports

3. **Telegram Bot Not Responding**
   - Verify BOT_TOKEN is correct
   - Check bot is running and has permissions
   - Test with `/start` command

4. **High Memory Usage**
   - Reduce data retention periods
   - Optimize database queries
   - Increase system memory

### Debug Mode

Enable debug logging:

```bash
python main.py --log-level DEBUG
```

### Log Analysis

Check application logs:

```bash
# Application logs
tail -f logs/trading.log

# Error logs
tail -f logs/error.log

# Trading logs
tail -f logs/trading.log
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Process

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Submit pull request

### Code Review Standards

- **Functionality**: Code works as intended
- **Testing**: Adequate test coverage
- **Documentation**: Clear docstrings and comments
- **Performance**: No performance regressions
- **Security**: No security vulnerabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/xauusd-trading-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/xauusd-trading-system/discussions)

## 🙏 Acknowledgments

- **Smart Money Concepts**: Based on ICT (Inner Circle Trader) methodology
- **Technical Analysis**: Traditional and modern analysis techniques
- **Open Source**: Built with open-source tools and libraries

---

**⚠️ Risk Warning**: Forex trading involves substantial risk of loss. This system is for educational and demonstration purposes. Always test thoroughly before deploying with real funds.

**📈 Performance Disclaimer**: Past performance does not guarantee future results. Market conditions change rapidly.