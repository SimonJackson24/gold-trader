# API Specification

Complete REST API documentation for the XAUUSD Gold Trading System.

## Base URL

```
Production: https://api.yourdomain.com/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

All API endpoints (except health check) require authentication using API keys or JWT tokens.

### API Key Authentication

```http
GET /api/v1/signals/active
X-API-Key: your_api_key_here
```

### JWT Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}

# Use token in subsequent requests
GET /api/v1/signals/active
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Endpoints

### Health & Status

#### GET /health

Check system health status.

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-05T14:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "mt5_connector": "connected",
    "telegram": "connected"
  },
  "uptime_seconds": 86400
}
```

**Status Codes:**
- `200 OK`: System healthy
- `503 Service Unavailable`: System unhealthy

---

### Signals

#### GET /signals/active

Get all currently active trading signals.

**Authentication:** Required

**Query Parameters:**
- `instrument` (optional): Filter by instrument (e.g., "XAUUSD")
- `limit` (optional): Number of results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Request:**
```http
GET /api/v1/signals/active?instrument=XAUUSD&limit=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "signals": [
    {
      "signal_id": "XAU_20240105_001",
      "instrument": "XAUUSD",
      "direction": "BUY",
      "entry_price": 2045.50,
      "stop_loss": 2040.00,
      "take_profit_1": 2055.00,
      "take_profit_2": 2065.00,
      "risk_reward_ratio": 3.5,
      "setup_type": "FVG + Order Block",
      "market_structure": "BOS",
      "confidence_score": 0.85,
      "session": "LONDON",
      "created_at": "2024-01-05T14:30:00Z",
      "status": "ACTIVE",
      "confluence_factors": [
        "Bullish FVG at 2043-2046",
        "Strong order block at 2042",
        "Liquidity sweep completed"
      ]
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Invalid or missing authentication
- `500 Internal Server Error`: Server error

---

#### GET /signals/{signal_id}

Get details of a specific signal.

**Authentication:** Required

**Path Parameters:**
- `signal_id`: Signal identifier

**Request:**
```http
GET /api/v1/signals/XAU_20240105_001
Authorization: Bearer <token>
```

**Response:**
```json
{
  "signal_id": "XAU_20240105_001",
  "instrument": "XAUUSD",
  "direction": "BUY",
  "entry_price": 2045.50,
  "stop_loss": 2040.00,
  "take_profit_1": 2055.00,
  "take_profit_2": 2065.00,
  "risk_reward_ratio": 3.5,
  "position_size": 0.50,
  "risk_percentage": 1.0,
  "setup_type": "FVG + Order Block",
  "market_structure": "BOS",
  "confidence_score": 0.85,
  "h4_context": "Uptrend confirmed, HH and HL pattern",
  "h1_context": "Bullish order block at 2042, FVG zone 2043-2046",
  "m15_context": "Price retracing to OB, waiting for rejection",
  "session": "LONDON",
  "created_at": "2024-01-05T14:30:00Z",
  "updated_at": "2024-01-05T14:30:00Z",
  "status": "ACTIVE",
  "telegram_message_id": 123456789,
  "trade": {
    "trade_id": 1,
    "entry_time": "2024-01-05T14:35:00Z",
    "status": "OPEN",
    "current_price": 2048.00,
    "profit_loss": 125.00,
    "profit_loss_pips": 25.0
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Signal not found
- `401 Unauthorized`: Invalid authentication

---

#### POST /signals

Create a new trading signal (manual override).

**Authentication:** Required (Admin only)

**Request Body:**
```json
{
  "instrument": "XAUUSD",
  "direction": "BUY",
  "entry_price": 2045.50,
  "stop_loss": 2040.00,
  "take_profit_1": 2055.00,
  "take_profit_2": 2065.00,
  "setup_type": "Manual Entry",
  "confidence_score": 0.80,
  "notes": "Manual signal based on fundamental analysis"
}
```

**Response:**
```json
{
  "signal_id": "XAU_20240105_002",
  "status": "created",
  "message": "Signal created successfully"
}
```

**Status Codes:**
- `201 Created`: Signal created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Insufficient permissions

---

### Trades

#### GET /trades/active

Get all currently active trades.

**Authentication:** Required

**Query Parameters:**
- `instrument` (optional): Filter by instrument
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "trades": [
    {
      "trade_id": 1,
      "signal_id": "XAU_20240105_001",
      "instrument": "XAUUSD",
      "direction": "BUY",
      "entry_time": "2024-01-05T14:35:00Z",
      "entry_price": 2045.50,
      "stop_loss": 2040.00,
      "take_profit_1": 2055.00,
      "take_profit_2": 2065.00,
      "position_size": 0.50,
      "current_price": 2048.00,
      "profit_loss": 125.00,
      "profit_loss_pips": 25.0,
      "status": "OPEN",
      "tp1_hit": false,
      "tp2_hit": false,
      "breakeven_moved": false
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

#### GET /trades/{trade_id}

Get details of a specific trade.

**Authentication:** Required

**Response:**
```json
{
  "trade_id": 1,
  "signal_id": "XAU_20240105_001",
  "entry_time": "2024-01-05T14:35:00Z",
  "exit_time": "2024-01-05T16:20:00Z",
  "duration_minutes": 105,
  "entry_price": 2045.50,
  "exit_price": 2055.00,
  "highest_price": 2056.20,
  "lowest_price": 2044.80,
  "profit_loss": 475.00,
  "profit_loss_pips": 95.0,
  "profit_loss_percentage": 4.75,
  "position_size": 0.50,
  "status": "CLOSED",
  "partial_closes": [
    {
      "time": "2024-01-05T15:45:00",
      "price": 2055.00,
      "size": 0.25,
      "profit": 237.50
    }
  ],
  "tp1_hit": true,
  "tp2_hit": true,
  "exit_reason": "TP2_HIT"
}
```

---

#### POST /trades/{trade_id}/close

Manually close a trade.

**Authentication:** Required (Admin only)

**Request Body:**
```json
{
  "reason": "Manual close",
  "percentage": 100
}
```

**Response:**
```json
{
  "trade_id": 1,
  "status": "closed",
  "exit_price": 2048.00,
  "profit_loss": 125.00,
  "message": "Trade closed successfully"
}
```

---

### Performance

#### GET /performance/daily

Get daily performance metrics.

**Authentication:** Required

**Query Parameters:**
- `instrument` (optional): Filter by instrument
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Number of days (default: 30)

**Response:**
```json
{
  "metrics": [
    {
      "date": "2024-01-05",
      "instrument": "XAUUSD",
      "total_signals": 5,
      "total_trades": 4,
      "winning_trades": 3,
      "losing_trades": 1,
      "win_rate": 75.00,
      "average_rr": 2.80,
      "total_pips": 185.50,
      "total_profit_loss": 927.50,
      "largest_win": 475.00,
      "largest_loss": -55.00
    }
  ],
  "summary": {
    "total_days": 1,
    "average_win_rate": 75.00,
    "total_profit_loss": 927.50,
    "total_pips": 185.50
  }
}
```

---

#### GET /performance/weekly

Get weekly performance metrics.

**Response:**
```json
{
  "metrics": [
    {
      "week_start": "2024-01-01",
      "week_end": "2024-01-07",
      "instrument": "XAUUSD",
      "total_trades": 20,
      "winning_trades": 13,
      "losing_trades": 7,
      "win_rate": 65.00,
      "average_rr": 2.90,
      "total_pips": 580.00,
      "total_profit_loss": 2900.00
    }
  ]
}
```

---

#### GET /performance/monthly

Get monthly performance metrics.

**Response:**
```json
{
  "metrics": [
    {
      "month": "2024-01",
      "instrument": "XAUUSD",
      "total_trades": 85,
      "winning_trades": 52,
      "losing_trades": 33,
      "win_rate": 61.18,
      "average_rr": 2.85,
      "total_pips": 2340.00,
      "total_profit_loss": 11700.00,
      "max_drawdown": -450.00,
      "sharpe_ratio": 2.15
    }
  ]
}
```

---

### Configuration

#### GET /config

Get current system configuration.

**Authentication:** Required (Admin only)

**Response:**
```json
{
  "trading": {
    "risk_per_trade": 1.0,
    "max_concurrent_trades": 2,
    "min_risk_reward": 2.0
  },
  "smc_parameters": {
    "fvg_min_size_pips": 5,
    "ob_lookback_candles": 20,
    "confluence_threshold": 80
  },
  "sessions": {
    "asian": {
      "start": "00:00",
      "end": "08:00",
      "risk_multiplier": 0.5
    },
    "london": {
      "start": "08:00",
      "end": "13:00",
      "risk_multiplier": 1.0
    },
    "ny": {
      "start": "13:00",
      "end": "17:00",
      "risk_multiplier": 1.5
    }
  }
}
```

---

#### PUT /config

Update system configuration.

**Authentication:** Required (Admin only)

**Request Body:**
```json
{
  "risk_per_trade": 1.5,
  "max_concurrent_trades": 3
}
```

**Response:**
```json
{
  "status": "updated",
  "message": "Configuration updated successfully",
  "updated_fields": ["risk_per_trade", "max_concurrent_trades"]
}
```

---

### System

#### GET /system/status

Get detailed system status.

**Authentication:** Required

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2024-01-05T14:30:00Z",
  "services": {
    "mt5_connector": {
      "status": "connected",
      "last_tick": "2024-01-05T14:29:58Z",
      "symbols": ["XAUUSD"]
    },
    "database": {
      "status": "connected",
      "connections": 5,
      "pool_size": 20
    },
    "redis": {
      "status": "connected",
      "memory_used": "2.5MB"
    },
    "telegram": {
      "status": "connected",
      "last_message": "2024-01-05T14:25:00Z"
    }
  },
  "active_trades": 2,
  "pending_signals": 1,
  "system_load": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 30.1
  }
}
```

---

#### POST /system/restart

Restart system components.

**Authentication:** Required (Admin only)

**Request Body:**
```json
{
  "component": "analysis-server",
  "reason": "Configuration update"
}
```

**Response:**
```json
{
  "status": "restarting",
  "component": "analysis-server",
  "estimated_downtime_seconds": 30
}
```

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('wss://api.yourdomain.com/ws');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token'
  }));
};
```

### Subscribe to Events

```javascript
// Subscribe to signal events
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'signals',
  instrument: 'XAUUSD'
}));

// Subscribe to trade updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'trades'
}));

// Subscribe to price updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'prices',
  instrument: 'XAUUSD'
}));
```

### Event Messages

#### New Signal Event
```json
{
  "type": "signal_created",
  "timestamp": "2024-01-05T14:30:00Z",
  "data": {
    "signal_id": "XAU_20240105_001",
    "instrument": "XAUUSD",
    "direction": "BUY",
    "entry_price": 2045.50,
    "confidence_score": 0.85
  }
}
```

#### Trade Update Event
```json
{
  "type": "trade_updated",
  "timestamp": "2024-01-05T14:35:00Z",
  "data": {
    "trade_id": 1,
    "status": "OPEN",
    "current_price": 2048.00,
    "profit_loss": 125.00,
    "profit_loss_pips": 25.0
  }
}
```

#### Price Tick Event
```json
{
  "type": "price_tick",
  "timestamp": "2024-01-05T14:30:00.123Z",
  "data": {
    "instrument": "XAUUSD",
    "bid": 2045.50,
    "ask": 2045.70,
    "last": 2045.60
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional error details"
    },
    "timestamp": "2024-01-05T14:30:00Z",
    "request_id": "req_123456"
  }
}
```

### Common Error Codes

- `UNAUTHORIZED`: Authentication required or invalid
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `BAD_REQUEST`: Invalid request parameters
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Authenticated requests**: 100 requests per minute
- **Unauthenticated requests**: 10 requests per minute

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704463800
```

When rate limit is exceeded:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Pagination

List endpoints support pagination:

**Request:**
```http
GET /api/v1/signals/active?limit=20&offset=40
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 40,
    "has_more": true,
    "next_offset": 60
  }
}
```

---

## Versioning

API version is specified in the URL path:
- Current version: `/api/v1/`
- Future versions: `/api/v2/`, `/api/v3/`, etc.

Version deprecation will be announced 6 months in advance.

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**API Version**: v1