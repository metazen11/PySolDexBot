from typing import Dict, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TradeChecker:
    def __init__(self, config: Dict):
        self.config = config
        self.min_sell_count = config.get('min_sell_count', 5)
        self.min_unique_sellers = config.get('min_unique_sellers', 3)
        self.min_successful_sells = config.get('min_successful_sells', 3)

    async def check_trade_history(self, token_address: str) -> Dict:
        """Analyze trading history for suspicious patterns"""
        try:
            # Get recent trades
            trades = await self._get_recent_trades(token_address)
            
            risks = []
            
            # Check sell transactions
            sell_count = sum(1 for trade in trades if trade['type'] == 'sell')
            unique_sellers = len(set(trade['wallet'] for trade in trades if trade['type'] == 'sell'))
            successful_sells = len([t for t in trades if t['type'] == 'sell' and t['success']])
            
            if sell_count < self.min_sell_count:
                risks.append('Insufficient sell transactions')
            if unique_sellers < self.min_unique_sellers:
                risks.append('Too few unique sellers')
            if successful_sells < self.min_successful_sells:
                risks.append('Too few successful sells')
            
            # Check transaction patterns
            if self._detect_failed_sell_pattern(trades):
                risks.append('Suspicious failed sell pattern')
                
            # Check sell size distribution
            if self._detect_size_manipulation(trades):
                risks.append('Suspicious sell size pattern')
                
            return {
                'is_risk': len(risks) > 0,
                'risk_factors': risks,
                'data': {
                    'sell_count': sell_count,
                    'unique_sellers': unique_sellers,
                    'successful_sells': successful_sells
                }
            }
            
        except Exception as e:
            logger.error(f"Error in trade history check: {e}")
            return {'is_risk': True, 'risk_factors': ['Trade check failed']}

    def _detect_failed_sell_pattern(self, trades: List[Dict]) -> bool:
        """Detect patterns of failed sell transactions"""
        sell_trades = [t for t in trades if t['type'] == 'sell']
        if not sell_trades:
            return False
            
        # Calculate failed sell ratio
        failed_sells = sum(1 for t in sell_trades if not t['success'])
        fail_ratio = failed_sells / len(sell_trades)
        
        # Check for suspicious patterns
        return fail_ratio > 0.3  # More than 30% fails is suspicious

    def _detect_size_manipulation(self, trades: List[Dict]) -> bool:
        """Check for suspicious patterns in trade sizes"""
        sell_sizes = [t['amount'] for t in trades if t['type'] == 'sell' and t['success']]
        if not sell_sizes:
            return False
            
        # Check if only small sells succeed
        avg_size = sum(sell_sizes) / len(sell_sizes)
        small_sells = sum(1 for size in sell_sizes if size < avg_size * 0.2)
        
        return small_sells / len(sell_sizes) > 0.8  # 80% small sells is suspicious

    async def _get_recent_trades(self, token_address: str) -> List[Dict]:
        """Get recent trades for analysis"""
        # Implement this using Jupiter API or other data source
        pass