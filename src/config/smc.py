"""
Smart Money Concepts (SMC) configuration for XAUUSD Gold Trading System.

Manages SMC analysis parameters, detection thresholds,
and confluence scoring settings.
"""

from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class FVGConfig(BaseSettings):
    """
    Fair Value Gap detection configuration.
    
    Defines parameters for identifying and
    validating Fair Value Gaps.
    """
    
    # Detection parameters
    min_size_pips: int = Field(default=5, ge=1, le=50, env="FVG_MIN_SIZE_PIPS")
    max_size_pips: int = Field(default=100, ge=10, le=500, env="FVG_MAX_SIZE_PIPS")
    min_strength: float = Field(default=0.3, ge=0.1, le=1.0, env="FVG_MIN_STRENGTH")
    
    # Validation parameters
    lookback_candles: int = Field(default=3, ge=1, le=10, env="FVG_LOOKBACK_CANDLES")
    fill_timeframe_minutes: int = Field(default=60, ge=15, le=240, env="FVG_FILL_TIMEFRAME")
    fill_threshold_percentage: float = Field(default=0.7, ge=0.5, le=1.0, env="FVG_FILL_THRESHOLD")
    
    # Filtering
    ignore_small_fvgs: bool = Field(default=True, env="FVG_IGNORE_SMALL")
    require_volume_spike: bool = Field(default=False, env="FVG_REQUIRE_VOLUME")
    volume_multiplier: float = Field(default=1.5, ge=1.0, le=5.0, env="FVG_VOLUME_MULTIPLIER")
    
    def to_dict(self) -> dict:
        """Convert FVG config to dictionary."""
        return {
            'min_size_pips': self.min_size_pips,
            'max_size_pips': self.max_size_pips,
            'min_strength': self.min_strength,
            'lookback_candles': self.lookback_candles,
            'fill_timeframe_minutes': self.fill_timeframe_minutes,
            'fill_threshold_percentage': self.fill_threshold_percentage,
            'ignore_small_fvgs': self.ignore_small_fvgs,
            'require_volume_spike': self.require_volume_spike,
            'volume_multiplier': self.volume_multiplier
        }


class OrderBlockConfig(BaseSettings):
    """
    Order Block detection configuration.
    
    Defines parameters for identifying institutional
    order blocks and accumulation zones.
    """
    
    # Detection parameters
    lookback_candles: int = Field(default=20, ge=5, le=100, env="OB_LOOKBACK_CANDLES")
    min_candle_range: float = Field(default=0.5, ge=0.1, le=2.0, env="OB_MIN_RANGE")
    wick_ratio_threshold: float = Field(default=0.6, ge=0.3, le=0.9, env="OB_WICK_RATIO")
    
    # Volume requirements
    min_volume_multiplier: float = Field(default=1.5, ge=1.0, le=5.0, env="OB_VOLUME_MULTIPLIER")
    avg_volume_periods: int = Field(default=20, ge=5, le=100, env="OB_AVG_VOLUME_PERIODS")
    
    # Validation
    require_rejection: bool = Field(default=True, env="OB_REQUIRE_REJECTION")
    rejection_ratio: float = Field(default=0.4, ge=0.2, le=0.8, env="OB_REJECTION_RATIO")
    min_touches: int = Field(default=2, ge=1, le=5, env="OB_MIN_TOUCHES")
    
    # Filtering
    near_round_numbers: bool = Field(default=True, env="OB_NEAR_ROUND_NUMBERS")
    round_number_pips: int = Field(default=50, ge=10, le=200, env="OB_ROUND_NUMBER_PIPS")
    
    def to_dict(self) -> dict:
        """Convert Order Block config to dictionary."""
        return {
            'lookback_candles': self.lookback_candles,
            'min_candle_range': self.min_candle_range,
            'wick_ratio_threshold': self.wick_ratio_threshold,
            'min_volume_multiplier': self.min_volume_multiplier,
            'avg_volume_periods': self.avg_volume_periods,
            'require_rejection': self.require_rejection,
            'rejection_ratio': self.rejection_ratio,
            'min_touches': self.min_touches,
            'near_round_numbers': self.near_round_numbers,
            'round_number_pips': self.round_number_pips
        }


class LiquidityConfig(BaseSettings):
    """
    Liquidity analysis configuration.
    
    Defines parameters for detecting liquidity
    sweeps and stop hunts.
    """
    
    # Swing point detection
    swing_point_period: int = Field(default=10, ge=3, le=50, env="LIQ_SWING_PERIOD")
    swing_point_threshold: float = Field(default=0.5, ge=0.2, le=2.0, env="LIQ_SWING_THRESHOLD")
    
    # Sweep detection
    sweep_extension_pips: int = Field(default=5, ge=1, le=20, env="LIQ_SWEEP_EXTENSION")
    reversal_threshold: float = Field(default=0.7, ge=0.3, le=1.0, env="LIQ_REVERSAL_THRESHOLD")
    reversal_timeframe_minutes: int = Field(default=30, ge=5, le=120, env="LIQ_REVERSAL_TIMEFRAME")
    
    # Volume analysis
    volume_spike_multiplier: float = Field(default=2.0, ge=1.0, le=5.0, env="LIQ_VOLUME_SPIKE")
    avg_volume_period: int = Field(default=20, ge=5, le=100, env="LIQ_AVG_VOLUME_PERIOD")
    
    # Pool identification
    pool_range_pips: int = Field(default=10, ge=2, le=50, env="LIQ_POOL_RANGE")
    min_pool_touches: int = Field(default=3, ge=1, le=10, env="LIQ_MIN_POOL_TOUCHES")
    
    def to_dict(self) -> dict:
        """Convert Liquidity config to dictionary."""
        return {
            'swing_point_period': self.swing_point_period,
            'swing_point_threshold': self.swing_point_threshold,
            'sweep_extension_pips': self.sweep_extension_pips,
            'reversal_threshold': self.reversal_threshold,
            'reversal_timeframe_minutes': self.reversal_timeframe_minutes,
            'volume_spike_multiplier': self.volume_spike_multiplier,
            'avg_volume_period': self.avg_volume_period,
            'pool_range_pips': self.pool_range_pips,
            'min_pool_touches': self.min_pool_touches
        }


class StructureConfig(BaseSettings):
    """
    Market structure analysis configuration.
    
    Defines parameters for identifying trend,
    structure breaks, and market state.
    """
    
    # Trend analysis
    trend_period: int = Field(default=20, ge=5, le=100, env="STRUCT_TREND_PERIOD")
    trend_strength_threshold: float = Field(default=0.6, ge=0.3, le=1.0, env="STRUCT_TREND_STRENGTH")
    
    # Structure identification
    min_swing_points: int = Field(default=3, ge=2, le=10, env="STRUCT_MIN_SWING_POINTS")
    structure_break_threshold: float = Field(default=0.8, ge=0.5, le=1.0, env="STRUCT_BREAK_THRESHOLD")
    
    # BOS and CHoCH
    bos_confirmation_candles: int = Field(default=2, ge=1, le=5, env="STRUCT_BOS_CONFIRMATION")
    choch_confirmation_candles: int = Field(default=1, ge=1, le=3, env="STRUCT_CHOCH_CONFIRMATION")
    
    # Range detection
    range_threshold_percentage: float = Field(default=0.3, ge=0.1, le=0.8, env="STRUCT_RANGE_THRESHOLD")
    range_min_periods: int = Field(default=10, ge=5, le=50, env="STRUCT_RANGE_MIN_PERIODS")
    
    def to_dict(self) -> dict:
        """Convert Structure config to dictionary."""
        return {
            'trend_period': self.trend_period,
            'trend_strength_threshold': self.trend_strength_threshold,
            'min_swing_points': self.min_swing_points,
            'structure_break_threshold': self.structure_break_threshold,
            'bos_confirmation_candles': self.bos_confirmation_candles,
            'choch_confirmation_candles': self.choch_confirmation_candles,
            'range_threshold_percentage': self.range_threshold_percentage,
            'range_min_periods': self.range_min_periods
        }


class SMCConfig(BaseSettings):
    """
    Main SMC configuration.
    
    Combines all SMC component configurations
    and manages confluence scoring.
    """
    
    # Component configurations
    fvg: FVGConfig = Field(default_factory=FVGConfig)
    order_block: OrderBlockConfig = Field(default_factory=OrderBlockConfig)
    liquidity: LiquidityConfig = Field(default_factory=LiquidityConfig)
    structure: StructureConfig = Field(default_factory=StructureConfig)
    
    # Confluence scoring
    confluence_threshold: float = Field(default=80.0, ge=50.0, le=100.0, env="SMC_CONFLUENCE_THRESHOLD")
    
    # Scoring weights
    fvg_weight: float = Field(default=25.0, ge=0.0, le=100.0, env="SMC_FVG_WEIGHT")
    ob_weight: float = Field(default=30.0, ge=0.0, le=100.0, env="SMC_OB_WEIGHT")
    liquidity_weight: float = Field(default=25.0, ge=0.0, le=100.0, env="SMC_LIQUIDITY_WEIGHT")
    structure_weight: float = Field(default=20.0, ge=0.0, le=100.0, env="SMC_STRUCTURE_WEIGHT")
    
    # Timeframe analysis
    h4_weight: float = Field(default=40.0, ge=0.0, le=100.0, env="SMC_H4_WEIGHT")
    h1_weight: float = Field(default=35.0, ge=0.0, le=100.0, env="SMC_H1_WEIGHT")
    m15_weight: float = Field(default=25.0, ge=0.0, le=100.0, env="SMC_M15_WEIGHT")
    
    # Analysis settings
    min_candles_required: int = Field(default=200, ge=50, le=1000, env="SMC_MIN_CANDLES")
    analysis_buffer_candles: int = Field(default=20, ge=5, le=100, env="SMC_ANALYSIS_BUFFER")
    
    # Validation
    require_multi_timeframe: bool = Field(default=True, env="SMC_REQUIRE_MTF")
    min_timeframes_aligned: int = Field(default=2, ge=1, le=3, env="SMC_MIN_TF_ALIGNED")
    
    class Config:
        env_prefix = "SMC_"
    
    def validate(self) -> bool:
        """
        Validate SMC configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Validate confluence threshold
        if not (50.0 <= self.confluence_threshold <= 100.0):
            errors.append("Confluence threshold must be between 50 and 100")
        
        # Validate weights sum to 100
        total_weight = (
            self.fvg_weight + self.ob_weight + 
            self.liquidity_weight + self.structure_weight
        )
        if abs(total_weight - 100.0) > 0.1:
            errors.append(f"SMC component weights must sum to 100, got {total_weight}")
        
        tf_total_weight = self.h4_weight + self.h1_weight + self.m15_weight
        if abs(tf_total_weight - 100.0) > 0.1:
            errors.append(f"Timeframe weights must sum to 100, got {tf_total_weight}")
        
        # Validate minimum requirements
        if self.min_candles_required < 50:
            errors.append("Minimum candles required should be at least 50")
        
        if self.min_timeframes_aligned < 1 or self.min_timeframes_aligned > 3:
            errors.append("Minimum timeframes aligned must be between 1 and 3")
        
        # Validate component configs
        try:
            self.fvg.validate()
        except ValueError as e:
            errors.append(f"FVG config: {e}")
        
        try:
            self.order_block.validate()
        except ValueError as e:
            errors.append(f"Order Block config: {e}")
        
        try:
            self.liquidity.validate()
        except ValueError as e:
            errors.append(f"Liquidity config: {e}")
        
        try:
            self.structure.validate()
        except ValueError as e:
            errors.append(f"Structure config: {e}")
        
        if errors:
            raise ValueError("SMC configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    def calculate_confluence_score(self, analysis_results: dict) -> float:
        """
        Calculate overall confluence score from analysis results.
        
        Args:
            analysis_results: Dictionary with component scores
            
        Returns:
            Overall confluence score (0-100)
        """
        # Component scores
        fvg_score = analysis_results.get('fvg_score', 0) * (self.fvg_weight / 100.0)
        ob_score = analysis_results.get('ob_score', 0) * (self.ob_weight / 100.0)
        liquidity_score = analysis_results.get('liquidity_score', 0) * (self.liquidity_weight / 100.0)
        structure_score = analysis_results.get('structure_score', 0) * (self.structure_weight / 100.0)
        
        # Timeframe scores
        h4_score = analysis_results.get('h4_score', 0) * (self.h4_weight / 100.0)
        h1_score = analysis_results.get('h1_score', 0) * (self.h1_weight / 100.0)
        m15_score = analysis_results.get('m15_score', 0) * (self.m15_weight / 100.0)
        
        # Combine scores
        component_total = fvg_score + ob_score + liquidity_score + structure_score
        timeframe_total = h4_score + h1_score + m15_score
        
        # Weighted average
        overall_score = (component_total * 0.6) + (timeframe_total * 0.4)
        
        return min(100.0, max(0.0, overall_score))
    
    def to_dict(self) -> dict:
        """Convert SMC config to dictionary."""
        return {
            'confluence_threshold': self.confluence_threshold,
            'fvg_weight': self.fvg_weight,
            'ob_weight': self.ob_weight,
            'liquidity_weight': self.liquidity_weight,
            'structure_weight': self.structure_weight,
            'h4_weight': self.h4_weight,
            'h1_weight': self.h1_weight,
            'm15_weight': self.m15_weight,
            'min_candles_required': self.min_candles_required,
            'analysis_buffer_candles': self.analysis_buffer_candles,
            'require_multi_timeframe': self.require_multi_timeframe,
            'min_timeframes_aligned': self.min_timeframes_aligned,
            'fvg': self.fvg.to_dict(),
            'order_block': self.order_block.to_dict(),
            'liquidity': self.liquidity.to_dict(),
            'structure': self.structure.to_dict()
        }