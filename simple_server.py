#!/usr/bin/env python3
"""
Simple test server to verify Angular frontend can connect to backend.
"""

import json
import jwt
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4201", "http://localhost:4202", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/auth/login")
async def login():
    # Mock login response for testing
    secret = "your-secret-key"
    payload = {
        "user_id": "1",
        "username": "testuser",
        "exp": int(time.time()) + 60 * 60  # 1 hour expiration
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return JSONResponse({
        "access_token": token,
        "refresh_token": "mock_refresh_token",
        "user": {
            "user_id": "1",
            "username": "testuser",
            "email": "testuser@example.com",
            "role": "admin",
            "permissions": ["read", "write"]
        }
    })

@app.post("/api/v1/auth/refresh")
async def refresh():
    # Mock refresh response for testing
    secret = "your-secret-key"
    payload = {
        "user_id": "1",
        "username": "testuser",
        "exp": int(time.time()) + 60 * 60  # 1 hour expiration
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return JSONResponse({
        "access_token": token,
        "user": {
            "user_id": "1",
            "username": "testuser",
            "email": "testuser@example.com",
            "role": "admin",
            "permissions": ["read", "write"]
        }
    })

@app.get("/api/v1/health")
async def health():
    return JSONResponse({"status": "healthy", "message": "Gold Trader API is running"})

@app.get("/api/v1/account/balance")
async def get_balance():
    # Mock balance data for testing
    return JSONResponse({
        "balance": 10000.0,
        "equity": 10500.0,
        "margin": 1000.0,
        "margin_free": 9500.0,
        "margin_level": 1050,
        "profit": 500.0,
        "open_trades": 2,
        "closed_trades": 10,
        "total_volume": 1.5,
        "deposit": 10000.0,
        "withdrawal": 0.0
    })

@app.get("/api/v1/signals")
async def get_signals():
    # Mock signals data for testing
    return JSONResponse({
        "signals": [
            {
                "signal_id": "SIGNAL_001",
                "instrument": "XAUUSD",
                "direction": "BUY",
                "entry_price": 2050.5,
                "stop_loss": 2045.0,
                "take_profit_1": 2060.0,
                "take_profit_2": 2070.0,
                "risk_reward_ratio": 2.0,
                "position_size": 0.01,
                "confidence_score": 85,
                "created_at": "2025-12-06T18:00:00Z",
                "status": "ACTIVE"
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0
    })

@app.get("/api/v1/performance")
async def get_performance():
    # Mock performance data for testing
    return JSONResponse({
        "total_trades": 125,
        "winning_trades": 80,
        "losing_trades": 45,
        "win_rate": 64.0,
        "total_profit_loss": 5500.0,
        "total_pips": 2750,
        "average_rr": 1.9,
        "max_drawdown": 12.5,
        "profit_factor": 2.1,
        "expectancy": 44.0
    })
@app.get("/api/v1/trades")
async def get_trades():
    # Mock trades data for testing
    return JSONResponse({
        "trades": [
            {
                "trade_id": "TRADE_001",
                "instrument": "XAUUSD",
                "direction": "BUY",
                "entry_price": 2050.5,
                "exit_price": 2060.0,
                "stop_loss": 2045.0,
                "take_profit": 2070.0,
                "position_size": 0.01,
                "profit_loss": 9.5,
                "pips": 95,
                "status": "CLOSED",
                "opened_at": "2025-12-06T18:00:00Z",
                "closed_at": "2025-12-06T20:00:00Z"
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0
    })

@app.get("/api/v1/account/positions")
async def get_positions():
    # Mock positions data for testing
    return JSONResponse([
        {
            "position_id": "POS_001",
            "instrument": "XAUUSD",
            "direction": "BUY",
            "entry_price": 2055.0,
            "stop_loss": 2050.0,
            "take_profit": 2065.0,
            "position_size": 0.02,
            "profit_loss": -1.0,
            "pips": -10,
            "status": "OPEN",
            "opened_at": "2025-12-07T10:00:00Z"
        }
    ])


@app.get("/api/v1/performance/daily")
async def get_daily_performance():
    # Mock daily performance data for testing
    return JSONResponse({
        "metrics": [
            {
                "date": "2025-12-01",
                "instrument": "XAUUSD",
                "total_signals": 5,
                "total_trades": 3,
                "winning_trades": 2,
                "losing_trades": 1,
                "win_rate": 66.7,
                "average_rr": 1.8,
                "total_pips": 125,
                "total_profit_loss": 250.0,
                "calculated_at": "2025-12-01T23:59:59Z"
            },
            {
                "date": "2025-12-02",
                "instrument": "XAUUSD",
                "total_signals": 4,
                "total_trades": 2,
                "winning_trades": 1,
                "losing_trades": 1,
                "win_rate": 50.0,
                "average_rr": 1.5,
                "total_pips": -45,
                "total_profit_loss": -90.0,
                "calculated_at": "2025-12-02T23:59:59Z"
            }
        ],
        "summary": {
            "total_days": 2,
            "average_win_rate": 58.35,
            "total_profit_loss": 160.0,
            "total_pips": 80
        }
    })

@app.get("/api/v1/performance/weekly")
async def get_weekly_performance():
    # Mock weekly performance data for testing
    return JSONResponse({
        "metrics": [
            {
                "week_start": "2025-11-25",
                "total_signals": 28,
                "total_trades": 15,
                "winning_trades": 10,
                "losing_trades": 5,
                "win_rate": 66.7,
                "total_profit_loss": 850.0,
                "total_pips": 425
            },
            {
                "week_start": "2025-12-02",
                "total_signals": 32,
                "total_trades": 18,
                "winning_trades": 12,
                "losing_trades": 6,
                "win_rate": 66.7,
                "total_profit_loss": 1020.0,
                "total_pips": 510
            }
        ],
        "summary": {
            "total_weeks": 2,
            "average_win_rate": 66.7,
            "total_profit_loss": 1870.0,
            "total_pips": 935
        }
    })

@app.get("/api/v1/performance/monthly")
async def get_monthly_performance():
    # Mock monthly performance data for testing
    return JSONResponse({
        "metrics": [
            {
                "month": 11,
                "year": 2025,
                "total_signals": 120,
                "total_trades": 65,
                "winning_trades": 42,
                "losing_trades": 23,
                "win_rate": 64.6,
                "total_profit_loss": 3200.0,
                "total_pips": 1600
            },
            {
                "month": 12,
                "year": 2025,
                "total_signals": 145,
                "total_trades": 78,
                "winning_trades": 52,
                "losing_trades": 26,
                "win_rate": 66.7,
                "total_profit_loss": 3850.0,
                "total_pips": 1925
            }
        ],
        "summary": {
            "total_months": 2,
            "average_win_rate": 65.65,
            "total_profit_loss": 7050.0,
            "total_pips": 3525
        }
    })

if __name__ == "__main__":
    print("Starting simple test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import WebSocket

...

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    await websocket.accept()
    print(f"WebSocket connection established with token: {token}")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        print(f"WebSocket connection closed: {e}")
