"""
Notifications module for XAUUSD Gold Trading System.

Provides notification services including:
- Telegram bot notifications
- Email notifications (future)
- SMS notifications (future)
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from .telegram_service import TelegramService

__all__ = ["TelegramService"]
