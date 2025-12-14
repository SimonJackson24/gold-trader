"""
WebSocket server for XAUUSD Gold Trading System.

Handles WebSocket connections from MT5 connector,
broadcasts real-time data, and manages client sessions.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Callable
from datetime import datetime
from decimal import Decimal
import websockets
from websockets.server import WebSocketServerProtocol

from ..models.market_data import Tick
from ..config import get_settings


class WebSocketServer:
    """
    WebSocket server implementation.
    
    Handles client connections, message broadcasting,
    and session management.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        """
        Initialize WebSocket server.
        
        Args:
            host: Server host
            port: Server port
        """
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        
        # Server state
        self.clients: Set[WebSocketServerProtocol] = set()
        self.is_running = False
        self.server = None
        
        # Message handlers
        self.tick_handlers: List[Callable] = []
        self.signal_handlers: List[Callable] = []
    
    def add_tick_handler(self, handler: Callable):
        """
        Add handler for tick messages.
        
        Args:
            handler: Tick handler function
        """
        self.tick_handlers.append(handler)
    
    def add_signal_handler(self, handler: Callable):
        """
        Add handler for signal messages.
        
        Args:
            handler: Signal handler function
        """
        self.signal_handlers.append(handler)
    
    async def start(self):
        """Start WebSocket server."""
        self.is_running = True
        self.logger.info(f"WebSocket server starting on {self.host}:{self.port}")
        
        # Create server
        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=self.settings.ws_heartbeat_interval,
            ping_timeout=10
        )
        
        self.logger.info("WebSocket server started")
    
    async def stop(self):
        """Stop WebSocket server."""
        self.is_running = False
        self.logger.info("WebSocket server stopping")
        
        # Close all client connections
        for client in self.clients:
            await client.close()
        self.clients.clear()
        
        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.logger.info("WebSocket server stopped")
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new client connection."""
        self.clients.add(websocket)
        self.logger.info(f"Client connected from {websocket.remote_address[0]}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': 'Connected to XAUUSD trading server',
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # Handle messages
            async for message in websocket:
                await self._handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {websocket.remote_address[0]}")
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'tick':
                # Handle tick data
                tick = self._parse_tick_data(data)
                await self._handle_tick_message(tick)
            
            elif message_type == 'signal':
                # Handle signal data
                signal = self._parse_signal_data(data)
                await self._handle_signal_message(signal)
            
            elif message_type == 'subscribe':
                # Handle subscription
                await self._handle_subscribe_message(websocket, data)
            
            else:
                # Unknown message type
                self.logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }))
    
    def _parse_tick_data(self, data: dict) -> Tick:
        """Parse tick data from message."""
        return Tick(
            symbol=data.get('symbol', 'XAUUSD'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            bid=Decimal(str(data['bid'])),
            ask=Decimal(str(data['ask'])),
            last=Decimal(str(data.get('last', data['bid']))),
            volume=data.get('volume')
        )
    
    def _parse_signal_data(self, data: dict):
        """Parse signal data from message."""
        # This would parse a signal object
        # For now, return None
        return None
    
    async def _handle_tick_message(self, tick: Tick):
        """Handle tick message and broadcast to handlers."""
        # Broadcast to all tick handlers
        for handler in self.tick_handlers:
            try:
                await handler(tick)
            except Exception as e:
                self.logger.error(f"Error in tick handler: {e}")
    
    async def _handle_signal_message(self, signal):
        """Handle signal message and broadcast to handlers."""
        # Broadcast to all signal handlers
        for handler in self.signal_handlers:
            try:
                await handler(signal)
            except Exception as e:
                self.logger.error(f"Error in signal handler: {e}")
    
    async def _handle_subscribe_message(self, websocket: WebSocketServerProtocol, data: dict):
        """Handle subscription message."""
        try:
            channels = data.get('channels', [])
            
            for channel in channels:
                if channel == 'ticks':
                    # Add to tick subscribers
                    for handler in self.tick_handlers:
                        try:
                            await handler(websocket)
                        except Exception as e:
                            self.logger.error(f"Error adding tick subscriber: {e}")
                elif channel == 'signals':
                    # Add to signal subscribers
                    for handler in self.signal_handlers:
                        try:
                            await handler(websocket)
                        except Exception as e:
                            self.logger.error(f"Error adding signal subscriber: {e}")
                else:
                    self.logger.warning(f"Unknown channel: {channel}")
            
            await websocket.send(json.dumps({
                'type': 'subscribed',
                'channels': channels,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
        except Exception as e:
            self.logger.error(f"Error handling subscription: {e}")
    
    async def broadcast_tick(self, tick: Tick):
        """Broadcast tick to all subscribed clients."""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'tick',
            'data': tick.to_dict()
        })
        
        # Send to all clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting tick to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    async def broadcast_signal(self, signal):
        """Broadcast signal to all subscribed clients."""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'signal',
            'data': signal.to_dict()
        })
        
        # Send to all clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting signal to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    def get_status(self) -> Dict[str, any]:
        """Get server status."""
        return {
            'is_running': self.is_running,
            'connected_clients': len(self.clients),
            'host': self.host,
            'port': self.port,
            'tick_handlers': len(self.tick_handlers),
            'signal_handlers': len(self.signal_handlers)
        }