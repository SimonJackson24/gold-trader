# System Architecture

## Overview

The XAUUSD Gold Trading System is built on a distributed architecture that separates concerns between data acquisition, analysis, and execution. This design ensures scalability, maintainability, and fault tolerance.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Trading System Architecture                  │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐                    ┌──────────────────────────────┐
│  Windows Machine │                    │      Linux VPS Server        │
│                  │                    │                              │
│  ┌────────────┐  │                    │  ┌────────────────────────┐ │
│  │    MT5     │  │                    │  │   Analysis Server      │ │
│  │  Terminal  │  │                    │  │                        │ │
│  └─────┬──────┘  │                    │  │  ┌──────────────────┐ │ │
│        │         │                    │  │  │ Market Data      │ │ │
│  ┌─────▼──────┐  │   WebSocket (WSS)  │  │  │ Processor        │ │ │
│  │ MT5 Bridge │  │◄──────────────────►│  │  └────────┬─────────┘ │ │
│  │  Service   │  │   Real-time Price  │  │           │           │ │
│  └─────┬──────┘  │      Streaming     │  │  ┌────────▼─────────┐ │ │
│        │         │                    │  │  │ SMC Analysis     │ │ │
│  ┌─────▼──────┐  │                    │  │  │ Engine           │ │ │
│  │ WebSocket  │  │                    │  │  │                  │ │ │
│  │   Server   │  │                    │  │  │ - FVG Detector   │ │ │
│  └────────────┘  │                    │  │  │ - Order Blocks   │ │ │
│                  │                    │  │  │ - Liquidity      │ │ │
└──────────────────┘                    │  │  │ - Structure      │ │ │
                                        │  │  └────────┬─────────┘ │ │
                                        │  │           │           │ │
                                        │  │  ┌────────▼─────────┐ │ │
                                        │  │  │ Signal Generator │ │ │
                                        │  │  └────────┬─────────┘ │ │
                                        │  │           │           │ │
                                        │  │  ┌────────▼─────────┐ │ │
                                        │  │  │ Trade Manager    │ │ │
                                        │  │  └────────┬─────────┘ │ │
                                        │  └───────────┼───────────┘ │
                                        │              │             │
                                        │  ┌───────────▼───────────┐ │
                                        │  │   FastAPI Server      │ │
                                        │  │   (REST API)          │ │
                                        │  └───────────┬───────────┘ │
                                        └──────────────┼─────────────┘
                                                       │
                    ┌──────────────────────────────────┼──────────────┐
                    │                                  │              │
           ┌────────▼────────┐              ┌─────────▼────────┐     │
           │   PostgreSQL    │              │  Telegram Bot    │     │
           │    Database     │              │     Service      │     │
           │                 │              │                  │     │
           │ - Signals       │              │ - Notifications  │     │
           │ - Trades        │              │ - Live Updates   │     │
           │ - Performance   │              │ - Reports        │     │
           └─────────────────┘              └──────────────────┘     │
                                                                      │
                                            ┌──────────────────┐     │
                                            │  Redis Cache     │     │
                                            │  - Session Data  │     │
                                            │  - Task Queue    │     │
                                            └──────────────────┘     │
                                                                      │
                                            ┌──────────────────┐     │
                                            │  Prometheus      │     │
                                            │  - Metrics       │     │
                                            └────────┬─────────┘     │
                                                     │                │
                                            ┌────────▼─────────┐     │
                                            │  Grafana         │     │
                                            │  - Dashboards    │     │
                                            └──────────────────┘     │
                                                                      │
                                                       └──────────────┘
```

## Component Details

### 1. MT5 Connector (Windows)

**Purpose**: Acquire real-time price data from MetaTrader 5 and stream it to the analysis server.

**Components**:

#### MT5 Bridge Service
```python
# Responsibilities:
- Connect to MT5 terminal
- Subscribe to XAUUSD symbol
- Handle OnTick events
- Validate and normalize price data
- Buffer data for reliability
```

**Technology**: Python 3.11+ with MetaTrader5 library

**Key Features**:
- Auto-reconnection on MT5 disconnection
- Data validation and sanitization
- Tick buffering (prevents data loss)
- Health monitoring

#### WebSocket Server
```python
# Responsibilities:
- Establish secure WebSocket connections
- Broadcast price data to analysis server
- Handle connection lifecycle
- Implement heartbeat mechanism
```

**Technology**: Python `websockets` library with SSL/TLS

**Protocol**:
```json
{
  "type": "tick",
  "symbol": "XAUUSD",
  "timestamp": "2024-01-05T14:30:00.123Z",
  "bid": 2045.50,
  "ask": 2045.70,
  "last": 2045.60,
  "volume": 100
}
```

### 2. Analysis Server (Linux)

**Purpose**: Core trading logic, signal generation, and trade management.

#### Market Data Processor

```python
class MarketDataProcessor:
    """
    Receives real-time price data and maintains rolling windows
    for multi-timeframe analysis.
    """
    
    def __init__(self):
        self.m15_window = RollingWindow(size=200)  # ~50 hours
        self.h1_window = RollingWindow(size=200)   # ~8 days
        self.h4_window = RollingWindow(size=200)   # ~33 days
        
    async def process_tick(self, tick_data):
        # Update candles
        # Detect candle closes
        # Trigger analysis on new candles
```

**Responsibilities**:
- WebSocket client connection to MT5 connector
- Tick-to-candle aggregation
- Multi-timeframe candle management
- Event emission on candle close

#### SMC Analysis Engine

**Architecture**:
```
┌─────────────────────────────────────────────────────┐
│            SMC Analysis Engine                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐    ┌──────────────────┐     │
│  │  FVG Detector    │    │  Order Block     │     │
│  │                  │    │  Detector        │     │
│  │ - Bullish FVG    │    │                  │     │
│  │ - Bearish FVG    │    │ - Bullish OB     │     │
│  │ - Gap Strength   │    │ - Bearish OB     │     │
│  └────────┬─────────┘    │ - Volume Analysis│     │
│           │              └────────┬─────────┘     │
│           │                       │               │
│  ┌────────▼───────────────────────▼─────────┐    │
│  │      Confluence Analyzer                 │    │
│  │                                          │    │
│  │  - Combines multiple SMC signals        │    │
│  │  - Calculates confidence scores         │    │
│  │  - Validates multi-timeframe alignment  │    │
│  └────────┬─────────────────────────────────┘    │
│           │                                       │
│  ┌────────▼─────────┐    ┌──────────────────┐   │
│  │ Liquidity        │    │ Market Structure │   │
│  │ Analyzer         │    │ Analyzer         │   │
│  │                  │    │                  │   │
│  │ - Sweep Detection│    │ - BOS Detection  │   │
│  │ - Pool Mapping   │    │ - CHoCH Detection│   │
│  └──────────────────┘    │ - Trend Analysis │   │
│                          └──────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Key Algorithms**:

1. **Fair Value Gap Detection**
```python
def detect_fvg(candles):
    """
    Bullish FVG: candle[i-1].high < candle[i+1].low
    Bearish FVG: candle[i-1].low > candle[i+1].high
    
    Returns: List of FVG zones with strength scores
    """
```

2. **Order Block Identification**
```python
def identify_order_block(candles, volume_data):
    """
    Criteria:
    - Last opposite candle before strong move
    - High volume (>2x average)
    - Strong rejection (wick >60% of range)
    - Near round numbers (psychological levels)
    
    Returns: Order block zones with institutional probability
    """
```

3. **Liquidity Sweep Detection**
```python
def detect_liquidity_sweep(price_data, swing_points):
    """
    Identifies:
    - Stop hunts above/below swing points
    - Quick reversals after sweep
    - Volume spikes during sweep
    
    Returns: Sweep events with reversal probability
    """
```

4. **Market Structure Analysis**
```python
def analyze_market_structure(swing_highs, swing_lows):
    """
    Determines:
    - Break of Structure (BOS) - trend continuation
    - Change of Character (CHoCH) - potential reversal
    - Trend direction and strength
    
    Returns: Structure state and trend bias
    """
```

#### Signal Generator

```python
class SignalGenerator:
    """
    Synthesizes SMC analysis into actionable trading signals.
    """
    
    def evaluate_setup(self, analysis_results):
        # Multi-timeframe confluence check
        confluence_score = self.calculate_confluence(analysis_results)
        
        if confluence_score >= 80:  # High probability setup
            signal = self.create_signal(analysis_results)
            return signal
        
        return None
    
    def calculate_confluence(self, analysis):
        """
        Scoring system:
        - H4 trend alignment: 40 points
        - H1 setup quality: 35 points
        - M15 entry precision: 25 points
        """
```

**Signal Structure**:
```python
@dataclass
class TradingSignal:
    signal_id: str
    instrument: str = "XAUUSD"
    direction: Literal["BUY", "SELL"]
    
    # Price levels
    entry_price: float
    stop_loss: float
    take_profit_1: float  # 50% position
    take_profit_2: float  # 50% position
    
    # Risk metrics
    risk_reward_ratio: float
    position_size: float
    risk_percentage: float
    
    # SMC context
    setup_type: str  # "FVG+OB", "LIQUIDITY_SWEEP", etc.
    market_structure: str  # "BOS", "CHoCH"
    confluence_factors: List[str]
    confidence_score: float  # 0-100
    
    # Timeframe analysis
    h4_context: str
    h1_context: str
    m15_context: str
    
    # Metadata
    timestamp: datetime
    session: str  # "ASIAN", "LONDON", "NY_OVERLAP"
```

#### Trade Manager

```python
class TradeManager:
    """
    Manages active trades and monitors progress.
    """
    
    async def open_trade(self, signal: TradingSignal):
        # Record trade in database
        # Start monitoring price movement
        # Set up partial profit targets
        
    async def monitor_trades(self):
        # Check price against TP/SL levels
        # Update Telegram with progress
        # Execute partial closes
        # Move stop to breakeven
        
    async def close_trade(self, trade_id, reason):
        # Calculate P/L
        # Update database
        # Send final notification
        # Update performance metrics
```

**Trade Lifecycle**:
```
SIGNAL_GENERATED → TRADE_OPENED → MONITORING
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                TP1_HIT          TP2_HIT           SL_HIT
                    │                 │                 │
              PARTIAL_CLOSE      FULL_CLOSE       FULL_CLOSE
                    │                 │                 │
              MOVE_SL_TO_BE      TRADE_CLOSED    TRADE_CLOSED
                    │
              CONTINUE_MONITORING
                    │
                TP2_HIT
                    │
              FULL_CLOSE
                    │
              TRADE_CLOSED
```

### 3. Database Layer (PostgreSQL)

**Schema Design**:

```sql
-- Signals table
CREATE TABLE signals (
    signal_id VARCHAR(50) PRIMARY KEY,
    instrument VARCHAR(20) NOT NULL,
    direction VARCHAR(4) NOT NULL,
    entry_price DECIMAL(10, 5) NOT NULL,
    stop_loss DECIMAL(10, 5) NOT NULL,
    take_profit_1 DECIMAL(10, 5),
    take_profit_2 DECIMAL(10, 5),
    risk_reward_ratio DECIMAL(5, 2),
    setup_type VARCHAR(100),
    market_structure VARCHAR(50),
    confidence_score DECIMAL(3, 2),
    session VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    INDEX idx_instrument_status (instrument, status),
    INDEX idx_created_at (created_at)
);

-- Trades table
CREATE TABLE trades (
    trade_id SERIAL PRIMARY KEY,
    signal_id VARCHAR(50) REFERENCES signals(signal_id),
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    entry_price DECIMAL(10, 5),
    exit_price DECIMAL(10, 5),
    profit_loss DECIMAL(10, 2),
    profit_loss_pips DECIMAL(8, 2),
    status VARCHAR(20),
    partial_closes JSONB,
    INDEX idx_signal_id (signal_id),
    INDEX idx_status (status),
    INDEX idx_entry_time (entry_time)
);

-- Performance metrics
CREATE TABLE performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    instrument VARCHAR(20),
    date DATE,
    total_signals INT,
    winning_trades INT,
    losing_trades INT,
    win_rate DECIMAL(5, 2),
    average_rr DECIMAL(5, 2),
    total_pips DECIMAL(10, 2),
    total_profit_loss DECIMAL(12, 2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_instrument_date (instrument, date)
);

-- Price history (for backtesting)
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    instrument VARCHAR(20),
    timeframe VARCHAR(10),
    timestamp TIMESTAMP,
    open DECIMAL(10, 5),
    high DECIMAL(10, 5),
    low DECIMAL(10, 5),
    close DECIMAL(10, 5),
    volume BIGINT,
    INDEX idx_instrument_timeframe_timestamp (instrument, timeframe, timestamp)
);
```

### 4. Communication Layer

#### WebSocket Protocol

**Connection Flow**:
```
MT5 Connector                    Analysis Server
     │                                  │
     │──── Connect (WSS) ──────────────►│
     │                                  │
     │◄─── Connection Accepted ─────────│
     │                                  │
     │──── Authentication Token ───────►│
     │                                  │
     │◄─── Auth Success ────────────────│
     │                                  │
     │──── Heartbeat (every 30s) ──────►│
     │                                  │
     │◄─── Heartbeat ACK ───────────────│
     │                                  │
     │──── Price Tick ─────────────────►│
     │──── Price Tick ─────────────────►│
     │──── Price Tick ─────────────────►│
     │                                  │
```

**Message Types**:
```json
// Tick data
{
  "type": "tick",
  "symbol": "XAUUSD",
  "timestamp": "2024-01-05T14:30:00.123Z",
  "bid": 2045.50,
  "ask": 2045.70,
  "last": 2045.60,
  "volume": 100
}

// Heartbeat
{
  "type": "heartbeat",
  "timestamp": "2024-01-05T14:30:00.000Z"
}

// Error
{
  "type": "error",
  "code": "MT5_DISCONNECTED",
  "message": "Lost connection to MT5 terminal",
  "timestamp": "2024-01-05T14:30:00.000Z"
}
```

#### REST API

**Endpoints**:
```
GET  /api/v1/health              - System health check
GET  /api/v1/signals/active      - Get active signals
GET  /api/v1/signals/{id}        - Get signal details
GET  /api/v1/trades/active       - Get active trades
GET  /api/v1/trades/{id}         - Get trade details
GET  /api/v1/performance/daily   - Daily performance
GET  /api/v1/performance/weekly  - Weekly performance
GET  /api/v1/performance/monthly - Monthly performance
POST /api/v1/config/update       - Update configuration
```

### 5. Notification System (Telegram)

**Architecture**:
```python
class TelegramNotifier:
    """
    Handles all Telegram communications.
    """
    
    async def broadcast_signal(self, signal: TradingSignal):
        # Format rich message with emojis
        # Include chart screenshot
        # Send to channel
        # Store message_id for updates
        
    async def update_trade_progress(self, trade_id, current_price):
        # Calculate current P/L
        # Update progress bar
        # Edit original message
        
    async def send_daily_report(self):
        # Aggregate daily statistics
        # Format performance report
        # Send to channel
```

**Message Format**:
```
🔔 XAUUSD TRADING SIGNAL 🔔

📊 Setup Type: FVG + Order Block Confluence
📈 Direction: BUY
💰 Entry: 2,045.50
🛑 Stop Loss: 2,040.00 (-55 pips)
🎯 TP1: 2,055.00 (+95 pips) [50%]
🎯 TP2: 2,065.00 (+195 pips) [50%]
⚖️ Risk:Reward: 1:3.5

Market Context:
✅ Bullish FVG at 2,043-2,046
✅ Strong bullish order block at 2,042
✅ Market structure: Higher High confirmed
✅ Liquidity sweep below 2,040 completed
✅ Institutional buying pressure detected

Risk Management:
💼 Position Size: 0.5 lots
📉 Risk: 1% of account
🎲 Confidence: 85%

Signal ID: XAU_20240105_001
⏰ Time: 2024-01-05 14:30:00 UTC
📊 Session: LONDON

---
📊 LIVE UPDATES 📊
Progress: [████░░░░░░] 40%
Current P/L: +$125.00 (+25 pips)
```

## Data Flow

### Signal Generation Flow

```
1. MT5 Tick Event
   │
   ▼
2. MT5 Bridge captures tick
   │
   ▼
3. WebSocket broadcasts to Analysis Server
   │
   ▼
4. Market Data Processor aggregates to candles
   │
   ▼
5. On candle close, trigger SMC Analysis
   │
   ├─► FVG Detector
   ├─► Order Block Detector
   ├─► Liquidity Analyzer
   ├─► Market Structure Analyzer
   │
   ▼
6. Confluence Analyzer synthesizes results
   │
   ▼
7. Signal Generator evaluates setup
   │
   ├─► If confluence >= 80%
   │   │
   │   ▼
   │   Generate Trading Signal
   │   │
   │   ├─► Save to Database
   │   ├─► Send Telegram Notification
   │   └─► Open Trade (Trade Manager)
   │
   └─► If confluence < 80%
       │
       ▼
       Continue monitoring
```

### Trade Management Flow

```
1. Trade Opened
   │
   ▼
2. Monitor price in real-time
   │
   ├─► Price reaches TP1
   │   │
   │   ├─► Close 50% position
   │   ├─► Move SL to breakeven
   │   ├─► Update Telegram
   │   └─► Continue monitoring
   │
   ├─► Price reaches TP2
   │   │
   │   ├─► Close remaining 50%
   │   ├─► Update Telegram
   │   ├─► Calculate final P/L
   │   └─► Update performance metrics
   │
   └─► Price hits SL
       │
       ├─► Close full position
       ├─► Update Telegram
       ├─► Calculate final P/L
       └─► Update performance metrics
```

## Scalability Considerations

### Horizontal Scaling

```
┌─────────────────────────────────────────────────┐
│         Load Balancer (Nginx)                   │
└────────────┬────────────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│Analysis│ │Analysis│ │Analysis│
│Server 1│ │Server 2│ │Server 3│
└────────┘ └────────┘ └────────┘
    │        │        │
    └────────┼────────┘
             │
    ┌────────▼────────┐
    │   PostgreSQL    │
    │   (Primary)     │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │   PostgreSQL    │
    │   (Replica)     │
    └─────────────────┘
```

### Multi-Instrument Architecture

```
┌─────────────────────────────────────────────────┐
│         Instrument Factory                      │
└────────┬────────────────────────────────────────┘
         │
    ┌────┼────┬────┬────┐
    │    │    │    │    │
    ▼    ▼    ▼    ▼    ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│XAUUSD  │ │GBPUSD  │ │EURUSD  │ │USDCAD  │
│Trader  │ │Trader  │ │Trader  │ │Trader  │
│Instance│ │Instance│ │Instance│ │Instance│
└────────┘ └────────┘ └────────┘ └────────┘
    │         │         │         │
    ▼         ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Channel │ │Channel │ │Channel │ │Channel │
│ XAU    │ │ GBP    │ │ EUR    │ │ CAD    │
└────────┘ └────────┘ └────────┘ └────────┘
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────┐
│              Security Layers                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. WebSocket Authentication                   │
│     - JWT tokens                               │
│     - Token rotation every 24h                 │
│                                                 │
│  2. API Authentication                         │
│     - API keys with rate limiting              │
│     - IP whitelisting                          │
│                                                 │
│  3. Database Security                          │
│     - SSL/TLS connections                      │
│     - Encrypted credentials                    │
│     - Connection pooling                       │
│                                                 │
│  4. Telegram Bot Security                      │
│     - Bot token encryption                     │
│     - Channel ID validation                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Monitoring & Observability

### Metrics Collection

```
Application Metrics (Prometheus)
├── Trading Metrics
│   ├── signals_generated_total
│   ├── trades_opened_total
│   ├── trades_closed_total
│   ├── win_rate_percentage
│   └── average_risk_reward
│
├── System Metrics
│   ├── websocket_connections_active
│   ├── api_requests_total
│   ├── database_queries_duration
│   └── memory_usage_bytes
│
└── Business Metrics
    ├── daily_pips_total
    ├── daily_profit_loss
    └── active_trades_count
```

### Logging Strategy

```python
# Structured logging with context
logger.info(
    "signal_generated",
    signal_id="XAU_20240105_001",
    instrument="XAUUSD",
    direction="BUY",
    confidence=85,
    setup_type="FVG+OB"
)
```

## Deployment Architecture

### Docker Compose Stack

```yaml
services:
  analysis-server:
    - FastAPI application
    - SMC analysis engine
    - Signal generator
    - Trade manager
    
  postgres:
    - Primary database
    - Persistent volume
    
  redis:
    - Cache layer
    - Task queue
    
  prometheus:
    - Metrics collection
    
  grafana:
    - Visualization dashboards
    
  nginx:
    - Reverse proxy
    - SSL termination
```

## Performance Characteristics

### Latency Targets

- **Tick to Analysis**: < 100ms
- **Signal Generation**: < 500ms
- **Telegram Notification**: < 2s
- **API Response**: < 200ms
- **Database Query**: < 50ms

### Throughput

- **Ticks per second**: 10-50 (XAUUSD typical)
- **Concurrent trades**: Up to 5 per instrument
- **API requests**: 100 req/s
- **WebSocket connections**: 10 concurrent

## Disaster Recovery

### Backup Strategy

```
Daily Backups:
├── Database (PostgreSQL)
│   ├── Full backup at 00:00 UTC
│   └── Retention: 30 days
│
├── Configuration Files
│   ├── Backup on change
│   └── Version controlled
│
└── Trade History
    ├── Incremental backup every 6h
    └── Retention: 90 days
```

### Failover Procedures

1. **MT5 Connector Failure**
   - Auto-restart service
   - Alert via Telegram
   - Fallback to backup connector

2. **Analysis Server Failure**
   - Health check every 30s
   - Auto-restart container
   - Load balancer redirects traffic

3. **Database Failure**
   - Automatic failover to replica
   - Alert administrators
   - Restore from backup if needed

## Future Enhancements

### Planned Architecture Changes

1. **Microservices Migration**
   - Separate services for each SMC component
   - Event-driven architecture with message queue
   - Independent scaling per service

2. **Machine Learning Integration**
   - ML model for signal confidence scoring
   - Pattern recognition enhancement
   - Adaptive parameter tuning

3. **Multi-Region Deployment**
   - Geographic distribution for low latency
   - Regional failover
   - Data replication across regions

4. **Advanced Analytics**
   - Real-time performance dashboards
   - Predictive analytics
   - A/B testing framework for strategies

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-02-05