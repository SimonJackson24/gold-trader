"""
Trading configuration for XAUUSD Gold Trading System.

Manages trading parameters, risk management settings,
and session-based configurations.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from typing import Dict, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from decimal import Decimal


class SessionConfig(BaseSettings):
    """
    Trading session configuration.

    Defines risk multipliers and trading parameters
    for different trading sessions.
    """

    name: str
    start_hour: int  # UTC hour
    end_hour: int  # UTC hour
    risk_multiplier: float = Field(default=1.0, ge=0.1, le=3.0)
    max_trades: int = Field(default=2, ge=1, le=10)
    min_confidence: float = Field(default=0.75, ge=0.5, le=1.0)
    enabled: bool = Field(default=True)

    @validator("start_hour", "end_hour")
    def validate_hours(cls, v):
        if not (0 <= v <= 23):
            raise ValueError("Hour must be between 0 and 23")
        return v

    def is_active(self, current_hour: int) -> bool:
        """
        Check if session is currently active.

        Args:
            current_hour: Current UTC hour (0-23)

        Returns:
            True if session is active
        """
        if not self.enabled:
            return False

        if self.start_hour <= self.end_hour:
            return self.start_hour <= current_hour < self.end_hour
        else:  # Session crosses midnight
            return current_hour >= self.start_hour or current_hour < self.end_hour

    def to_dict(self) -> dict:
        """Convert session config to dictionary."""
        return {
            "name": self.name,
            "start_hour": self.start_hour,
            "end_hour": self.end_hour,
            "risk_multiplier": self.risk_multiplier,
            "max_trades": self.max_trades,
            "min_confidence": self.min_confidence,
            "enabled": self.enabled,
        }


class TradingConfig(BaseSettings):
    """
    Main trading configuration.

    Manages risk management, position sizing,
    and trading parameters.
    """

    # Risk management
    risk_per_trade: float = Field(default=1.0, ge=0.1, le=5.0, env="RISK_PER_TRADE")
    max_daily_risk: float = Field(default=5.0, ge=1.0, le=20.0, env="MAX_DAILY_RISK")
    max_concurrent_trades: int = Field(
        default=2, ge=1, le=10, env="MAX_CONCURRENT_TRADES"
    )
    min_risk_reward: float = Field(default=2.0, ge=1.5, le=10.0, env="MIN_RISK_REWARD")

    # Position sizing
    default_lot_size: float = Field(
        default=0.01, ge=0.01, le=10.0, env="DEFAULT_LOT_SIZE"
    )
    max_lot_size: float = Field(default=1.0, ge=0.01, le=10.0, env="MAX_LOT_SIZE")
    lot_size_step: float = Field(default=0.01, ge=0.01, le=1.0, env="LOT_SIZE_STEP")

    # Stop loss and take profit
    sl_buffer_pips: int = Field(default=5, ge=1, le=50, env="SL_BUFFER_PIPS")
    tp1_percentage: float = Field(default=0.5, ge=0.1, le=0.9, env="TP1_PERCENTAGE")
    tp2_percentage: float = Field(default=1.0, ge=0.5, le=2.0, env="TP2_PERCENTAGE")
    move_to_breakeven_pips: int = Field(default=15, ge=5, le=100, env="MOVE_TO_BE_PIPS")

    # Entry and exit rules
    max_slippage_pips: int = Field(default=3, ge=1, le=20, env="MAX_SLIPPAGE_PIPS")
    entry_timeout_minutes: int = Field(
        default=30, ge=5, le=240, env="ENTRY_TIMEOUT_MINUTES"
    )
    signal_expiry_minutes: int = Field(
        default=240, ge=60, le=1440, env="SIGNAL_EXPIRY_MINUTES"
    )

    # Trading sessions
    asian_session: SessionConfig = Field(
        default_factory=lambda: SessionConfig(
            name="ASIAN", start_hour=0, end_hour=8, risk_multiplier=0.5
        )
    )
    london_session: SessionConfig = Field(
        default_factory=lambda: SessionConfig(
            name="LONDON", start_hour=8, end_hour=13, risk_multiplier=1.0
        )
    )
    ny_session: SessionConfig = Field(
        default_factory=lambda: SessionConfig(
            name="NY", start_hour=13, end_hour=17, risk_multiplier=1.5
        )
    )
    ny_overlap_session: SessionConfig = Field(
        default_factory=lambda: SessionConfig(
            name="NY_OVERLAP", start_hour=13, end_hour=17, risk_multiplier=2.0
        )
    )

    # Account settings
    account_balance: float = Field(default=10000.0, ge=100.0, env="ACCOUNT_BALANCE")
    account_currency: str = Field(default="USD", env="ACCOUNT_CURRENCY")
    leverage: int = Field(default=100, ge=1, le=1000, env="LEVERAGE")

    # Trading restrictions
    no_trading_friday: bool = Field(default=False, env="NO_TRADING_FRIDAY")
    no_trading_weekend: bool = Field(default=True, env="NO_TRADING_WEEKEND")
    news_filter_minutes: int = Field(
        default=30, ge=0, le=120, env="NEWS_FILTER_MINUTES"
    )

    class Config:
        env_prefix = "TRADING_"

    def validate(self) -> bool:
        """
        Validate trading configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        errors = []

        # Validate risk parameters
        if self.risk_per_trade > self.max_daily_risk:
            errors.append("Risk per trade cannot exceed max daily risk")

        if self.min_risk_reward < 1.5:
            errors.append("Minimum risk:reward ratio should be at least 1.5")

        # Validate position sizing
        if self.default_lot_size > self.max_lot_size:
            errors.append("Default lot size cannot exceed maximum lot size")

        # Validate TP percentages
        if self.tp1_percentage + self.tp2_percentage != 1.5:
            errors.append("TP1 and TP2 percentages should sum to 1.5 (50% and 100%)")

        # Validate account settings
        if self.account_balance <= 0:
            errors.append("Account balance must be positive")

        if self.leverage <= 0:
            errors.append("Leverage must be positive")

        # Validate sessions
        sessions = [
            self.asian_session,
            self.london_session,
            self.ny_session,
            self.ny_overlap_session,
        ]

        for session in sessions:
            try:
                session.validate()
            except ValueError as e:
                errors.append(f"Session {session.name}: {e}")

        if errors:
            raise ValueError(
                "Trading configuration validation failed:\n"
                + "\n".join(f"- {error}" for error in errors)
            )

        return True

    def get_session_config(self, session_name: str) -> Optional[SessionConfig]:
        """
        Get session configuration by name.

        Args:
            session_name: Name of the session

        Returns:
            SessionConfig or None if not found
        """
        sessions = {
            "ASIAN": self.asian_session,
            "LONDON": self.london_session,
            "NY": self.ny_session,
            "NY_OVERLAP": self.ny_overlap_session,
        }
        return sessions.get(session_name.upper())

    def get_current_session(self, current_hour: int) -> Optional[str]:
        """
        Get current trading session based on hour.

        Args:
            current_hour: Current UTC hour

        Returns:
            Session name or None if no active session
        """
        sessions = [
            ("ASIAN", self.asian_session),
            ("LONDON", self.london_session),
            ("NY", self.ny_session),
            ("NY_OVERLAP", self.ny_overlap_session),
        ]

        for name, session in sessions:
            if session.is_active(current_hour):
                return name

        return None

    def calculate_position_size(
        self, risk_amount: float, stop_loss_pips: Decimal
    ) -> Decimal:
        """
        Calculate position size based on risk and stop loss.

        Args:
            risk_amount: Risk amount in account currency
            stop_loss_pips: Stop loss in pips

        Returns:
            Position size in lots
        """
        if stop_loss_pips == 0:
            return Decimal("0")

        # Simplified calculation: (Risk Amount) / (Stop Loss * Pip Value * Lot Size)
        # Assuming $10 per pip per standard lot
        pip_value_per_lot = 10.0
        position_size = risk_amount / (float(stop_loss_pips) * pip_value_per_lot)

        # Round to valid lot size
        position_size = round(position_size / self.lot_size_step) * self.lot_size_step

        # Apply limits
        position_size = min(position_size, self.max_lot_size)
        position_size = max(position_size, self.default_lot_size)

        return Decimal(str(position_size))

    def get_risk_amount(self) -> float:
        """
        Get risk amount per trade.

        Returns:
            Risk amount in account currency
        """
        return (self.account_balance * self.risk_per_trade) / 100.0

    def can_trade_now(self, current_hour: int, is_weekend: bool = False) -> bool:
        """
        Check if trading is allowed at current time.

        Args:
            current_hour: Current UTC hour
            is_weekend: Whether it's weekend

        Returns:
            True if trading is allowed
        """
        # Check weekend
        if is_weekend and self.no_trading_weekend:
            return False

        # Check Friday
        if current_hour >= 20 and self.no_trading_friday:  # Friday evening UTC
            return False

        # Check session
        current_session = self.get_current_session(current_hour)
        if not current_session:
            return False

        session_config = self.get_session_config(current_session)
        return session_config and session_config.enabled

    def to_dict(self) -> dict:
        """Convert trading config to dictionary."""
        return {
            "risk_per_trade": self.risk_per_trade,
            "max_daily_risk": self.max_daily_risk,
            "max_concurrent_trades": self.max_concurrent_trades,
            "min_risk_reward": self.min_risk_reward,
            "default_lot_size": self.default_lot_size,
            "max_lot_size": self.max_lot_size,
            "lot_size_step": self.lot_size_step,
            "sl_buffer_pips": self.sl_buffer_pips,
            "tp1_percentage": self.tp1_percentage,
            "tp2_percentage": self.tp2_percentage,
            "move_to_breakeven_pips": self.move_to_breakeven_pips,
            "max_slippage_pips": self.max_slippage_pips,
            "entry_timeout_minutes": self.entry_timeout_minutes,
            "signal_expiry_minutes": self.signal_expiry_minutes,
            "asian_session": self.asian_session.to_dict(),
            "london_session": self.london_session.to_dict(),
            "ny_session": self.ny_session.to_dict(),
            "ny_overlap_session": self.ny_overlap_session.to_dict(),
            "account_balance": self.account_balance,
            "account_currency": self.account_currency,
            "leverage": self.leverage,
            "no_trading_friday": self.no_trading_friday,
            "no_trading_weekend": self.no_trading_weekend,
            "news_filter_minutes": self.news_filter_minutes,
        }
