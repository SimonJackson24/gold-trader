"""
FastAPI application for XAUUSD Gold Trading System.

Provides REST API endpoints for:
- System status and health checks
- Trading signals
- Trade management
- Market data
- Account information
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
import uvicorn

from ..config import get_settings
from ..auth import jwt_handler, require_permission
from .auth import router as auth_router
from ..models.signal import Signal
from ..models.trade import Trade
from ..models.market_data import Tick, Candle
from ..database import get_database
from ..smart_money.smart_money_engine import SmartMoneyEngine
from ..signal_generator.signal_generator import SignalGenerator
from ..trade_manager.trade_manager import TradeManager
from ..market_data.market_data_processor import MarketDataProcessor
from ..notifications.telegram_service import TelegramService
from ..connectors.websocket_server import WebSocketServer
from ..connectors.mt5_connector import MT5Connector


# Pydantic models for API requests/responses
class SignalRequest(BaseModel):
    """Signal request model."""
    symbol: str = Field(..., description="Trading symbol")
    signal_type: str = Field(..., description="Signal type (BUY/SELL)")
    entry_price: Decimal = Field(..., description="Entry price")
    stop_loss: Decimal = Field(..., description="Stop loss price")
    take_profit: Decimal = Field(..., description="Take profit price")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    reasoning: str = Field(..., description="Signal reasoning")


class TradeRequest(BaseModel):
    """Trade request model."""
    symbol: str = Field(..., description="Trading symbol")
    trade_type: str = Field(..., description="Trade type (BUY/SELL)")
    volume: Decimal = Field(..., gt=0, description="Trade volume")
    price: Optional[Decimal] = Field(None, description="Trade price (market price if not specified)")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss price")
    take_profit: Optional[Decimal] = Field(None, description="Take profit price")


class SubscriptionRequest(BaseModel):
    """Subscription request model."""
    channels: List[str] = Field(..., description="List of channels to subscribe to")


# Global variables for services
settings = get_settings()
logger = logging.getLogger(__name__)
security = HTTPBearer()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Service instances
smart_money_engine: Optional[SmartMoneyEngine] = None
signal_generator: Optional[SignalGenerator] = None
trade_manager: Optional[TradeManager] = None
market_data_processor: Optional[MarketDataProcessor] = None
telegram_service: Optional[TelegramService] = None
websocket_server: Optional[WebSocketServer] = None
mt5_connector: Optional[MT5Connector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting XAUUSD Trading API...")
    
    # Initialize services
    global smart_money_engine, signal_generator, trade_manager
    global market_data_processor, telegram_service, websocket_server, mt5_connector
    
    try:
        # Initialize database
        db = get_database()
        await db.connect()
        
        # Initialize services
        smart_money_engine = SmartMoneyEngine()
        signal_generator = SignalGenerator()
        trade_manager = TradeManager()
        market_data_processor = MarketDataProcessor()
        telegram_service = TelegramService()
        websocket_server = WebSocketServer()
        mt5_connector = MT5Connector()
        
        # Start services
        await telegram_service.start()
        await websocket_server.start(market_data_processor)
        await mt5_connector.connect()
        
        # Set up service connections
        market_data_processor.add_tick_handler(signal_generator.process_tick)
        signal_generator.add_signal_handler(trade_manager.process_signal)
        signal_generator.add_signal_handler(telegram_service.send_signal_notification)
        trade_manager.add_trade_handler(telegram_service.send_trade_notification)
        
        logger.info("All services started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down XAUUSD Trading API...")
    
    try:
        # Stop services
        if mt5_connector:
            await mt5_connector.disconnect()
        if websocket_server:
            await websocket_server.stop()
        if telegram_service:
            await telegram_service.stop()
        
        # Close database
        db = get_database()
        await db.disconnect()
        
        logger.info("All services stopped successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="XAUUSD Gold Trading System API",
    description="REST API for XAUUSD Gold Trading System with Smart Money Concepts",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware with restricted origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Restrict methods
    allow_headers=["Authorization", "Content-Type"],  # Restrict headers
)

# Include authentication routes
app.include_router(auth_router)


# Authentication dependency
async def verify_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token with rate limiting."""
    # Apply rate limiting to all authenticated endpoints
    await jwt_handler.check_rate_limit(request)
    
    # Get and verify JWT token
    user = jwt_handler.get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Store user in request state for later use
    request.state.user = user
    return user


# Health check endpoints
@app.get("/health", tags=["Health"])
@limiter.limit("60/minute")  # Rate limit health checks
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/status", tags=["Health"])
async def get_status(token: str = Depends(verify_token)):
    """Get system status."""
    status = {
        "api": "running",
        "services": {
            "smart_money_engine": smart_money_engine is not None,
            "signal_generator": signal_generator is not None,
            "trade_manager": trade_manager is not None,
            "market_data_processor": market_data_processor is not None,
            "telegram_service": telegram_service.get_status() if telegram_service else None,
            "websocket_server": websocket_server.get_status() if websocket_server else None,
            "mt5_connector": mt5_connector.get_status() if mt5_connector else None
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    return status


# Signal endpoints
@app.get("/signals", tags=["Signals"])
@require_permission("read")
async def get_signals(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    token: str = Depends(verify_token)
):
    """Get recent trading signals."""
    try:
        signals = await signal_generator.get_recent_signals(limit, offset)
        return {
            "signals": [signal.to_dict() for signal in signals],
            "total": len(signals),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signals", tags=["Signals"])
@require_permission("write")
async def create_signal(
    request: Request,
    signal_request: SignalRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Create new trading signal."""
    try:
        # Create signal
        signal = Signal(
            symbol=signal_request.symbol,
            signal_type=signal_request.signal_type,
            entry_price=signal_request.entry_price,
            stop_loss=signal_request.stop_loss,
            take_profit=signal_request.take_profit,
            confidence=signal_request.confidence,
            reasoning=signal_request.reasoning,
            timestamp=datetime.utcnow()
        )
        
        # Process signal in background
        background_tasks.add_task(signal_generator.process_signal, signal)
        
        return {
            "message": "Signal created successfully",
            "signal": signal.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals/{signal_id}", tags=["Signals"])
@require_permission("read")
async def get_signal(
    request: Request,
    signal_id: str = Path(..., description="Signal ID"),
    token: str = Depends(verify_token)
):
    """Get specific signal by ID."""
    try:
        signal = await signal_generator.get_signal(signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return signal.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Trade endpoints
@app.get("/trades", tags=["Trades"])
@require_permission("read")
async def get_trades(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Trade status filter"),
    token: str = Depends(verify_token)
):
    """Get recent trades."""
    try:
        trades = await trade_manager.get_trades(limit, offset, status)
        return {
            "trades": [trade.to_dict() for trade in trades],
            "total": len(trades),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trades", tags=["Trades"])
@require_permission("write")
async def create_trade(
    request: Request,
    trade_request: TradeRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Create new trade."""
    try:
        # Create trade
        trade = Trade(
            symbol=trade_request.symbol,
            trade_type=trade_request.trade_type,
            volume=trade_request.volume,
            price=trade_request.price,
            stop_loss=trade_request.stop_loss,
            take_profit=trade_request.take_profit,
            status="PENDING",
            timestamp=datetime.utcnow()
        )
        
        # Execute trade in background
        background_tasks.add_task(trade_manager.execute_trade, trade)
        
        return {
            "message": "Trade created successfully",
            "trade": trade.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trades/{trade_id}", tags=["Trades"])
@require_permission("read")
async def get_trade(
    request: Request,
    trade_id: str = Path(..., description="Trade ID"),
    token: str = Depends(verify_token)
):
    """Get specific trade by ID."""
    try:
        trade = await trade_manager.get_trade(trade_id)
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        return trade.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Market data endpoints
@app.get("/market/ticks", tags=["Market Data"])
@require_permission("read")
async def get_ticks(
    request: Request,
    symbol: str = Query("XAUUSD", description="Trading symbol"),
    limit: int = Query(100, ge=1, le=1000),
    token: str = Depends(verify_token)
):
    """Get recent tick data."""
    try:
        ticks = await market_data_processor.get_recent_ticks(symbol, limit)
        return {
            "symbol": symbol,
            "ticks": [tick.to_dict() for tick in ticks],
            "total": len(ticks)
        }
    except Exception as e:
        logger.error(f"Error getting ticks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/candles", tags=["Market Data"])
@require_permission("read")
async def get_candles(
    request: Request,
    symbol: str = Query("XAUUSD", description="Trading symbol"),
    timeframe: str = Query("M15", description="Timeframe"),
    limit: int = Query(100, ge=1, le=1000),
    token: str = Depends(verify_token)
):
    """Get recent candle data."""
    try:
        candles = await market_data_processor.get_candles(symbol, timeframe, limit)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": [candle.to_dict() for candle in candles],
            "total": len(candles)
        }
    except Exception as e:
        logger.error(f"Error getting candles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Account endpoints
@app.get("/account/balance", tags=["Account"])
@require_permission("read")
async def get_balance(
    request: Request,
    token: str = Depends(verify_token)
):
    """Get account balance information."""
    try:
        balance_info = await mt5_connector.get_account_info()
        return balance_info
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/account/positions", tags=["Account"])
@require_permission("read")
async def get_positions(
    request: Request,
    token: str = Depends(verify_token)
):
    """Get open positions."""
    try:
        positions = await mt5_connector.get_positions()
        return {
            "positions": positions,
            "total": len(positions)
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analysis endpoints
@app.post("/analysis/smart-money", tags=["Analysis"])
@require_permission("read")
async def analyze_smart_money(
    request: Request,
    symbol: str = Query("XAUUSD", description="Trading symbol"),
    token: str = Depends(verify_token)
):
    """Perform Smart Money Concepts analysis."""
    try:
        # Get recent market data
        candles = await market_data_processor.get_candles(symbol, "H1", 100)
        
        # Perform analysis
        analysis = await smart_money_engine.analyze_candles(candles)
        
        return {
            "symbol": symbol,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in smart money analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket subscription endpoint
@app.post("/websocket/subscribe", tags=["WebSocket"])
@require_permission("read")
async def websocket_subscribe(
    request: Request,
    subscription_request: SubscriptionRequest,
    token: str = Depends(verify_token)
):
    """Subscribe to WebSocket channels."""
    try:
        # This would handle WebSocket subscription logic
        # For now, return success
        return {
            "message": "Subscription successful",
            "channels": subscription_request.channels
        }
    except Exception as e:
        logger.error(f"Error in WebSocket subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Performance endpoints
@app.get("/performance/daily", tags=["Performance"])
@require_permission("read")
async def get_daily_performance(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    instrument: Optional[str] = Query("XAUUSD", description="Trading instrument"),
    limit: int = Query(30, ge=1, le=100, description="Maximum results to return"),
    token: str = Depends(verify_token)
):
    """Get daily performance metrics."""
    try:
        from ..database import get_database
        from ..database.repositories import PerformanceRepository
        
        db = get_database()
        await db.connect()
        
        # Parse dates or use defaults
        from datetime import datetime, timedelta
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_dt = (datetime.utcnow() - timedelta(days=30)).date()
            
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_dt = datetime.utcnow().date()
        
        # Get performance metrics
        perf_repo = PerformanceRepository(db.get_session())
        metrics = perf_repo.get_metrics_by_date_range(start_dt, end_dt, instrument)
        
        # Calculate summary statistics
        if metrics:
            summary = {
                "total_days": len(metrics),
                "average_win_rate": sum(m.win_rate or 0 for m in metrics) / len(metrics),
                "total_profit_loss": sum(m.total_profit_loss or 0 for m in metrics),
                "total_pips": sum(m.total_pips or 0 for m in metrics)
            }
        else:
            summary = {
                "total_days": 0,
                "average_win_rate": 0,
                "total_profit_loss": 0,
                "total_pips": 0
            }
        
        await db.disconnect()
        
        return {
            "metrics": [metric.to_dict() for metric in metrics],
            "summary": summary,
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting daily performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/weekly", tags=["Performance"])
@require_permission("read")
async def get_weekly_performance(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    instrument: Optional[str] = Query("XAUUSD", description="Trading instrument"),
    limit: int = Query(12, ge=1, le=52, description="Maximum weeks to return"),
    token: str = Depends(verify_token)
):
    """Get weekly performance metrics."""
    try:
        from ..database import get_database
        from ..database.repositories import PerformanceRepository
        from datetime import datetime, timedelta
        import calendar
        
        db = get_database()
        await db.connect()
        
        # Parse dates or use defaults (last 12 weeks)
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_dt = (datetime.utcnow() - timedelta(weeks=12)).date()
            
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_dt = datetime.utcnow().date()
        
        # Get performance metrics
        perf_repo = PerformanceRepository(db.get_session())
        daily_metrics = perf_repo.get_metrics_by_date_range(start_dt, end_dt, instrument)
        
        # Aggregate daily metrics into weekly data
        weekly_data = {}
        for metric in daily_metrics:
            week_start = metric.metric_date - timedelta(days=metric.metric_date.weekday())
            week_key = week_start.isoformat()
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "week_start": week_start,
                    "total_signals": 0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0,
                    "total_profit_loss": 0,
                    "total_pips": 0
                }
            
            week_data = weekly_data[week_key]
            week_data["total_signals"] += metric.total_signals or 0
            week_data["total_trades"] += metric.total_trades or 0
            week_data["winning_trades"] += metric.winning_trades or 0
            week_data["losing_trades"] += metric.losing_trades or 0
            week_data["total_profit_loss"] += metric.total_profit_loss or 0
            week_data["total_pips"] += metric.total_pips or 0
        
        # Calculate win rates for each week
        for week_data in weekly_data.values():
            if week_data["total_trades"] > 0:
                week_data["win_rate"] = (week_data["winning_trades"] / week_data["total_trades"]) * 100
        
        # Convert to list and limit
        weekly_list = sorted(weekly_data.values(), key=lambda x: x["week_start"], reverse=True)[:limit]
        
        # Calculate summary
        if weekly_list:
            summary = {
                "total_weeks": len(weekly_list),
                "average_win_rate": sum(w["win_rate"] for w in weekly_list) / len(weekly_list),
                "total_profit_loss": sum(w["total_profit_loss"] for w in weekly_list),
                "total_pips": sum(w["total_pips"] for w in weekly_list)
            }
        else:
            summary = {
                "total_weeks": 0,
                "average_win_rate": 0,
                "total_profit_loss": 0,
                "total_pips": 0
            }
        
        await db.disconnect()
        
        return {
            "metrics": weekly_list,
            "summary": summary,
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting weekly performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/monthly", tags=["Performance"])
@require_permission("read")
async def get_monthly_performance(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    instrument: Optional[str] = Query("XAUUSD", description="Trading instrument"),
    limit: int = Query(12, ge=1, le=24, description="Maximum months to return"),
    token: str = Depends(verify_token)
):
    """Get monthly performance metrics."""
    try:
        from ..database import get_database
        from ..database.repositories import PerformanceRepository
        from datetime import datetime, timedelta
        
        db = get_database()
        await db.connect()
        
        # Parse dates or use defaults (last 12 months)
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_dt = (datetime.utcnow() - timedelta(days=365)).date()
            
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_dt = datetime.utcnow().date()
        
        # Get performance metrics
        perf_repo = PerformanceRepository(db.get_session())
        daily_metrics = perf_repo.get_metrics_by_date_range(start_dt, end_dt, instrument)
        
        # Aggregate daily metrics into monthly data
        monthly_data = {}
        for metric in daily_metrics:
            month_key = metric.metric_date.strftime("%Y-%m")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": metric.metric_date.month,
                    "year": metric.metric_date.year,
                    "total_signals": 0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0,
                    "total_profit_loss": 0,
                    "total_pips": 0
                }
            
            month_data = monthly_data[month_key]
            month_data["total_signals"] += metric.total_signals or 0
            month_data["total_trades"] += metric.total_trades or 0
            month_data["winning_trades"] += metric.winning_trades or 0
            month_data["losing_trades"] += metric.losing_trades or 0
            month_data["total_profit_loss"] += metric.total_profit_loss or 0
            month_data["total_pips"] += metric.total_pips or 0
        
        # Calculate win rates for each month
        for month_data in monthly_data.values():
            if month_data["total_trades"] > 0:
                month_data["win_rate"] = (month_data["winning_trades"] / month_data["total_trades"]) * 100
        
        # Convert to list and limit
        monthly_list = sorted(monthly_data.values(), key=lambda x: (x["year"], x["month"]), reverse=True)[:limit]
        
        # Calculate summary
        if monthly_list:
            summary = {
                "total_months": len(monthly_list),
                "average_win_rate": sum(m["win_rate"] for m in monthly_list) / len(monthly_list),
                "total_profit_loss": sum(m["total_profit_loss"] for m in monthly_list),
                "total_pips": sum(m["total_pips"] for m in monthly_list)
            }
        else:
            summary = {
                "total_months": 0,
                "average_win_rate": 0,
                "total_profit_loss": 0,
                "total_pips": 0
            }
        
        await db.disconnect()
        
        return {
            "metrics": monthly_list,
            "summary": summary,
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting monthly performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )