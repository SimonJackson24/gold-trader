"""
Telegram configuration for XAUUSD Gold Trading System.

Manages Telegram bot settings, notification preferences,
and message formatting options.
"""

from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class TelegramConfig(BaseSettings):
    """
    Telegram bot configuration.
    
    Manages bot authentication, channel settings,
    and notification preferences.
    """
    
    # Bot authentication
    bot_token: str = Field(default="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz", env="TELEGRAM_BOT_TOKEN")
    chat_id: str = Field(default="-1001234567890", env="TELEGRAM_CHAT_ID")
    
    # Channel settings
    channel_username: Optional[str] = Field(default=None, env="TELEGRAM_CHANNEL_USERNAME")
    channel_id: Optional[str] = Field(default=None, env="TELEGRAM_CHANNEL_ID")
    
    # Notification settings
    enable_signals: bool = Field(default=True, env="TELEGRAM_ENABLE_SIGNALS")
    enable_trade_updates: bool = Field(default=True, env="TELEGRAM_ENABLE_TRADE_UPDATES")
    enable_daily_report: bool = Field(default=True, env="TELEGRAM_ENABLE_DAILY_REPORT")
    enable_error_alerts: bool = Field(default=True, env="TELEGRAM_ENABLE_ERRORS")
    
    # Message formatting
    use_emojis: bool = Field(default=True, env="TELEGRAM_USE_EMOJIS")
    use_markdown: bool = Field(default=True, env="TELEGRAM_USE_MARKDOWN")
    include_charts: bool = Field(default=False, env="TELEGRAM_INCLUDE_CHARTS")
    chart_resolution: str = Field(default="M15", env="TELEGRAM_CHART_RESOLUTION")
    
    # Rate limiting
    messages_per_minute: int = Field(default=5, ge=1, le=30, env="TELEGRAM_MESSAGES_PER_MINUTE")
    burst_limit: int = Field(default=10, ge=1, le=50, env="TELEGRAM_BURST_LIMIT")
    
    # Retry settings
    max_retries: int = Field(default=3, ge=1, le=10, env="TELEGRAM_MAX_RETRIES")
    retry_delay_seconds: int = Field(default=5, ge=1, le=60, env="TELEGRAM_RETRY_DELAY")
    
    # Timeout settings
    connection_timeout: int = Field(default=30, ge=5, le=120, env="TELEGRAM_CONNECTION_TIMEOUT")
    read_timeout: int = Field(default=60, ge=10, le=300, env="TELEGRAM_READ_TIMEOUT")
    
    # Webhook settings
    use_webhook: bool = Field(default=False, env="TELEGRAM_USE_WEBHOOK")
    webhook_url: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    webhook_secret: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_SECRET")
    
    # Message templates
    signal_template: str = Field(
        default="🔔 {direction} {instrument} SIGNAL 🔔\n\n"
                "📊 Setup: {setup_type}\n"
                "📈 Entry: {entry_price}\n"
                "🛑 SL: {stop_loss}\n"
                "🎯 TP1: {tp1} | TP2: {tp2}\n"
                "⚖️ R:R: {rr_ratio}\n"
                "🎲 Confidence: {confidence}%\n"
                "⏰ Session: {session}\n"
                "🆔 ID: {signal_id}",
        env="TELEGRAM_SIGNAL_TEMPLATE"
    )
    
    trade_update_template: str = Field(
        default="📊 TRADE UPDATE 📊\n\n"
                     "🆔 Signal: {signal_id}\n"
                     "💰 Current P/L: {pl} ({pips} pips)\n"
                     "📈 Progress: {progress_bar}\n"
                     "📍 Price: {current_price}",
        env="TELEGRAM_TRADE_UPDATE_TEMPLATE"
    )
    
    daily_report_template: str = Field(
        default="📅 DAILY REPORT 📅\n\n"
                         "📊 Date: {date}\n"
                         "💰 Total P/L: {total_pl}\n"
                         "📈 Win Rate: {win_rate}%\n"
                         "🎯 Total Trades: {total_trades}\n"
                         "✅ Wins: {wins}\n"
                         "❌ Losses: {losses}",
        env="TELEGRAM_DAILY_REPORT_TEMPLATE"
    )
    
    error_template: str = Field(
        default="🚨 ERROR ALERT 🚨\n\n"
                   "⚠️ Error: {error_type}\n"
                   "📝 Message: {message}\n"
                   "⏰ Time: {timestamp}\n"
                   "📍 Component: {component}",
        env="TELEGRAM_ERROR_TEMPLATE"
    )
    
    class Config:
        env_prefix = "TELEGRAM_"
    
    @validator('bot_token')
    def validate_bot_token(cls, v):
        """Validate bot token format."""
        if not v or len(v) < 20:
            raise ValueError('Invalid bot token format')
        return v
    
    @validator('chat_id')
    def validate_chat_id(cls, v):
        """Validate chat ID format."""
        if not v:
            raise ValueError('Chat ID is required')
        return v
    
    @validator('chart_resolution')
    def validate_chart_resolution(cls, v):
        """Validate chart resolution."""
        valid_resolutions = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
        if v.upper() not in valid_resolutions:
            raise ValueError(f'Chart resolution must be one of: {valid_resolutions}')
        return v.upper()
    
    def validate(self) -> bool:
        """
        Validate Telegram configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Validate required fields
        if not self.bot_token:
            errors.append("Bot token is required")
        
        if not self.chat_id:
            errors.append("Chat ID is required")
        
        # Validate rate limiting
        if self.burst_limit < self.messages_per_minute:
            errors.append("Burst limit should be greater than or equal to messages per minute")
        
        # Validate timeouts
        if self.read_timeout <= self.connection_timeout:
            errors.append("Read timeout should be greater than connection timeout")
        
        # Validate webhook settings
        if self.use_webhook and not self.webhook_url:
            errors.append("Webhook URL is required when using webhook mode")
        
        if self.use_webhook and not self.webhook_secret:
            errors.append("Webhook secret is required when using webhook mode")
        
        if errors:
            raise ValueError("Telegram configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    def get_api_url(self) -> str:
        """
        Get Telegram bot API URL.
        
        Returns:
            Telegram API URL with bot token
        """
        return f"https://api.telegram.org/bot{self.bot_token}"
    
    def get_file_url(self, file_path: str) -> str:
        """
        Get Telegram file URL.
        
        Args:
            file_path: File path on Telegram servers
            
        Returns:
            Complete file URL
        """
        return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
    
    def format_signal_message(self, signal_data: dict) -> str:
        """
        Format signal message using template.
        
        Args:
            signal_data: Dictionary with signal information
            
        Returns:
            Formatted message string
        """
        return self.signal_template.format(**signal_data)
    
    def format_trade_update(self, trade_data: dict) -> str:
        """
        Format trade update message using template.
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            Formatted message string
        """
        return self.trade_update_template.format(**trade_data)
    
    def format_daily_report(self, report_data: dict) -> str:
        """
        Format daily report message using template.
        
        Args:
            report_data: Dictionary with report information
            
        Returns:
            Formatted message string
        """
        return self.daily_report_template.format(**report_data)
    
    def format_error_message(self, error_data: dict) -> str:
        """
        Format error message using template.
        
        Args:
            error_data: Dictionary with error information
            
        Returns:
            Formatted message string
        """
        return self.error_template.format(**error_data)
    
    def create_progress_bar(self, current_price: float, entry_price: float, 
                          tp1: float, tp2: float) -> str:
        """
        Create progress bar for trade updates.
        
        Args:
            current_price: Current price
            entry_price: Entry price
            tp1: Take profit 1
            tp2: Take profit 2
            
        Returns:
            Progress bar string
        """
        if entry_price < tp2:  # Long trade
            total_range = tp2 - entry_price
            progress = min(1.0, max(0.0, (current_price - entry_price) / total_range))
        else:  # Short trade
            total_range = entry_price - tp2
            progress = min(1.0, max(0.0, (entry_price - current_price) / total_range))
        
        filled_blocks = int(progress * 10)
        empty_blocks = 10 - filled_blocks
        
        if self.use_emojis:
            return f"[{'█' * filled_blocks}{'░' * empty_blocks}] {int(progress * 100)}%"
        else:
            return f"[{'=' * filled_blocks}{' ' * empty_blocks}] {int(progress * 100)}%"
    
    def get_emoji_for_direction(self, direction: str) -> str:
        """
        Get emoji for trade direction.
        
        Args:
            direction: Trade direction (BUY/SELL)
            
        Returns:
            Direction emoji
        """
        if not self.use_emojis:
            return ""
        
        return "📈" if direction.upper() == "BUY" else "📉"
    
    def get_emoji_for_result(self, profit: float) -> str:
        """
        Get emoji for trade result.
        
        Args:
            profit: Trade profit (positive/negative)
            
        Returns:
            Result emoji
        """
        if not self.use_emojis:
            return ""
        
        if profit > 0:
            return "✅"
        elif profit < 0:
            return "❌"
        else:
            return "➖"
    
    def to_dict(self) -> dict:
        """Convert Telegram config to dictionary (excluding sensitive data)."""
        return {
            'chat_id': self.chat_id,
            'channel_username': self.channel_username,
            'channel_id': self.channel_id,
            'enable_signals': self.enable_signals,
            'enable_trade_updates': self.enable_trade_updates,
            'enable_daily_report': self.enable_daily_report,
            'enable_error_alerts': self.enable_error_alerts,
            'use_emojis': self.use_emojis,
            'use_markdown': self.use_markdown,
            'include_charts': self.include_charts,
            'chart_resolution': self.chart_resolution,
            'messages_per_minute': self.messages_per_minute,
            'burst_limit': self.burst_limit,
            'max_retries': self.max_retries,
            'retry_delay_seconds': self.retry_delay_seconds,
            'connection_timeout': self.connection_timeout,
            'read_timeout': self.read_timeout,
            'use_webhook': self.use_webhook,
            'webhook_url': self.webhook_url if self.webhook_url else None,
            'webhook_secret': '***' if self.webhook_secret else None
        }