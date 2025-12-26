"""
MT5 connector for XAUUSD Gold Trading System.

Bridges MetaTrader 5 terminal with our trading system
through WebSocket communication.
"""

import asyncio
import json
import logging
import random
from typing import Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
from decimal import Decimal
import MetaTrader5 as mt5
import websockets
from websockets.client import WebSocketClientProtocol

from ..models.market_data import Tick
from ..models.candle import Candle
from ..models.trade import Trade
from ..config import get_settings


class MT5Connector:
    """
    MT5 connector implementation.
    
    Connects to MetaTrader 5 terminal, retrieves market data,
    and executes trades through WebSocket communication.
    """
    
    def __init__(self, websocket_url: str = "ws://localhost:8001"):
        """
        Initialize MT5 connector.
        
        Args:
            websocket_url: WebSocket server URL
        """
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.websocket_url = websocket_url
        
        # MT5 connection state
        self.is_connected = False
        self.mt5_initialized = False
        
        # WebSocket connection
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.is_websocket_connected = False
        
        # Data handlers
        self.tick_handlers: List[Callable] = []
        self.trade_handlers: List[Callable] = []
        
        # Subscription state
        self.subscribed_symbols: Set[str] = set()
        self.last_tick_time: Dict[str, datetime] = {}
    
    async def connect(self):
        """Connect to MT5 terminal and WebSocket server."""
        if getattr(self.settings, 'dev_mock_mt5', False):
            self.logger.info("MT5 connector starting in MOCK mode")
            self.is_connected = True
            # Even in mock mode, we still connect to our own websocket if needed
            try:
                await self._connect_websocket()
            except Exception as e:
                self.logger.warning(f"Could not connect to local websocket in mock mode: {e}")
            return

        try:
            # Initialize MT5
            if not mt5.initialize(
                login=int(self.settings.mt5_login),
                password=self.settings.mt5_password,
                server=self.settings.mt5_server,
                path=self.settings.mt5_path
            ):
                raise Exception(f"Failed to initialize MT5: {mt5.last_error()}")
            
            self.mt5_initialized = True
            self.logger.info("MT5 initialized successfully")
            
            # Connect to WebSocket server
            await self._connect_websocket()
            
            self.is_connected = True
            self.logger.info("MT5 connector connected successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to connect MT5 connector: {e}")
            await self.disconnect()
            raise
    
    async def _connect_websocket(self):
        """Connect to WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_websocket_connected = True
            self.logger.info(f"Connected to WebSocket server: {self.websocket_url}")
            
            # Start message handler
            asyncio.create_task(self._handle_websocket_messages())
            
        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket server: {e}")
            raise
    
    async def _handle_websocket_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'signal':
                    # Handle trading signal
                    await self._handle_signal(data.get('data'))
                
                elif message_type == 'trade_request':
                    # Handle trade request
                    await self._handle_trade_request(data.get('data'))
                
                elif message_type == 'subscribe':
                    # Handle subscription request
                    await self._handle_subscribe_request(data.get('data'))
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            self.is_websocket_connected = False
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
    
    async def _handle_signal(self, signal_data: dict):
        """Handle trading signal."""
        try:
            # Convert signal to trade
            trade = self._signal_to_trade(signal_data)
            
            # Execute trade
            result = await self._execute_trade(trade)
            
            # Send result back
            if self.websocket:
                await self.websocket.send(json.dumps({
                    'type': 'trade_result',
                    'data': {
                        'signal_id': signal_data.get('id'),
                        'success': result['success'],
                        'trade_id': result.get('trade_id'),
                        'error': result.get('error')
                    }
                }))
            
        except Exception as e:
            self.logger.error(f"Error handling signal: {e}")
    
    async def _handle_trade_request(self, request_data: dict):
        """Handle trade request."""
        try:
            # Create trade from request
            trade = Trade(
                symbol=request_data['symbol'],
                trade_type=request_data['type'],
                volume=Decimal(str(request_data['volume'])),
                price=Decimal(str(request_data['price'])),
                stop_loss=Decimal(str(request_data.get('stop_loss'))),
                take_profit=Decimal(str(request_data.get('take_profit')))
            )
            
            # Execute trade
            result = await self._execute_trade(trade)
            
            # Send result back
            if self.websocket:
                await self.websocket.send(json.dumps({
                    'type': 'trade_result',
                    'data': result
                }))
            
        except Exception as e:
            self.logger.error(f"Error handling trade request: {e}")
    
    async def _handle_subscribe_request(self, request_data: dict):
        """Handle subscription request."""
        try:
            symbol = request_data.get('symbol', 'XAUUSD')
            subscribe = request_data.get('subscribe', True)
            
            if subscribe:
                await self.subscribe_symbol(symbol)
            else:
                await self.unsubscribe_symbol(symbol)
            
            # Send confirmation
            if self.websocket:
                await self.websocket.send(json.dumps({
                    'type': 'subscription_result',
                    'data': {
                        'symbol': symbol,
                        'subscribed': subscribe
                    }
                }))
            
        except Exception as e:
            self.logger.error(f"Error handling subscription request: {e}")
    
    async def subscribe_symbol(self, symbol: str):
        """
        Subscribe to symbol for real-time data.
        
        Args:
            symbol: Symbol to subscribe to
        """
        if symbol in self.subscribed_symbols:
            return
        
        self.subscribed_symbols.add(symbol)
        self.logger.info(f"Subscribed to {symbol}")
        
        # Start data streaming
        asyncio.create_task(self._stream_symbol_data(symbol))
    
    async def unsubscribe_symbol(self, symbol: str):
        """
        Unsubscribe from symbol.
        
        Args:
            symbol: Symbol to unsubscribe from
        """
        if symbol in self.subscribed_symbols:
            self.subscribed_symbols.remove(symbol)
            self.logger.info(f"Unsubscribed from {symbol}")
    
    async def _stream_symbol_data(self, symbol: str):
        """Stream real-time data for symbol."""
        mock_price = Decimal('2000.00')
        while symbol in self.subscribed_symbols and self.is_connected:
            try:
                if not self.mt5_initialized:
                    # Generate mock tick
                    mock_price += Decimal(str(random.uniform(-0.1, 0.1)))
                    tick_data = Tick(
                        symbol=symbol,
                        timestamp=datetime.utcnow(),
                        bid=mock_price,
                        ask=mock_price + Decimal('0.2'),
                        volume=random.randint(1, 10)
                    )
                else:
                    # Get tick data from MT5
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick:
                        await asyncio.sleep(1)
                        continue
                        
                    tick_data = Tick(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(tick.time),
                        bid=Decimal(str(tick.bid)),
                        ask=Decimal(str(tick.ask)),
                        last=Decimal(str(tick.last)) if tick.last else None,
                        volume=tick.volume
                    )
                
                # Send tick to WebSocket server
                if self.websocket:
                    try:
                        await self.websocket.send(json.dumps({
                            'type': 'tick',
                            'data': tick_data.to_dict()
                        }))
                    except Exception as e:
                        self.logger.debug(f"Could not send to websocket: {e}")
                
                # Call tick handlers
                for handler in self.tick_handlers:
                    try:
                        await handler(tick_data)
                    except Exception as e:
                        self.logger.error(f"Error in tick handler: {e}")
                
                # Wait before next tick
                await asyncio.sleep(1.0 if not self.mt5_initialized else 0.1)
                
            except Exception as e:
                self.logger.error(f"Error streaming data for {symbol}: {e}")
                await asyncio.sleep(1)
    
    async def _execute_trade(self, trade: Trade) -> dict:
        """
        Execute trade through MT5.
        
        Args:
            trade: Trade to execute
            
        Returns:
            Trade execution result
        """
        try:
            # Prepare trade request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": trade.symbol,
                "volume": float(trade.volume),
                "type": mt5.ORDER_TYPE_BUY if trade.trade_type == "BUY" else mt5.ORDER_TYPE_SELL,
                "price": float(trade.price),
                "sl": float(trade.stop_loss) if trade.stop_loss else 0,
                "tp": float(trade.take_profit) if trade.take_profit else 0,
                "deviation": 20,
                "magic": 234000,
                "comment": "XAUUSD Trading System",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send trade request
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f"Trade failed: {result.comment}"
                }
            
            # Create trade record
            executed_trade = Trade(
                symbol=trade.symbol,
                trade_type=trade.trade_type,
                volume=trade.volume,
                price=Decimal(str(result.price)),
                stop_loss=Decimal(str(result.sl)) if result.sl else None,
                take_profit=Decimal(str(result.tp)) if result.tp else None,
                status='EXECUTED',
                mt5_order_id=result.order,
                mt5_position_id=result.position
            )
            
            # Call trade handlers
            for handler in self.trade_handlers:
                try:
                    await handler(executed_trade)
                except Exception as e:
                    self.logger.error(f"Error in trade handler: {e}")
            
            return {
                'success': True,
                'trade_id': executed_trade.id,
                'order_id': result.order,
                'position_id': result.position,
                'price': result.price
            }
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _signal_to_trade(self, signal_data: dict) -> Trade:
        """Convert signal data to trade object."""
        return Trade(
            symbol=signal_data.get('symbol', 'XAUUSD'),
            trade_type=signal_data.get('signal_type', 'BUY'),
            volume=Decimal(str(signal_data.get('volume', 0.01))),
            price=Decimal(str(signal_data.get('entry_price'))),
            stop_loss=Decimal(str(signal_data.get('stop_loss'))),
            take_profit=Decimal(str(signal_data.get('take_profit'))),
            confidence=signal_data.get('confidence', 0.5)
        )
    
    async def get_account_info(self) -> dict:
        """Get MT5 account information."""
        try:
            account_info = mt5.account_info()
            if account_info:
                return {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'free_margin': account_info.margin_free,
                    'margin_level': account_info.margin_level,
                    'profit': account_info.profit
                }
            return {}
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {}
    
    async def get_positions(self) -> List[dict]:
        """Get open positions from MT5."""
        try:
            positions = mt5.positions_get()
            if positions:
                return [
                    {
                        'ticket': pos.ticket,
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                        'volume': pos.volume,
                        'price_open': pos.price_open,
                        'price_current': pos.price_current,
                        'profit': pos.profit,
                        'time': datetime.fromtimestamp(pos.time).isoformat()
                    }
                    for pos in positions
                ]
            return []
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    def add_tick_handler(self, handler: Callable):
        """Add tick data handler."""
        self.tick_handlers.append(handler)
    
    def add_trade_handler(self, handler: Callable):
        """Add trade execution handler."""
        self.trade_handlers.append(handler)
    
    def get_status(self) -> dict:
        """Get connector status."""
        return {
            'is_connected': self.is_connected,
            'mt5_initialized': self.mt5_initialized,
            'websocket_connected': self.is_websocket_connected,
            'subscribed_symbols': list(self.subscribed_symbols),
            'websocket_url': self.websocket_url
        }