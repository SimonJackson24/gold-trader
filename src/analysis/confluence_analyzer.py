"""
Confluence analyzer for Smart Money Concepts.

Combines multiple SMC indicators to calculate
overall confluence scores and signal confidence.
"""

from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime

from ..models.candle import Candle
from ..models.market_data import PriceLevel
from ..config import get_settings

from .fvg_detector import FairValueGap, FairValueGapDetector
from .order_block_detector import OrderBlock, OrderBlockDetector
from .liquidity_analyzer import LiquidityPool, LiquiditySweep, LiquidityAnalyzer
from .structure_analyzer import MarketStructure, StructureBreak


class ConfluenceFactor:
    """Confluence factor data structure."""
    
    def __init__(self, factor_type: str, score: float, description: str,
                 weight: float = 1.0):
        """
        Initialize confluence factor.
        
        Args:
            factor_type: Type of factor
            score: Factor score (0.0 to 1.0)
            description: Factor description
            weight: Factor weight in overall calculation
        """
        self.type = factor_type
        self.score = score
        self.description = description
        self.weight = weight
        self.timestamp = datetime.utcnow()
        
        # Validate
        self._validate_factor()
    
    def _validate_factor(self):
        """Validate confluence factor parameters."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Factor score must be between 0 and 1, got {self.score}")
        
        if self.weight < 0:
            raise ValueError(f"Factor weight must be positive, got {self.weight}")
    
    def to_dict(self) -> dict:
        """Convert confluence factor to dictionary."""
        return {
            'type': self.type,
            'score': self.score,
            'description': self.description,
            'weight': self.weight,
            'timestamp': self.timestamp.isoformat()
        }


class TimeframeAnalysis:
    """Timeframe analysis data structure."""
    
    def __init__(self, timeframe: str):
        """
        Initialize timeframe analysis.
        
        Args:
            timeframe: Timeframe identifier (H4, H1, M15)
        """
        self.timeframe = timeframe
        self.fvg_score = 0.0
        self.ob_score = 0.0
        self.liquidity_score = 0.0
        self.structure_score = 0.0
        self.overall_score = 0.0
        self.factors = []
        self.timestamp = datetime.utcnow()
    
    def add_factor(self, factor: ConfluenceFactor):
        """
        Add a confluence factor.
        
        Args:
            factor: Confluence factor to add
        """
        self.factors.append(factor)
        self._recalculate_scores()
    
    def _recalculate_scores(self):
        """Recalculate all scores based on factors."""
        if not self.factors:
            self.fvg_score = 0.0
            self.ob_score = 0.0
            self.liquidity_score = 0.0
            self.structure_score = 0.0
            self.overall_score = 0.0
            return
        
        # Calculate weighted scores
        total_weight = sum(f.weight for f in self.factors)
        
        for factor in self.factors:
            if factor.type == "FVG":
                self.fvg_score += factor.score * factor.weight
            elif factor.type == "ORDER_BLOCK":
                self.ob_score += factor.score * factor.weight
            elif factor.type == "LIQUIDITY":
                self.liquidity_score += factor.score * factor.weight
            elif factor.type == "STRUCTURE":
                self.structure_score += factor.score * factor.weight
        
        # Normalize scores
        if total_weight > 0:
            self.fvg_score = (self.fvg_score / total_weight) * 100
            self.ob_score = (self.ob_score / total_weight) * 100
            self.liquidity_score = (self.liquidity_score / total_weight) * 100
            self.structure_score = (self.structure_score / total_weight) * 100
        
        # Calculate overall score
        self.overall_score = (
            (self.fvg_score * 0.25) +
            (self.ob_score * 0.30) +
            (self.liquidity_score * 0.25) +
            (self.structure_score * 0.20)
        )
    
    def to_dict(self) -> dict:
        """Convert timeframe analysis to dictionary."""
        return {
            'timeframe': self.timeframe,
            'fvg_score': self.fvg_score,
            'ob_score': self.ob_score,
            'liquidity_score': self.liquidity_score,
            'structure_score': self.structure_score,
            'overall_score': self.overall_score,
            'factors': [f.to_dict() for f in self.factors],
            'timestamp': self.timestamp.isoformat()
        }


class ConfluenceAnalysis:
    """Complete confluence analysis result."""
    
    def __init__(self, instrument: str = "XAUUSD"):
        """
        Initialize confluence analysis.
        
        Args:
            instrument: Trading instrument
        """
        self.instrument = instrument
        self.h4_analysis = TimeframeAnalysis("H4")
        self.h1_analysis = TimeframeAnalysis("H1")
        self.m15_analysis = TimeframeAnalysis("M15")
        self.overall_score = 0.0
        self.confidence = 0.0
        self.setup_type = "UNKNOWN"
        self.market_structure = "UNKNOWN"
        self.confluence_factors = []
        self.timestamp = datetime.utcnow()
        
        # Analysis components
        self.fvgs: List[FairValueGap] = []
        self.order_blocks: List[OrderBlock] = []
        self.liquidity_pools: List[LiquidityPool] = []
        self.liquidity_sweeps: List[LiquiditySweep] = []
        self.market_structure_obj: Optional[MarketStructure] = None
    
    def analyze(self, h4_candles: List[Candle], h1_candles: List[Candle],
               m15_candles: List[Candle], current_price: Decimal,
               market_structure: Optional[MarketStructure] = None) -> Dict[str, Any]:
        """
        Perform complete confluence analysis.
        
        Args:
            h4_candles: H4 timeframe candles
            h1_candles: H1 timeframe candles
            m15_candles: M15 timeframe candles
            current_price: Current market price
            market_structure: Optional market structure object
            
        Returns:
            Complete analysis results
        """
        settings = get_settings()
        config = settings.smc
        
        # Initialize detectors
        fvg_detector = FairValueGapDetector()
        ob_detector = OrderBlockDetector()
        liquidity_analyzer = LiquidityAnalyzer()
        
        # Use provided market structure or create new one
        self.market_structure_obj = market_structure
        
        if not self.market_structure_obj:
            self.market_structure_obj = MarketStructure(self.instrument)
            for candle in h1_candles:  # Use H1 for structure
                self.market_structure_obj.update_with_candle(candle)
        
        # Detect FVGs
        self.fvgs = fvg_detector.detect_fvgs(h1_candles)
        
        # Detect Order Blocks
        swing_points = self.market_structure_obj.swing_highs + self.market_structure_obj.swing_lows
        self.order_blocks = ob_detector.detect_order_blocks(h1_candles, swing_points)
        
        # Analyze liquidity
        self.liquidity_pools = liquidity_analyzer.identify_liquidity_pools(
            swing_points, current_price
        )
        self.liquidity_sweeps = liquidity_analyzer.detect_liquidity_sweeps(
            self.liquidity_pools, h1_candles, current_price
        )
        
        # Analyze each timeframe
        self._analyze_h4(h4_candles, current_price)
        self._analyze_h1(h1_candles, current_price)
        self._analyze_m15(m15_candles, current_price)
        
        # Calculate overall confluence
        self._calculate_overall_confluence()
        
        # Determine setup type and market structure
        self._determine_setup_type()
        self._determine_market_structure()
        
        return self.to_dict()
    
    def _analyze_h4(self, candles: List[Candle], current_price: Decimal):
        """Analyze H4 timeframe for confluence."""
        if not candles:
            return
        
        # Get active FVGs
        active_fvgs = fvg_detector.get_active_fvgs(
            self.fvgs, current_price, max_age_minutes=1440  # 24 hours
        )
        
        # Get active order blocks
        active_obs = ob_detector.get_active_order_blocks(
            self.order_blocks, current_price, max_age_minutes=1440
        )
        
        # Add FVG factors
        for fvg in active_fvgs[:3]:  # Top 3 FVGs
            factor = ConfluenceFactor(
                factor_type="FVG",
                score=fvg.strength,
                description=f"FVG at {fvg.mid_price:.5f}",
                weight=config.fvg_weight / 100.0
            )
            self.h4_analysis.add_factor(factor)
        
        # Add Order Block factors
        for ob in active_obs[:3]:  # Top 3 OBs
            factor = ConfluenceFactor(
                factor_type="ORDER_BLOCK",
                score=ob.strength,
                description=f"OB at {ob.price:.5f}",
                weight=config.ob_weight / 100.0
            )
            self.h4_analysis.add_factor(factor)
    
    def _analyze_h1(self, candles: List[Candle], current_price: Decimal):
        """Analyze H1 timeframe for confluence."""
        if not candles:
            return
        
        # Get active FVGs
        active_fvgs = fvg_detector.get_active_fvgs(
            self.fvgs, current_price, max_age_minutes=720  # 12 hours
        )
        
        # Get active order blocks
        active_obs = ob_detector.get_active_order_blocks(
            self.order_blocks, current_price, max_age_minutes=720
        )
        
        # Add FVG factors
        for fvg in active_fvgs[:2]:  # Top 2 FVGs
            factor = ConfluenceFactor(
                factor_type="FVG",
                score=fvg.strength,
                description=f"FVG at {fvg.mid_price:.5f}",
                weight=config.fvg_weight / 100.0
            )
            self.h1_analysis.add_factor(factor)
        
        # Add Order Block factors
        for ob in active_obs[:2]:  # Top 2 OBs
            factor = ConfluenceFactor(
                factor_type="ORDER_BLOCK",
                score=ob.strength,
                description=f"OB at {ob.price:.5f}",
                weight=config.ob_weight / 100.0
            )
            self.h1_analysis.add_factor(factor)
        
        # Add liquidity factors
        for sweep in self.liquidity_sweeps[-2:]:  # Last 2 sweeps
            factor = ConfluenceFactor(
                factor_type="LIQUIDITY_SWEEP",
                score=sweep.strength,
                description=f"Liquidity sweep at {sweep.pool_price:.5f}",
                weight=config.liquidity_weight / 100.0
            )
            self.h1_analysis.add_factor(factor)
    
    def _analyze_m15(self, candles: List[Candle], current_price: Decimal):
        """Analyze M15 timeframe for confluence."""
        if not candles:
            return
        
        # Get active FVGs
        active_fvgs = fvg_detector.get_active_fvgs(
            self.fvgs, current_price, max_age_minutes=240  # 4 hours
        )
        
        # Get active order blocks
        active_obs = ob_detector.get_active_order_blocks(
            self.order_blocks, current_price, max_age_minutes=240
        )
        
        # Add FVG factors
        for fvg in active_fvgs[:1]:  # Top 1 FVG
            factor = ConfluenceFactor(
                factor_type="FVG",
                score=fvg.strength,
                description=f"FVG at {fvg.mid_price:.5f}",
                weight=config.fvg_weight / 100.0
            )
            self.m15_analysis.add_factor(factor)
        
        # Add Order Block factors
        for ob in active_obs[:1]:  # Top 1 OB
            factor = ConfluenceFactor(
                factor_type="ORDER_BLOCK",
                score=ob.strength,
                description=f"OB at {ob.price:.5f}",
                weight=config.ob_weight / 100.0
            )
            self.m15_analysis.add_factor(factor)
        
        # Add entry precision factors
        if len(candles) >= 2:
            last_candle = candles[-1]
            prev_candle = candles[-2]
            
            # Price rejection or confirmation
            if last_candle.is_doji(threshold=0.1):
                factor = ConfluenceFactor(
                    factor_type="PRICE_REJECTION",
                    score=0.6,
                    description="Doji at key level",
                    weight=0.5
                )
                self.m15_analysis.add_factor(factor)
            elif (last_candle.is_bullish and 
                  prev_candle.is_bearish and
                  last_candle.close > prev_candle.close):
                factor = ConfluenceFactor(
                    factor_type="BULLISH_CONFIRMATION",
                    score=0.7,
                    description="Bullish confirmation",
                    weight=0.5
                )
                self.m15_analysis.add_factor(factor)
            elif (last_candle.is_bearish and 
                  prev_candle.is_bullish and
                  last_candle.close < prev_candle.close):
                factor = ConfluenceFactor(
                    factor_type="BEARISH_CONFIRMATION",
                    score=0.7,
                    description="Bearish confirmation",
                    weight=0.5
                )
                self.m15_analysis.add_factor(factor)
    
    def _calculate_overall_confluence(self):
        """Calculate overall confluence score from timeframes."""
        settings = get_settings()
        config = settings.smc
        
        # Weighted timeframe scores
        h4_weight = config.h4_weight / 100.0
        h1_weight = config.h1_weight / 100.0
        m15_weight = config.m15_weight / 100.0
        
        # Calculate weighted overall score
        self.overall_score = (
            (self.h4_analysis.overall_score * h4_weight) +
            (self.h1_analysis.overall_score * h1_weight) +
            (self.m15_analysis.overall_score * m15_weight)
        )
        
        # Calculate confidence
        self.confidence = min(1.0, self.overall_score / 100.0)
    
    def _determine_setup_type(self):
        """Determine the primary setup type."""
        if not self.h4_analysis.factors:
            self.setup_type = "INSUFFICIENT_DATA"
            return
        
        # Analyze factor combinations
        fvg_present = any(f.type == "FVG" for f in self.h4_analysis.factors)
        ob_present = any(f.type == "ORDER_BLOCK" for f in self.h4_analysis.factors)
        liquidity_present = any(f.type.startswith("LIQUIDITY") for f in self.h4_analysis.factors)
        
        # Determine setup type based on factor combination
        if fvg_present and ob_present:
            self.setup_type = "FVG+OB"
        elif fvg_present and liquidity_present:
            self.setup_type = "FVG+LIQUIDITY"
        elif ob_present and liquidity_present:
            self.setup_type = "OB+LIQUIDITY"
        elif fvg_present:
            self.setup_type = "FVG_ONLY"
        elif ob_present:
            self.setup_type = "OB_ONLY"
        elif liquidity_present:
            self.setup_type = "LIQUIDITY_ONLY"
        else:
            self.setup_type = "STRUCTURAL"
    
    def _determine_market_structure(self):
        """Determine market structure state."""
        if not self.market_structure_obj:
            self.market_structure = "UNKNOWN"
            return
        
        structure = self.market_structure_obj.current_state
        
        # Map to descriptive string
        if structure == "UPTREND":
            self.market_structure = "BOS"
        elif structure == "DOWNTREND":
            self.market_structure = "BOS"
        elif structure == "RANGING":
            self.market_structure = "RANGE"
        else:
            self.market_structure = "UNCLEAR"
    
    def meets_threshold(self, threshold: float = None) -> bool:
        """
        Check if confluence meets minimum threshold.
        
        Args:
            threshold: Minimum confluence threshold
            
        Returns:
            True if meets threshold
        """
        if threshold is None:
            settings = get_settings()
            threshold = settings.smc.confluence_threshold
        
        return self.overall_score >= threshold
    
    def get_confluence_factors(self) -> List[str]:
        """Get list of confluence factor descriptions."""
        return [f.description for f in self.h4_analysis.factors]
    
    def to_dict(self) -> dict:
        """Convert confluence analysis to dictionary."""
        return {
            'instrument': self.instrument,
            'h4_analysis': self.h4_analysis.to_dict(),
            'h1_analysis': self.h1_analysis.to_dict(),
            'm15_analysis': self.m15_analysis.to_dict(),
            'overall_score': self.overall_score,
            'confidence': self.confidence,
            'setup_type': self.setup_type,
            'market_structure': self.market_structure,
            'confluence_factors': self.get_confluence_factors(),
            'fvgs': [fvg.to_dict() for fvg in self.fvgs[:5]],
            'order_blocks': [ob.to_dict() for ob in self.order_blocks[:5]],
            'liquidity_pools': [lp.to_dict() for lp in self.liquidity_pools[:5]],
            'liquidity_sweeps': [ls.to_dict() for ls in self.liquidity_sweeps[:5]],
            'timestamp': self.timestamp.isoformat()
        }


class ConfluenceAnalyzer:
    """
    Confluence analyzer implementation.
    
    Combines all SMC components to calculate
    overall confluence and signal confidence.
    """
    
    def __init__(self):
        """Initialize confluence analyzer."""
        self.settings = get_settings()
        self.config = self.settings.smc
    
    def analyze_confluence(self, h4_candles: List[Candle], h1_candles: List[Candle],
                        m15_candles: List[Candle], current_price: Decimal,
                        market_structure: Optional[MarketStructure] = None) -> ConfluenceAnalysis:
        """
        Perform complete confluence analysis.
        
        Args:
            h4_candles: H4 timeframe candles
            h1_candles: H1 timeframe candles
            m15_candles: M15 timeframe candles
            current_price: Current market price
            market_structure: Optional market structure object
            
        Returns:
            Complete confluence analysis
        """
        analysis = ConfluenceAnalysis()
        return analysis.analyze(
            h4_candles, h1_candles, m15_candles, current_price, market_structure
        )
    
    def calculate_signal_quality(self, analysis: ConfluenceAnalysis) -> Dict[str, float]:
        """
        Calculate signal quality metrics.
        
        Args:
            analysis: Confluence analysis results
            
        Returns:
            Signal quality metrics
        """
        # Risk:Reward ratio calculation
        rr_score = 0.0
        if analysis.overall_score > 80:
            rr_score = 1.0  # High confidence signals typically have good R:R
        elif analysis.overall_score > 70:
            rr_score = 0.8
        else:
            rr_score = 0.6
        
        # Entry precision score
        entry_score = 1.0
        if analysis.m15_analysis.factors:
            # Check for precise entry factors
            precision_factors = [
                f for f in analysis.m15_analysis.factors
                if f.type in ["BULLISH_CONFIRMATION", "BEARISH_CONFIRMATION", "PRICE_REJECTION"]
            ]
            entry_score = min(1.0, len(precision_factors) / 2.0)
        
        # Multi-timeframe alignment score
        alignment_score = 1.0
        if self.config.require_multi_timeframe:
            # Check if multiple timeframes align
            aligned_timeframes = 0
            if analysis.h4_analysis.overall_score > 60:
                aligned_timeframes += 1
            if analysis.h1_analysis.overall_score > 60:
                aligned_timeframes += 1
            if analysis.m15_analysis.overall_score > 60:
                aligned_timeframes += 1
            
            alignment_score = aligned_timeframes / 3.0
            entry_score *= alignment_score
        
        return {
            'overall_quality': analysis.overall_score,
            'rr_potential': rr_score,
            'entry_precision': entry_score,
            'timeframe_alignment': alignment_score,
            'combined_quality': (analysis.overall_score + rr_score + entry_score) / 3.0
        }
    
    def validate_signal_setup(self, analysis: ConfluenceAnalysis) -> Dict[str, Any]:
        """
        Validate signal setup against requirements.
        
        Args:
            analysis: Confluence analysis results
            
        Returns:
            Validation results
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check minimum confluence
        if not analysis.meets_threshold(self.config.confluence_threshold):
            validation['is_valid'] = False
            validation['errors'].append(
                f"Confluence score {analysis.overall_score} below threshold {self.config.confluence_threshold}"
            )
        
        # Check multi-timeframe requirement
        if (self.config.require_multi_timeframe and 
            analysis.h4_analysis.overall_score < 50 and
            analysis.h1_analysis.overall_score < 50 and
            analysis.m15_analysis.overall_score < 50):
            validation['is_valid'] = False
            validation['errors'].append(
                "Insufficient multi-timeframe alignment"
            )
        
        # Check for conflicting signals
        if self._has_conflicting_factors(analysis):
            validation['warnings'].append(
                "Potential conflicting factors detected"
            )
        
        return validation
    
    def _has_conflicting_factors(self, analysis: ConfluenceAnalysis) -> bool:
        """
        Check for conflicting confluence factors.
        
        Args:
            analysis: Confluence analysis
            
        Returns:
            True if conflicts detected
        """
        # Check for bullish and bearish factors in same analysis
        has_bullish = any(
            "BULLISH" in f.description.upper() 
            for f in analysis.h4_analysis.factors
        )
        has_bearish = any(
            "BEARISH" in f.description.upper() 
            for f in analysis.h4_analysis.factors
        )
        
        return has_bullish and has_bearish