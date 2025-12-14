"""
MT5 bridge for XAUUSD Gold Trading System.

Connects to MetaTrader 5 terminal, captures real-time
price data, and forwards to analysis server.
"""

import asyncio
import logging
from typing import Optional, Callable, List
from datetime import datetime
from decimal import Decimal

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None
    logging.warning("MetaTrader5 not available. MT5 bridge will run in simulation mode.")


class MT5Bridge:
    """
    MT5 bridge implementation.
    
    Connects to MT5 terminal, captures tick data,
    and forwards to WebSocket server.
    """
    
    def __init__(self):
        """Initialize MT5 bridge."""
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.is_subscribed = False
        self.symbol = "XAUUSD"
        self.on_tick_callbacks: List[Callable] = []
        self.on_error_callbacks: List[Callable] = []
        
        # Processing state
        self.ticks_processed = 0
        self.last_tick_time = None
    
    async def connect(self) -> bool:
        """
        Connect to MT5 terminal.
        
        Returns:
            True if successful
        """
        if not mt5:
            self.logger.error("MetaTrader5 not available")
            return False
        
        try:
            # Initialize MT5
            if not mt5.initialize():
                self.logger.error("Failed to initialize MT5")
                return False
            
            # Login to trade account
            if not mt5.login():
                self.logger.error("Failed to login to MT5")
                return False
            
            # Wait for terminal to be ready
            if not mt5.terminal_wait():
                self.logger.error("MT5 terminal not ready")
                return False
            
            # Subscribe to symbol
            if not mt5.symbol_select(self.symbol, mt5.MODE_TRADES):
                self.logger.error(f"Failed to select symbol {self.symbol}")
                return False
            
            self.is_connected = True
            self.is_subscribed = True
            
            self.logger.info(f"Connected to MT5 for {self.symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to MT5: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MT5 terminal."""
        if self.is_connected:
            mt5.shutdown()
            self.is_connected = False
            self.is_subscribed = False
            self.logger.info("Disconnected from MT5")
    
    def add_tick_callback(self, callback: Callable):
        """
        Add callback for tick data.
        
        Args:
            callback: Callback function
        """
        self.on_tick_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """
        Add callback for error events.
        
        Args:
            callback: Callback function
        """
        self.on_error_callbacks.append(callback)
    
    async def start_tick_streaming(self):
        """
        Start streaming tick data from MT5.
        """
        if not self.is_connected or not self.is_subscribed:
            self.logger.error("Not connected to MT5")
            return
        
        try:
            # Start tick capture
            if not mt5.copy_rates_from_pos(self.symbol, mt5.MODE_TRADES):
                self.logger.error("Failed to start tick streaming")
                return
            
            self.logger.info("Started tick streaming for {self.symbol}")
            
            # Process ticks
            while self.is_connected and self.is_subscribed:
                # Get tick data
                tick = mt5.copy_rates_tick(self.symbol)
                
                if tick:
                    self.ticks_processed += 1
                    self.last_tick_time = tick.time
                    
                    # Trigger callbacks
                    for callback in self.on_tick_callbacks:
                        try:
                            await callback({
                                'symbol': self.symbol,
                                'timestamp': tick.time,
                                'bid': tick.bid,
                                'ask': tick.ask,
                                'last': tick.last,
                                'volume': tick.volume
                            })
                        except Exception as e:
                            self.logger.error(f"Error in tick callback: {e}")
                else:
                    self.logger.warning("Received empty tick from MT5")
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.01)
            
        except Exception as e:
            self.logger.error(f"Error in tick streaming: {e}")
    
    async def get_account_info(self) -> Optional[dict]:
        """
        Get account information.
        
        Returns:
            Account info or None
        """
        if not mt5:
            return None
        
        try:
            account_info = mt5.account_info()
            return {
                'login': account_info.login,
                'server': account_info.server,
                'name': account_info.name,
                'currency': account_info.currency,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin_free': account_info.margin_free,
                'margin_level': account_info.margin_level
            }
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        Get symbol information.
        
        Args:
            symbol: Symbol to query
            
        Returns:
            Symbol info or None
        """
        if not mt5:
            return None
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            return {
                'symbol': symbol_info.symbol,
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'trade_contract_size': symbol_info.trade_contract_size,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'swap_mode': symbol_info.swap_mode,
                'swap_long': symbol_info.swap_long,
                'swap_short': symbol_info.swap_short,
                'swap_rollover3days': symbol_info.swap_rollover3days,
                'description': symbol_info.description
            }
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_status(self) -> dict:
        """
        Get bridge status.
        
        Returns:
            Status dictionary
        """
        return {
            'is_connected': self.is_connected,
            'is_subscribed': self.is_subscribed,
            'symbol': self.symbol,
            'ticks_processed': self.ticks_processed,
            'last_tick_time': self.last_tick_time.isoformat() if self.last_tick_time else None,
            'mt5_available': mt5 is not None
        }