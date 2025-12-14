"""
Signal generator for XAUUSD Gold Trading System.

Converts SMC analysis results into actionable trading signals
with proper risk management and validation.
"""

import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from ..models.signal import TradingSignal, SignalStatus, SessionType
from ..models.market_data import PriceLevel
from ..analysis.confluence_analyzer import ConfluenceAnalysis
from ..config import get_settings


class SignalGenerator:
    """
    Signal generator implementation.
    
    Creates trading signals from SMC analysis
    with proper risk management.
    """
    
    def __init__(self):
        """Initialize signal generator."""
        self.settings = get_settings()
        self.logger = __import__('logging').getLogger(__name__)
    
    async def generate_signal(self, analysis: ConfluenceAnalysis, 
                          current_price: Decimal) -> Optional[TradingSignal]:
        """
        Generate trading signal from analysis.
        
        Args:
            analysis: Confluence analysis results
            current_price: Current market price
            
        Returns:
            Trading signal or None
        """
        # Check if signal meets requirements
        if not analysis.meets_threshold(self.settings.smc.confluence_threshold):
            return None
        
        # Generate signal ID
        signal_id = self._generate_signal_id()
        
        # Determine signal direction and setup type
        direction, setup_type = self._determine_signal_direction(analysis, current_price)
        
        # Calculate entry price
        entry_price = self._calculate_entry_price(analysis, current_price, direction)
        
        # Calculate stop loss and take profits
        stop_loss, tp1, tp2 = self._calculate_price_levels(
            entry_price, direction, analysis
        )
        
        # Calculate risk metrics
        position_size, risk_percentage = self._calculate_position_risk(
            entry_price, stop_loss, direction
        )
        
        # Calculate risk:reward ratio
        risk_reward_ratio = self._calculate_risk_reward(
            entry_price, stop_loss, tp2, direction
        )
        
        # Create signal
        signal = TradingSignal(
            signal_id=signal_id,
            instrument="XAUUSD",
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward_ratio=risk_reward_ratio,
            position_size=position_size,
            risk_percentage=risk_percentage,
            setup_type=setup_type,
            market_structure=analysis.market_structure,
            confluence_factors=analysis.get_confluence_factors(),
            confidence_score=analysis.confidence,
            h4_context=self._create_context_description(analysis.h4_analysis),
            h1_context=self._create_context_description(analysis.h1_analysis),
            m15_context=self._create_context_description(analysis.m15_analysis),
            session=self._get_current_session(),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=self.settings.trading.signal_expiry_minutes),
            status=SignalStatus.ACTIVE
        )
        
        self.logger.info(
            f"Generated signal {signal_id}: {direction} {setup_type} "
            f"at {entry_price} with RR {risk_reward_ratio:.2f}"
        )
        
        return signal
    
    def _generate_signal_id(self) -> str:
        """
        Generate unique signal ID.
        
        Returns:
            Unique signal identifier
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"XAU_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    def _determine_signal_direction(self, analysis: ConfluenceAnalysis, 
                                  current_price: Decimal) -> tuple[str, str]:
        """
        Determine signal direction and setup type.
        
        Args:
            analysis: Confluence analysis results
            current_price: Current market price
            
        Returns:
            Tuple of (direction, setup_type)
        """
        # Analyze confluence factors
        factors = analysis.get_confluence_factors()
        
        # Determine direction based on dominant factors
        bullish_factors = ["FVG", "BULLISH_CONFIRMATION", "LIQUIDITY_SWEEP_BUY"]
        bearish_factors = ["FVG", "BEARISH_CONFIRMATION", "LIQUIDITY_SWEEP_SELL"]
        
        bullish_count = sum(1 for f in factors if f in bullish_factors)
        bearish_count = sum(1 for f in factors if f in bearish_factors)
        
        if bullish_count > bearish_count:
            direction = "BUY"
            setup_type = self._determine_bullish_setup(factors)
        elif bearish_count > bullish_count:
            direction = "SELL"
            setup_type = self._determine_bearish_setup(factors)
        else:
            direction = "HOLD"
            setup_type = "NEUTRAL"
        
        return direction, setup_type
    
    def _determine_bullish_setup(self, factors: list) -> str:
        """
        Determine bullish setup type.
        
        Args:
            factors: List of confluence factors
            
        Returns:
            Setup type string
        """
        if "FVG" in factors and "ORDER_BLOCK" in factors:
            return "FVG+OB"
        elif "LIQUIDITY_SWEEP_BUY" in factors:
            return "LIQUIDITY_SWEEP"
        elif "BULLISH_CONFIRMATION" in factors:
            return "BREAKOUT_CONFIRMATION"
        else:
            return "BULLISH_STRENGTH"
    
    def _determine_bearish_setup(self, factors: list) -> str:
        """
        Determine bearish setup type.
        
        Args:
            factors: List of confluence factors
            
        Returns:
            Setup type string
        """
        if "FVG" in factors and "ORDER_BLOCK" in factors:
            return "FVG+OB"
        elif "LIQUIDITY_SWEEP_SELL" in factors:
            return "LIQUIDITY_SWEEP"
        elif "BEARISH_CONFIRMATION" in factors:
            return "BREAKOUT_CONFIRMATION"
        else:
            return "BEARISH_STRENGTH"
    
    def _calculate_entry_price(self, analysis: ConfluenceAnalysis, 
                           current_price: Decimal, direction: str) -> Decimal:
        """
        Calculate optimal entry price.
        
        Args:
            analysis: Confluence analysis results
            current_price: Current market price
            direction: Signal direction
            
        Returns:
            Entry price
        """
        # For now, use current price as entry
        # In a real system, this would consider:
        # - Distance from key levels
        # - Market session adjustments
        # - Slippage considerations
        
        return current_price
    
    def _calculate_price_levels(self, entry_price: Decimal, direction: str, 
                           analysis: ConfluenceAnalysis) -> tuple[Decimal, Decimal, Decimal]:
        """
        Calculate stop loss and take profit levels.
        
        Args:
            entry_price: Entry price
            direction: Signal direction
            analysis: Confluence analysis
            
        Returns:
            Tuple of (stop_loss, tp1, tp2)
        """
        trading_config = self.settings.trading
        sl_buffer_pips = trading_config.sl_buffer_pips / 10000  # Convert to price
        
        if direction == "BUY":
            # Buy signal: SL below entry
            stop_loss = entry_price - sl_buffer_pips
            tp1 = entry_price + (entry_price - stop_loss) * trading_config.tp1_percentage
            tp2 = entry_price + (entry_price - stop_loss) * trading_config.tp2_percentage
        else:  # SELL signal: SL above entry
            stop_loss = entry_price + sl_buffer_pips
            tp1 = entry_price - (stop_loss - entry_price) * trading_config.tp1_percentage
            tp2 = entry_price - (stop_loss - entry_price) * trading_config.tp2_percentage
        
        return stop_loss, tp1, tp2
    
    def _calculate_position_risk(self, entry_price: Decimal, stop_loss: Decimal, 
                           direction: str) -> tuple[Decimal, float]:
        """
        Calculate position size and risk percentage.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss level
            direction: Signal direction
            
        Returns:
            Tuple of (position_size, risk_percentage)
        """
        trading_config = self.settings.trading
        
        # Calculate risk in pips
        if direction == "BUY":
            risk_pips = entry_price - stop_loss
        else:
            risk_pips = stop_loss - entry_price
        
        # Calculate position size
        position_size = trading_config.calculate_position_size(
            trading_config.get_risk_amount(),
            risk_pips
        )
        
        # Risk percentage is already configured
        risk_percentage = trading_config.risk_per_trade
        
        return position_size, risk_percentage
    
    def _calculate_risk_reward(self, entry_price: Decimal, stop_loss: Decimal, 
                           tp2: Decimal, direction: str) -> float:
        """
        Calculate risk:reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss level
            tp2: Take profit 2 level
            direction: Signal direction
            
        Returns:
            Risk:reward ratio
        """
        if direction == "BUY":
            risk = entry_price - stop_loss
            reward = tp2 - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - tp2
        
        if risk > 0:
            return float(reward / risk)
        else:
            return 0.0
    
    def _create_context_description(self, timeframe_analysis) -> str:
        """
        Create context description from timeframe analysis.
        
        Args:
            timeframe_analysis: Timeframe analysis results
            
        Returns:
            Context description
        """
        if not timeframe_analysis.factors:
            return "Insufficient data"
        
        # Get top factors
        top_factors = sorted(
            timeframe_analysis.factors,
            key=lambda f: f.score,
            reverse=True
        )[:3]
        
        descriptions = []
        for factor in top_factors:
            descriptions.append(f"{factor.description}: {factor.score:.1f}")
        
        return " | ".join(descriptions)
    
    def _get_current_session(self) -> SessionType:
        """
        Get current trading session.
        
        Returns:
            Current session type
        """
        current_hour = datetime.utcnow().hour
        return SessionType(
            self.settings.trading.get_current_session(current_hour) or "LONDON"
        )
    
    def validate_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Validate generated signal.
        
        Args:
            signal: Trading signal to validate
            
        Returns:
            Validation results
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check minimum risk:reward ratio
        if signal.risk_reward_ratio < self.settings.trading.min_risk_reward:
            validation['is_valid'] = False
            validation['errors'].append(
                f"Risk:reward ratio {signal.risk_reward_ratio} below minimum {self.settings.trading.min_risk_reward}"
            )
        
        # Check maximum position size
        if signal.position_size > self.settings.trading.max_lot_size:
            validation['warnings'].append(
                f"Position size {signal.position_size} exceeds maximum {self.settings.trading.max_lot_size}"
            )
        
        # Check signal expiry
        if signal.is_expired:
            validation['warnings'].append("Signal has expired")
        
        return validation