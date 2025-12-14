"""
Notifications module for XAUUSD Gold Trading System.

Provides notification services including:
- Telegram bot notifications
- Email notifications (future)
- SMS notifications (future)
"""

from .telegram_service import TelegramService

__all__ = [
    'TelegramService'
]