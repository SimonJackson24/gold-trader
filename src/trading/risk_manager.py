"""
Risk manager for XAUUSD Gold Trading System.

Handles position sizing, risk calculation,
and risk management rules.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from typing import Dict, Optional
from decimal import Decimal

from ..config import get_settings


class RiskManager:
    """
    Risk manager implementation.

    Manages trading risk, position sizing,
    and risk management rules.
    """

    def __init__(self):
        """Initialize risk manager."""
        self.settings = get_settings()

    def calculate_position_size(
        self,
        account_balance: float,
        risk_amount: float,
        stop_loss_pips: Decimal,
        lot_size_step: float = 0.01,
        max_lot_size: float = 1.0,
    ) -> Decimal:
        """
        Calculate optimal position size.

        Args:
            account_balance: Account balance
            risk_amount: Risk amount in currency
            stop_loss_pips: Stop loss in pips
            lot_size_step: Minimum lot size step
            max_lot_size: Maximum lot size

        Returns:
            Calculated position size
        """
        # Calculate position size based on risk
        # Simplified calculation: Risk / (Stop Loss * Pip Value per Lot)
        # Assuming $10 per pip per standard lot
        pip_value_per_lot = Decimal("10")
        position_size = risk_amount / (stop_loss_pips * pip_value_per_lot)

        # Round to valid step size
        position_size = (position_size // lot_size_step) * lot_size_step

        # Apply limits
        position_size = max(position_size, lot_size_step)
        position_size = min(position_size, max_lot_size)

        return Decimal(str(position_size))

    def calculate_risk_amount(
        self, account_balance: float, risk_percentage: float
    ) -> float:
        """
        Calculate risk amount per trade.

        Args:
            account_balance: Account balance
            risk_percentage: Risk percentage

        Returns:
            Risk amount in currency
        """
        return (account_balance * risk_percentage) / 100.0

    def validate_trade_parameters(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
        account_balance: float,
        position_size: Decimal,
    ) -> Dict[str, str]:
        """
        Validate trade parameters against risk rules.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss
            take_profit: Take profit
            account_balance: Account balance
            position_size: Position size

        Returns:
            Validation results
        """
        validation = {"is_valid": True, "warnings": [], "errors": []}

        # Check minimum risk:reward ratio
        risk_pips = abs(entry_price - stop_loss)
        reward_pips = abs(take_profit - entry_price)

        if reward_pips > 0 and risk_pips > 0:
            rr_ratio = float(reward_pips / risk_pips)
            if rr_ratio < self.settings.trading.min_risk_reward:
                validation["is_valid"] = False
                validation["errors"].append(
                    f"Risk:reward ratio {rr_ratio:.2f} below minimum {self.settings.trading.min_risk_reward}"
                )

        # Check maximum position size
        if position_size > self.settings.trading.max_lot_size:
            validation["warnings"].append(
                f"Position size {position_size} exceeds maximum {self.settings.trading.max_lot_size}"
            )

        # Check position size against account balance
        max_position_by_balance = account_balance * 0.02  # 2% risk per trade max
        if position_size > max_position_by_balance:
            validation["warnings"].append(
                f"Position size {position_size} exceeds 2% of account balance"
            )

        # Check risk percentage
        risk_amount = self.calculate_risk_amount(
            account_balance, self.settings.trading.risk_per_trade
        )
        actual_risk_percentage = (
            (risk_pips * position_size * 10) / account_balance * 100
        )

        if actual_risk_percentage > self.settings.trading.max_daily_risk:
            validation["warnings"].append(
                f"Trade risk {actual_risk_percentage:.2f}% exceeds daily maximum {self.settings.trading.max_daily_risk}%"
            )

        return validation

    def get_risk_metrics(
        self, account_balance: float, open_trades: list
    ) -> Dict[str, float]:
        """
        Calculate current risk metrics.

        Args:
            account_balance: Account balance
            open_trades: List of open trades

        Returns:
            Risk metrics dictionary
        """
        total_risk = 0.0
        total_position = 0.0

        for trade in open_trades:
            if trade.position_size and trade.entry_price and trade.stop_loss:
                risk_pips = abs(trade.entry_price - trade.stop_loss)
                risk_amount = (
                    risk_pips * trade.position_size * 10
                ) / 100  # Convert to currency
                total_risk += risk_amount
                total_position += float(trade.position_size)

        risk_percentage = (
            (total_risk / account_balance * 100) if account_balance > 0 else 0
        )

        return {
            "total_risk": total_risk,
            "total_position": total_position,
            "risk_percentage": risk_percentage,
            "number_of_trades": len(open_trades),
        }

    def check_daily_risk_limit(
        self, account_balance: float, additional_risk: float = 0.0
    ) -> bool:
        """
        Check if additional trade would exceed daily risk limit.

        Args:
            account_balance: Account balance
            additional_risk: Additional risk amount

        Returns:
            True if within limit
        """
        current_risk = self.get_risk_metrics(account_balance, [])["total_risk"]
        max_daily_risk = account_balance * (self.settings.trading.max_daily_risk / 100)

        return (current_risk + additional_risk) <= max_daily_risk

    def calculate_correlation_risk(self, trades: list) -> float:
        """
        Calculate portfolio correlation risk.

        Args:
            trades: List of open trades

        Returns:
            Correlation risk score (0.0 to 1.0)
        """
        if len(trades) < 2:
            return 0.0

        # Simple correlation check based on direction
        # If multiple trades in same direction, increase risk
        same_direction_count = sum(
            1 for t in trades if t.direction == trades[0].direction
        )
        total_trades = len(trades)

        if same_direction_count > 1:
            # Higher correlation risk
            return 0.3 + (same_direction_count / total_trades) * 0.4

        # Lower correlation risk (trades in different directions)
        elif same_direction_count == 0:
            return 0.1

        return 0.0

    def get_portfolio_heatmap(self, account_balance: float) -> Dict[str, str]:
        """
        Get portfolio risk heatmap.

        Args:
            account_balance: Account balance

        Returns:
            Risk heatmap data
        """
        risk_levels = {
            "LOW": account_balance * 0.01,  # 1% risk
            "MEDIUM": account_balance * 0.02,  # 2% risk
            "HIGH": account_balance * 0.03,  # 3% risk
            "CRITICAL": account_balance * 0.05,  # 5% risk
        }

        return {
            "risk_levels": risk_levels,
            "recommended_max_risk": risk_levels["MEDIUM"],
            "diversification_score": 0.8,  # Balanced portfolio
            "correlation_alert": False,
        }
