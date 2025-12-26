"""
Smart Money Concepts (SMC) analysis engine.

This module orchestrates various SMC components to provide a comprehensive
market analysis based on institutional trading concepts.
"""

from typing import List, Dict, Any
from ..models.candle import Candle
from .fvg_detector import FairValueGapDetector
from .order_block_detector import OrderBlockDetector
from .liquidity_analyzer import LiquidityAnalyzer
from .structure_analyzer import MarketStructure # Corrected import


class SmartMoneyEngine:
    """
    Central engine for Smart Money Concepts analysis.

    Combines various detectors and analyzers to produce a holistic
    view of market structure, liquidity, and imbalances.
    """

    def __init__(self):
        """Initializes all SMC analysis components."""
        self.fvg_detector = FairValueGapDetector()
        self.order_block_detector = OrderBlockDetector()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.market_structure = MarketStructure() # Using the corrected class name

    async def analyze_candles(self, candles: List[Candle]) -> Dict[str, Any]:
        """
        Performs a comprehensive SMC analysis on a list of candles.

        Args:
            candles: A list of Candle objects for analysis.

        Returns:
            A dictionary containing the combined analysis results.
        """
        if not candles:
            return {"error": "No candles provided for analysis."}

        # Update market structure
        for candle in candles:
            self.market_structure.update_with_candle(candle)

        # Detect FVGs
        fvg_results = self.fvg_detector.detect_fvg(candles)

        # Detect Order Blocks
        ob_results = self.order_block_detector.detect_order_blocks(candles)

        # Analyze Liquidity
        liquidity_results = self.liquidity_analyzer.analyze_liquidity(candles)

        # Get structure summary
        structure_summary = self.market_structure.get_structure_summary()

        # Combine results
        analysis_results = {
            "market_structure": structure_summary,
            "fair_value_gaps": [fvg.to_dict() for fvg in fvg_results],
            "order_blocks": [ob.to_dict() for ob in ob_results],
            "liquidity_zones": [lz.to_dict() for lz in liquidity_results],
            # Add more combined analysis or confluence logic here
        }

        return analysis_results
