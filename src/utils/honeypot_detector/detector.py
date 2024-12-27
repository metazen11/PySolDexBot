from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime, timedelta
from .trade_checker import TradeChecker
from .tax_checker import TaxChecker
from .pool_checker import PoolChecker
from .contract_checker import ContractChecker

logger = logging.getLogger(__name__)

class HoneypotDetector:
    def __init__(self, config: Dict):
        self.config = config
        self.trade_checker = TradeChecker(config)
        self.tax_checker = TaxChecker(config)
        self.pool_checker = PoolChecker(config)
        self.contract_checker = ContractChecker(config)
        
    async def analyze_token(self, token_address: str) -> Dict:
        """Comprehensive token analysis for honeypot detection"""
        try:
            # Run all checks concurrently
            results = await asyncio.gather(
                self.trade_checker.check_trade_history(token_address),
                self.tax_checker.check_tax_rates(token_address),
                self.pool_checker.verify_pool_manipulation(token_address),
                self.contract_checker.check_contract_risks(token_address),
                return_exceptions=True
            )
            
            # Combine all results
            is_honeypot = False
            risk_factors = []
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in honeypot analysis: {result}")
                    continue
                    
                if result.get('is_risk', False):
                    is_honeypot = True
                    risk_factors.extend(result.get('risk_factors', []))
                    
            return {
                'is_honeypot': is_honeypot,
                'risk_factors': risk_factors,
                'analysis_time': datetime.now(),
                'confidence_score': self._calculate_confidence_score(results)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing token {token_address}: {e}")
            return {'is_honeypot': True, 'risk_factors': ['Analysis failed']}

    def _calculate_confidence_score(self, results: List[Dict]) -> float:
        """Calculate confidence score for honeypot detection"""
        try:
            # Weight different factors
            weights = {
                'trade_history': 0.3,
                'tax_rates': 0.25,
                'pool_manipulation': 0.25,
                'contract_risks': 0.2
            }
            
            total_score = 0
            total_weight = 0
            
            for result, (check_type, weight) in zip(results, weights.items()):
                if isinstance(result, Exception):
                    continue
                    
                # Convert binary risk to score (1 = no risk, 0 = risk)
                factor_score = 0 if result.get('is_risk', True) else 1
                total_score += factor_score * weight
                total_weight += weight
                
            return (total_score / total_weight * 100) if total_weight > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0  # Return lowest score on error