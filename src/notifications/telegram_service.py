"""
Telegram notification service for XAUUSD Gold Trading System.

Sends trading signals, alerts, and system notifications
through Telegram bot.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
import logging
from typing import Dict, List, Optional, Union, Set, Callable
from datetime import datetime
from decimal import Decimal
import aiohttp
import telegram
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from ..models.signal import TradingSignal as Signal
from ..models.trade import Trade
from ..models.market_data import Tick
from ..config import get_settings


class TelegramService:
    """
    Telegram notification service implementation.

    Handles bot commands, message formatting, and notification delivery.
    """

    def __init__(self):
        """Initialize Telegram service."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

        # Bot state
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.is_running = False

        # User management
        self.authorized_users: Set[int] = set()
        self.user_preferences: Dict[int, Dict] = {}

        # Notification handlers
        self.signal_handlers: List[Callable] = []
        self.trade_handlers: List[Callable] = []

    async def start(self):
        """Start Telegram bot service."""
        if getattr(self.settings, "dev_mock_telegram", False):
            self.logger.info("Telegram bot service starting in MOCK mode")
            self.is_running = True
            return

        try:
            # Initialize bot
            self.bot = Bot(token=self.settings.telegram_bot_token)
            self.application = (
                Application.builder().token(self.settings.telegram_bot_token).build()
            )

            # Register command handlers
            self._register_handlers()

            # Start bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            self.is_running = True
            self.logger.info("Telegram bot started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start Telegram bot: {e}")
            raise

    async def stop(self):
        """Stop Telegram bot service."""
        self.is_running = False

        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

        self.logger.info("Telegram bot stopped")

    def _register_handlers(self):
        """Register bot command handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(
            CommandHandler("subscribe", self._handle_subscribe)
        )
        self.application.add_handler(
            CommandHandler("unsubscribe", self._handle_unsubscribe)
        )
        self.application.add_handler(CommandHandler("balance", self._handle_balance))
        self.application.add_handler(
            CommandHandler("positions", self._handle_positions)
        )
        self.application.add_handler(CommandHandler("signals", self._handle_signals))

        # Message handlers
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id

        # Add to authorized users if admin
        if user_id == self.settings.telegram_admin_id:
            self.authorized_users.add(user_id)

        welcome_message = """
🤖 XAUUSD Gold Trading Bot

Welcome to the XAUUSD Gold Trading System!

Available commands:
/start - Start the bot
/help - Show help
/status - System status
/subscribe - Subscribe to notifications
/unsubscribe - Unsubscribe from notifications
/balance - Account balance
/positions - Open positions
/signals - Recent signals

📈 Smart Money Concepts Trading
"""

        await update.message.reply_text(welcome_message)

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
📚 Help - XAUUSD Trading Bot

Commands:
/start - Initialize the bot
/help - Show this help message
/status - Check system status
/subscribe [type] - Subscribe to notifications (signals, trades, all)
/unsubscribe [type] - Unsubscribe from notifications
/balance - View account balance
/positions - View open positions
/signals - View recent trading signals

Notification Types:
- signals: Trading signals only
- trades: Trade executions only
- all: All notifications

Example:
/subscribe signals - Subscribe to trading signals
/unsubscribe all - Unsubscribe from all notifications

🔒 Security: Only authorized users can access trading functions.
"""

        await update.message.reply_text(help_message)

    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized access")
            return

        status_message = f"""
📊 System Status

🤖 Bot: {"✅ Running" if self.is_running else "❌ Stopped"}
👥 Users: {len(self.authorized_users)} authorized
📈 Signals: Active
💼 Trades: Active

⏰ Time: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC
"""

        await update.message.reply_text(status_message)

    async def _handle_subscribe(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /subscribe command."""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized access")
            return

        # Get subscription type
        subscription_type = "all"  # Default
        if context.args:
            subscription_type = context.args[0].lower()

        if subscription_type not in ["signals", "trades", "all"]:
            await update.message.reply_text(
                "❌ Invalid subscription type. Use: signals, trades, or all"
            )
            return

        # Update user preferences
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id]["subscriptions"] = subscription_type

        message = f"""
✅ Subscription Updated

You are now subscribed to: {subscription_type.upper()}

You will receive notifications for:
- signals: Trading signals
- trades: Trade executions
- all: All notifications

Use /unsubscribe to stop receiving notifications.
"""

        await update.message.reply_text(message)

    async def _handle_unsubscribe(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /unsubscribe command."""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized access")
            return

        # Remove subscriptions
        if user_id in self.user_preferences:
            self.user_preferences[user_id].pop("subscriptions", None)

        await update.message.reply_text("✅ Unsubscribed from all notifications")

    async def _handle_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command."""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized access")
            return

        # Get balance from trade manager
        # This would be implemented by calling the trade manager
        balance_info = await self._get_balance_info()

        message = f"""
💰 Account Balance

Balance: ${balance_info.get("balance", "N/A")}
Equity: ${balance_info.get("equity", "N/A")}
Margin: ${balance_info.get("margin", "N/A")}
Free Margin: ${balance_info.get("free_margin", "N/A")}
Margin Level: {balance_info.get("margin_level", "N/A")}%

📈 Profit: ${balance_info.get("profit", "N/A")}
"""

        await update.message.reply_text(message)

    async def _handle_positions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /positions command."""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized access")
            return

        # Get positions from trade manager
        positions = await self._get_positions()

        if not positions:
            await update.message.reply_text("📊 No open positions")
            return

        message = "📊 Open Positions\n\n"

        for pos in positions[:10]:  # Limit to 10 positions
            profit_emoji = "🟢" if pos["profit"] >= 0 else "🔴"
            message += f"""
{profit_emoji} {pos["symbol"]}
Type: {pos["type"]}
Volume: {pos["volume"]}
Entry: ${pos["price_open"]}
Current: ${pos["price_current"]}
Profit: ${pos["profit"]:.2f}
---
"""

        await update.message.reply_text(message)

    async def _handle_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command."""
        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized access")
            return

        # Get recent signals
        signals = await self._get_recent_signals()

        if not signals:
            await update.message.reply_text("📈 No recent signals")
            return

        message = "📈 Recent Signals\n\n"

        for signal in signals[:5]:  # Limit to 5 signals
            confidence_emoji = (
                "🔥"
                if signal.confidence >= 0.8
                else "⚡"
                if signal.confidence >= 0.6
                else "💡"
            )
            message += f"""
{confidence_emoji} {signal.symbol}
Signal: {signal.signal_type}
Entry: ${signal.entry_price}
SL: ${signal.stop_loss}
TP: ${signal.take_profit}
Confidence: {signal.confidence:.1%}
Time: {signal.timestamp.strftime("%H:%M")}
---
"""

        await update.message.reply_text(message)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        user_id = update.effective_user.id
        message_text = update.message.text.lower()

        # Handle common queries
        if "help" in message_text:
            await self._handle_help(update, context)
        elif "status" in message_text:
            await self._handle_status(update, context)
        else:
            await update.message.reply_text("Use /help to see available commands")

    async def send_signal_notification(self, signal: Signal):
        """Send trading signal notification."""
        if not self.bot:
            self.logger.info(f"MOCK Signal Notification: {signal.signal_id}")
            return

        message = self._format_signal_message(signal)

        # Send to subscribed users
        for user_id, preferences in self.user_preferences.items():
            if self._should_send_notification(user_id, "signals"):
                try:
                    await self.bot.send_message(
                        chat_id=user_id, text=message, parse_mode="Markdown"
                    )
                except Exception as e:
                    self.logger.error(f"Error sending signal to user {user_id}: {e}")

    async def send_trade_notification(self, trade: Trade):
        """Send trade execution notification."""
        if not self.bot:
            self.logger.info(f"MOCK Trade Notification: {trade.trade_id}")
            return

        message = self._format_trade_message(trade)

        # Send to subscribed users
        for user_id, preferences in self.user_preferences.items():
            if self._should_send_notification(user_id, "trades"):
                try:
                    await self.bot.send_message(
                        chat_id=user_id, text=message, parse_mode="Markdown"
                    )
                except Exception as e:
                    self.logger.error(f"Error sending trade to user {user_id}: {e}")

    async def send_alert(self, title: str, message: str, level: str = "info"):
        """Send general alert notification."""
        if not self.bot:
            self.logger.info(f"MOCK Alert: {title} - {message}")
            return

        alert_message = f"""
🚨 *{title}*

{message}

⏰ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC
"""

        # Send to all authorized users
        for user_id in self.authorized_users:
            try:
                await self.bot.send_message(
                    chat_id=user_id, text=alert_message, parse_mode="Markdown"
                )
            except Exception as e:
                self.logger.error(f"Error sending alert to user {user_id}: {e}")

    def _format_signal_message(self, signal: Signal) -> str:
        """Format signal message for Telegram."""
        confidence_emoji = (
            "🔥"
            if signal.confidence >= 0.8
            else "⚡"
            if signal.confidence >= 0.6
            else "💡"
        )
        direction_emoji = "🟢" if signal.signal_type == "BUY" else "🔴"

        return f"""
{direction_emoji} *{signal.signal_type} Signal - {signal.symbol}*

{confidence_emoji} Confidence: {signal.confidence:.1%}

📍 Entry: ${signal.entry_price}
🛑 Stop Loss: ${signal.stop_loss}
🎯 Take Profit: ${signal.take_profit}

📊 Analysis: {signal.reasoning}

⏰ {signal.timestamp.strftime("%Y-%m-%d %H:%M:%S")} UTC
"""

    def _format_trade_message(self, trade: Trade) -> str:
        """Format trade message for Telegram."""
        status_emoji = (
            "✅"
            if trade.status == "EXECUTED"
            else "⏳"
            if trade.status == "PENDING"
            else "❌"
        )
        direction_emoji = "🟢" if trade.trade_type == "BUY" else "🔴"

        return f"""
{status_emoji} *Trade {trade.status.title()}*

{direction_emoji} {trade.trade_type} {trade.symbol}

💰 Volume: {trade.volume}
📍 Entry: ${trade.price}
🛑 SL: ${trade.stop_loss}
🎯 TP: ${trade.take_profit}

💵 P&L: ${trade.profit_loss:.2f}

⏰ {trade.timestamp.strftime("%Y-%m-%d %H:%M:%S")} UTC
"""

    def _is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized."""
        return (
            user_id in self.authorized_users
            or user_id == self.settings.telegram_admin_id
        )

    def _should_send_notification(self, user_id: int, notification_type: str) -> bool:
        """Check if user should receive notification."""
        if user_id not in self.user_preferences:
            return False

        subscriptions = self.user_preferences[user_id].get("subscriptions", "all")

        if subscriptions == "all":
            return True
        elif subscriptions == notification_type:
            return True

        return False

    async def _get_balance_info(self) -> dict:
        """Get account balance information."""
        # This would be implemented by calling the trade manager
        # For now, return mock data
        return {
            "balance": 10000.0,
            "equity": 10250.0,
            "margin": 500.0,
            "free_margin": 9750.0,
            "margin_level": 2050.0,
            "profit": 250.0,
        }

    async def _get_positions(self) -> List[dict]:
        """Get open positions."""
        # This would be implemented by calling the trade manager
        # For now, return mock data
        return []

    async def _get_recent_signals(self) -> List[Signal]:
        """Get recent trading signals."""
        # This would be implemented by calling the signal manager
        # For now, return mock data
        return []

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "is_running": self.is_running,
            "authorized_users": len(self.authorized_users),
            "total_users": len(self.user_preferences),
            "bot_token_configured": bool(self.settings.telegram_bot_token),
        }
