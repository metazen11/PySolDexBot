import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ...utils.honeypot_detector.detector import HoneypotDetector
from ...utils.price_monitor.monitor import PriceMonitor
from ...utils.token_checker import TokenAPIChecker

logger = logging.getLogger(__name__)

class MomentumScanner:
    def __init__(self, config: Dict):
        self.config = config
        self.honeypot_detector = HoneypotDetector(config)
        self.price_monitor = PriceMonitor(config)
        self.token_checker = TokenAPIChecker(config)
        
        # Initialize settings from config
        self.min_liquidity_usd = config.get('min_liquidity_usd', 50000)
        self.min_volume_24h = config.get('min_volume_24h', 10000)
        self.min_holders = config.get('min_holders', 200)
        self.max_mcap = config.get('max_market_cap', 10_000_000)  # $10M max
        
        # Momentum settings
        self.volume_spike_threshold = config.get('volume_spike_threshold', 3.0)  # 300% increase
        self.price_increase_threshold = config.get('price_increase_threshold', 0.05)  # 5% increase
        self.min_price_usd = config.get('min_price_usd', 0.000001)  # Minimum price to consider
        
        # Track opportunities and state
        self.opportunities = {}
        self.blacklisted_tokens = set()
        self.is_running = False

    async def start(self):
        """Start the momentum scanner"""
        if self.is_running:
            return

        logger.info("Starting momentum scanner...")
        self.is_running = True
        await self.token_checker.initialize()
        await self.price_monitor.start()

        try:
            while self.is_running:
                await self._scan_cycle()
                await asyncio.sleep(60)  # Scan every minute
        except Exception as e:
            logger.error(f"Error in scanner main loop: {e}")
            await self.stop()

    async def stop(self):
        """Stop the scanner"""
        logger.info("Stopping momentum scanner...")
        self.is_running = False
        await self.price_monitor.stop()

    async def _scan_cycle(self):
        """Run a complete scan cycle"""
        try:
            # Get new token pairs
            pairs = await self._get_new_pairs()
            
            for pair in pairs:
                if not await self._should_analyze_pair(pair):
                    continue

                # Full analysis if pair meets initial criteria
                await self._analyze_opportunity(pair)

            # Update existing opportunities
            await self._update_opportunities()
            
            # Cleanup old opportunities
            self._cleanup_old_opportunities()

        except Exception as e:
            logger.error(f"Error in scan cycle: {e}")

    async def _should_analyze_pair(self, pair: Dict) -> bool:
        """Determine if pair should be analyzed"""
        try:
            # Skip if token is blacklisted
            if pair['token_mint'] in self.blacklisted_tokens:
                return False

            # Basic criteria checks
            if not self._meets_basic_criteria(pair):
                return False

            # Check if token is already being tracked
            if pair['token_mint'] in self.opportunities:
                return False

            # Initial safety check
            is_safe = await self._quick_safety_check(pair)
            if not is_safe:
                self.blacklisted_tokens.add(pair['token_mint'])
                return False

            return True

        except Exception as e:
            logger.error(f"Error in pair analysis check: {e}")
            return False

    def _meets_basic_criteria(self, pair: Dict) -> bool:
        """Check if pair meets basic criteria"""
        try:
            return (
                pair.get('liquidity_usd', 0) >= self.min_liquidity_usd and
                pair.get('volume_24h', 0) >= self.min_volume_24h and
                pair.get('market_cap', 0) <= self.max_mcap and
                pair.get('price_usd', 0) >= self.min_price_usd
            )
        except Exception as e:
            logger.error(f"Error in basic criteria check: {e}")
            return False

    async def _analyze_opportunity(self, pair: Dict):
        """Analyze a potential opportunity"""
        try:
            token_mint = pair['token_mint']
            
            # Comprehensive safety check
            safety_score = await self._comprehensive_safety_check(pair)
            if safety_score < 80:  # Minimum 80% safety score
                return

            # Check momentum indicators
            momentum_score = await self._calculate_momentum_score(pair)
            if momentum_score < 70:  # Minimum 70% momentum score
                return

            # Add to opportunities if it passes all checks
            await self._add_opportunity(pair, safety_score, momentum_score)

        except Exception as e:
            logger.error(f"Error analyzing opportunity: {e}")

    async def _comprehensive_safety_check(self, pair: Dict) -> float:
        """Comprehensive token safety analysis"""
        try:
            # Get detailed token info
            token_info = await self.token_checker.get_token_info(pair['token_mint'])
            
            # Run honeypot detection
            honeypot_analysis = await self.honeypot_detector.analyze_token(pair['token_mint'])
            
            # Scoring factors
            factors = [
                # Basic metrics
                token_info['holder_count'] >= self.min_holders,
                token_info['liquidity_usd'] >= self.min_liquidity_usd,
                
                # Contract safety
                not honeypot_analysis['is_honeypot'],
                token_info['verified_contract'],
                
                # Liquidity metrics
                token_info['lp_locked'],
                token_info['lp_lock_time_days'] >= 30,
                
                # Trading patterns
                token_info['unique_holders'] >= 100,
                token_info['buy_sell_ratio'] >= 0.7,  # Healthy buy/sell ratio
                
                # Additional safety checks
                not token_info['has_mint_function'],
                not token_info['has_blacklist_function'],
                token_info['owner_wallet_percentage'] <= 5,  # Max 5% owned by creator
            ]
            
            # Calculate score (0-100)
            return (sum(1 for f in factors if f) / len(factors)) * 100

        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            return 0

    async def _calculate_momentum_score(self, pair: Dict) -> float:
        """Calculate momentum score based on multiple factors"""
        try:
            # Get price history
            price_data = await self._get_price_history(pair['token_mint'])
            df = pd.DataFrame(price_data)
            
            if df.empty:
                return 0

            # Calculate technical indicators
            df['rsi'] = self._calculate_rsi(df['close'])
            df['macd'], df['signal'] = self._calculate_macd(df['close'])
            df['volume_sma'] = df['volume'].rolling(window=20).mean()

            # Scoring factors
            factors = [
                # Price momentum
                df['close'].iloc[-1] > df['close'].iloc[-2],  # Price increasing
                df['close'].iloc[-1] > df['close'].rolling(24).mean().iloc[-1],  # Above 24-period MA
                
                # Volume momentum
                df['volume'].iloc[-1] > df['volume_sma'].iloc[-1] * self.volume_spike_threshold,
                df['volume'].iloc[-1] > df['volume'].iloc[-2],  # Volume increasing
                
                # Technical indicators
                df['rsi'].iloc[-1] > 50,  # RSI showing strength
                df['macd'].iloc[-1] > df['signal'].iloc[-1],  # MACD bullish
                
                # Price action
                self._calculate_price_change(df) >= self.price_increase_threshold,
                self._detect_accumulation_pattern(df)
            ]
            
            # Calculate score (0-100)
            return (sum(1 for f in factors if f) / len(factors)) * 100

        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return 0

    async def _add_opportunity(self, pair: Dict, safety_score: float, momentum_score: float):
        """Add new trading opportunity"""
        try:
            token_mint = pair['token_mint']
            
            logger.info(f"New opportunity found: {pair['symbol']}")
            logger.info(f"Safety Score: {safety_score:.1f}")
            logger.info(f"Momentum Score: {momentum_score:.1f}")
            
            self.opportunities[token_mint] = {
                'symbol': pair['symbol'],
                'found_at': datetime.now(),
                'found_price': pair['price_usd'],
                'current_price': pair['price_usd'],
                'volume_24h': pair['volume_24h'],
                'liquidity_usd': pair['liquidity_usd'],
                'market_cap': pair['market_cap'],
                'safety_score': safety_score,
                'momentum_score': momentum_score,
                'highest_price': pair['price_usd'],
                'lowest_price': pair['price_usd'],
                'updates': 1
            }
            
            # Start monitoring price
            await self.price_monitor.add_token(token_mint)

        except Exception as e:
            logger.error(f"Error adding opportunity: {e}")

    def _cleanup_old_opportunities(self):
        """Remove opportunities older than 24 hours"""
        current_time = datetime.now()
        expired_tokens = [
            token for token, opp in self.opportunities.items()
            if (current_time - opp['found_at']) > timedelta(hours=24)
        ]
        
        for token in expired_tokens:
            self.opportunities.pop(token)
            asyncio.create_task(self.price_monitor.remove_token(token))

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _calculate_macd(prices: pd.Series) -> tuple:
        """Calculate MACD and Signal line"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal

    @staticmethod
    def _calculate_price_change(df: pd.DataFrame) -> float:
        """Calculate price change percentage"""
        if len(df) < 2:
            return 0
        return (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]

    @staticmethod
    def _detect_accumulation_pattern(df: pd.DataFrame) -> bool:
        """Detect accumulation pattern"""
        if len(df) < 20:
            return False
            
        recent_data = df.tail(20)
        volume_increasing = recent_data['volume'].is_monotonic_increasing
        price_stable = (
            recent_data['close'].max() - recent_data['close'].min()
        ) / recent_data['close'].mean() < 0.03  # 3% range
        
        return volume_increasing and price_stable