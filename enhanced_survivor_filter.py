#!/usr/bin/env python3
"""
Enhanced Survivor Token Filter with DexScreener API Integration
Real-time price, volume, and momentum analysis for exchange potential
"""

import sqlite3
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import asyncio
import aiohttp

class EnhancedSurvivorFilter:
    """
    Advanced token analysis with DexScreener API for real-time data
    """

    def __init__(self):
        self.database_file = 'raydium_pools.db'

        # DexScreener API endpoints
        self.dexscreener_base = 'https://api.dexscreener.com/latest/dex'
        self.dexscreener_tokens = 'https://api.dexscreener.com/latest/dex/tokens'

        # Rate limiting
        self.last_dex_request = 0
        self.min_dex_interval = 0.2  # 300 requests/minute = 5 requests/second

        # Enhanced thresholds
        self.MIN_AGE_MINUTES = 10
        self.MAX_AGE_HOURS = 24
        self.MIN_LIQUIDITY_USD = 5000
        self.MIN_VOLUME_24H = 1000

    def rate_limit_dexscreener(self):
        """Ensure we don't exceed DexScreener rate limits"""
        now = time.time()
        elapsed = now - self.last_dex_request
        if elapsed < self.min_dex_interval:
            time.sleep(self.min_dex_interval - elapsed)
        self.last_dex_request = time.time()

    def get_dexscreener_data(self, token_address: str) -> Optional[Dict]:
        """
        Get comprehensive token data from DexScreener API
        """
        try:
            self.rate_limit_dexscreener()

            url = f"{self.dexscreener_tokens}/{token_address}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    # Get the highest liquidity pair (usually most relevant)
                    pairs = data['pairs']
                    best_pair = max(pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0))

                    return {
                        'price_usd': float(best_pair.get('priceUsd', 0)),
                        'price_change_5m': best_pair.get('priceChange', {}).get('m5', 0),
                        'price_change_1h': best_pair.get('priceChange', {}).get('h1', 0),
                        'price_change_6h': best_pair.get('priceChange', {}).get('h6', 0),
                        'price_change_24h': best_pair.get('priceChange', {}).get('h24', 0),
                        'volume_5m': best_pair.get('volume', {}).get('m5', 0),
                        'volume_1h': best_pair.get('volume', {}).get('h1', 0),
                        'volume_6h': best_pair.get('volume', {}).get('h6', 0),
                        'volume_24h': best_pair.get('volume', {}).get('h24', 0),
                        'liquidity_usd': best_pair.get('liquidity', {}).get('usd', 0),
                        'market_cap': best_pair.get('fdv', 0),  # Fully diluted valuation
                        'buys_5m': best_pair.get('txns', {}).get('m5', {}).get('buys', 0),
                        'sells_5m': best_pair.get('txns', {}).get('m5', {}).get('sells', 0),
                        'buys_1h': best_pair.get('txns', {}).get('h1', {}).get('buys', 0),
                        'sells_1h': best_pair.get('txns', {}).get('h1', {}).get('sells', 0),
                        'pair_address': best_pair.get('pairAddress', ''),
                        'dex': best_pair.get('dexId', ''),
                        'pair_age': best_pair.get('pairCreatedAt', 0)
                    }

            return None

        except Exception as e:
            print(f"Error fetching DexScreener data for {token_address}: {e}")
            return None

    def analyze_momentum(self, dex_data: Dict) -> Dict:
        """
        Analyze momentum and trading patterns from DexScreener data
        """
        momentum = {
            'score': 0,
            'signals': [],
            'risk_level': 'HIGH',
            'activity_level': 'LOW'
        }

        if not dex_data:
            return momentum

        # Price momentum analysis
        price_5m = dex_data.get('price_change_5m', 0)
        price_1h = dex_data.get('price_change_1h', 0)
        price_6h = dex_data.get('price_change_6h', 0)
        price_24h = dex_data.get('price_change_24h', 0)

        # Volume analysis
        volume_5m = dex_data.get('volume_5m', 0)
        volume_1h = dex_data.get('volume_1h', 0)
        volume_6h = dex_data.get('volume_6h', 0)
        volume_24h = dex_data.get('volume_24h', 0)

        # Transaction analysis
        buys_5m = dex_data.get('buys_5m', 0)
        sells_5m = dex_data.get('sells_5m', 0)
        buys_1h = dex_data.get('buys_1h', 0)
        sells_1h = dex_data.get('sells_1h', 0)

        # Momentum scoring
        score = 0

        # 1. Recent price momentum (5min-1h)
        if price_5m > 5:  # +5% in 5 minutes
            score += 15
            momentum['signals'].append("🚀 Strong 5min pump")
        elif price_5m > 2:
            score += 8
            momentum['signals'].append("📈 Good 5min momentum")
        elif price_5m < -5:
            score -= 10
            momentum['signals'].append("📉 Recent dump")

        if price_1h > 10:  # +10% in 1 hour
            score += 20
            momentum['signals'].append("🔥 Hot 1h momentum")
        elif price_1h > 5:
            score += 10
            momentum['signals'].append("📊 Good 1h growth")

        # 2. Volume momentum
        if volume_1h > volume_6h / 6:  # 1h volume > average hourly
            score += 15
            momentum['signals'].append("💪 High volume surge")

        if volume_5m > volume_1h / 12:  # 5min volume > average 5min
            score += 10
            momentum['signals'].append("⚡ Recent volume spike")

        # 3. Buy/Sell pressure
        if buys_5m > 0 and sells_5m > 0:
            buy_ratio_5m = buys_5m / (buys_5m + sells_5m)
            if buy_ratio_5m > 0.7:  # 70%+ buys
                score += 15
                momentum['signals'].append(f"🟢 Strong buying pressure ({buy_ratio_5m:.1%})")
            elif buy_ratio_5m > 0.6:
                score += 8
                momentum['signals'].append(f"📈 Good buying pressure ({buy_ratio_5m:.1%})")
            elif buy_ratio_5m < 0.3:
                score -= 10
                momentum['signals'].append(f"🔴 Heavy selling pressure ({buy_ratio_5m:.1%})")

        # 4. Activity level assessment
        total_txns_5m = buys_5m + sells_5m
        total_txns_1h = buys_1h + sells_1h

        if total_txns_5m >= 5:
            momentum['activity_level'] = 'VERY HIGH'
            score += 10
        elif total_txns_1h >= 10:
            momentum['activity_level'] = 'HIGH'
            score += 5
        elif total_txns_1h >= 5:
            momentum['activity_level'] = 'MODERATE'
        else:
            momentum['activity_level'] = 'LOW'
            score -= 5

        # 5. Stability vs volatility
        if abs(price_24h) < 20 and price_1h > 0:  # Steady growth
            score += 10
            momentum['signals'].append("🎯 Stable upward trend")
        elif abs(price_24h) > 100:  # Very volatile
            score -= 5
            momentum['signals'].append("⚠️ High volatility")

        # Risk assessment
        momentum['score'] = max(0, min(100, score))

        if momentum['score'] >= 70:
            momentum['risk_level'] = 'LOW'
        elif momentum['score'] >= 50:
            momentum['risk_level'] = 'MODERATE'
        elif momentum['score'] >= 30:
            momentum['risk_level'] = 'HIGH'
        else:
            momentum['risk_level'] = 'VERY HIGH'

        return momentum

    def calculate_enhanced_survivor_score(self, token_data: Dict, dex_data: Dict, momentum: Dict) -> float:
        """
        Enhanced scoring with DexScreener data
        """
        score = 0.0

        # Use DexScreener data if available, fallback to database
        liquidity = dex_data.get('liquidity_usd', token_data.get('liquidity', 0)) if dex_data else token_data.get('liquidity', 0)
        volume_24h = dex_data.get('volume_24h', token_data.get('volume24h', 0)) if dex_data else token_data.get('volume24h', 0)
        market_cap = dex_data.get('market_cap', liquidity * 2) if dex_data else liquidity * 2

        # Age factor
        age_hours = (datetime.now() - token_data['discovered_at']).total_seconds() / 3600
        if 0.5 <= age_hours <= 2:
            score += 20
        elif 0.25 <= age_hours <= 6:
            score += 15
        elif age_hours < 0.25:
            score += 5

        # Liquidity scoring (exchange listing potential)
        if liquidity >= 20000000:  # $20M+
            score += 35
        elif liquidity >= 10000000:  # $10M+
            score += 30
        elif liquidity >= 5000000:   # $5M+
            score += 25
        elif liquidity >= 1000000:   # $1M+
            score += 20
        elif liquidity >= 500000:    # $500k+
            score += 15
        elif liquidity >= 100000:    # $100k+
            score += 10
        elif liquidity >= 25000:     # $25k+
            score += 5

        # Volume momentum
        if volume_24h > 0 and liquidity > 0:
            vol_ratio = volume_24h / liquidity
            if vol_ratio >= 5:
                score += 25
            elif vol_ratio >= 3:
                score += 20
            elif vol_ratio >= 1:
                score += 15
            elif vol_ratio >= 0.5:
                score += 10
            else:
                score += 5

        # Market cap bonus
        if market_cap >= 100000000:  # $100M+
            score += 15
        elif market_cap >= 50000000:  # $50M+
            score += 10
        elif market_cap >= 10000000:  # $10M+
            score += 5

        # Momentum bonus from DexScreener analysis
        if momentum:
            momentum_score = momentum.get('score', 0)
            score += momentum_score * 0.3  # 30% weight to momentum

        # Platform bonus
        if token_data.get('is_pump_token'):
            score += 8

        return min(score, 100)

    def get_db_connection(self):
        conn = sqlite3.connect(self.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn

    def find_enhanced_survivors(self, limit: int = 15, check_live_data: bool = True) -> List[Dict]:
        """
        Find survivors with enhanced DexScreener data
        """
        conn = self.get_db_connection()

        query = '''
            SELECT
                name,
                token_address,
                liquidity,
                volume24h,
                discovered_at,
                is_pump_token,
                ROUND((liquidity * 2), 2) as market_cap_estimate
            FROM pools
            WHERE
                discovered_at > datetime('now', '-24 hours')
                AND discovered_at < datetime('now', '-10 minutes')
                AND liquidity > 2000
                AND volume24h > 500
                AND token_address IS NOT NULL
                AND token_address != ''
            ORDER BY
                liquidity DESC,
                volume24h DESC
            LIMIT ?
        '''

        cursor = conn.execute(query, (limit * 3,))  # Get more to filter
        tokens = []

        for row in cursor:
            token_data = dict(row)

            if not check_live_data:
                # Quick mode without live data
                score = self.calculate_enhanced_survivor_score(token_data, None, None)
                if score >= 25:
                    token_data['survivor_score'] = score
                    token_data['age_hours'] = round(
                        (datetime.now() - token_data['discovered_at']).total_seconds() / 3600, 1
                    )
                    tokens.append(token_data)
                continue

            # Get live DexScreener data
            print(f"🔍 Analyzing {token_data['name']} with DexScreener...")
            dex_data = self.get_dexscreener_data(token_data['token_address'])

            if not dex_data:
                continue  # Skip tokens not found on DexScreener

            # Analyze momentum
            momentum = self.analyze_momentum(dex_data)

            # Calculate enhanced score
            score = self.calculate_enhanced_survivor_score(token_data, dex_data, momentum)

            if score >= 35:  # Higher threshold for live analysis
                token_data['survivor_score'] = score
                token_data['dex_data'] = dex_data
                token_data['momentum'] = momentum
                token_data['age_hours'] = round(
                    (datetime.now() - token_data['discovered_at']).total_seconds() / 3600, 1
                )
                tokens.append(token_data)

                if len(tokens) >= limit:
                    break

        conn.close()

        # Sort by score
        return sorted(tokens, key=lambda x: x['survivor_score'], reverse=True)

    def display_enhanced_results(self, tokens: List[Dict]):
        """
        Display enhanced results with DexScreener data
        """
        print("\n" + "="*90)
        print("🎯 ENHANCED SURVIVOR ANALYSIS - Real-time DexScreener Data")
        print("="*90)

        if not tokens:
            print("❌ No high-potential survivors found with current filters.")
            print("💡 Try lowering thresholds or checking during active trading hours.")
            return

        for i, token in enumerate(tokens, 1):
            score = token['survivor_score']
            dex_data = token.get('dex_data', {})
            momentum = token.get('momentum', {})

            # Basic info
            print(f"\n{i}. {token['name']} ⭐ Score: {score:.0f}/100")

            # Live price and market data
            if dex_data:
                price = dex_data.get('price_usd', 0)
                liquidity = dex_data.get('liquidity_usd', token['liquidity'])
                market_cap = dex_data.get('market_cap', liquidity * 2)
                volume_24h = dex_data.get('volume_24h', token['volume24h'])

                print(f"   💰 Price: ${price:.8f}")
                print(f"   📊 Liquidity: ${liquidity:,.0f}")
                print(f"   📈 Volume 24h: ${volume_24h:,.0f}")
                print(f"   🏷️  Market Cap: ${market_cap:,.0f}")

                # Price changes
                changes = []
                if dex_data.get('price_change_5m'):
                    changes.append(f"5m: {dex_data['price_change_5m']:+.1f}%")
                if dex_data.get('price_change_1h'):
                    changes.append(f"1h: {dex_data['price_change_1h']:+.1f}%")
                if dex_data.get('price_change_24h'):
                    changes.append(f"24h: {dex_data['price_change_24h']:+.1f}%")

                if changes:
                    print(f"   📊 Price Changes: {' | '.join(changes)}")

                # Recent activity
                buys_5m = dex_data.get('buys_5m', 0)
                sells_5m = dex_data.get('sells_5m', 0)
                if buys_5m + sells_5m > 0:
                    print(f"   ⚡ Recent Activity: {buys_5m} buys, {sells_5m} sells (5min)")

            # Momentum analysis
            if momentum:
                print(f"   🎯 Momentum: {momentum.get('score', 0)}/100 ({momentum.get('activity_level', 'LOW')})")
                print(f"   ⚠️  Risk Level: {momentum.get('risk_level', 'HIGH')}")

                signals = momentum.get('signals', [])
                if signals:
                    print(f"   📡 Signals: {' | '.join(signals[:3])}")  # Show top 3 signals

            # Investment recommendation
            if score >= 80:
                print("   🚀 STRONG BUY - Exceptional potential")
            elif score >= 65:
                print("   💰 BUY - Strong potential")
            elif score >= 50:
                print("   📈 CONSIDER - Good momentum")
            elif score >= 35:
                print("   ⚠️  RISKY - Monitor closely")
            else:
                print("   🔴 AVOID - High risk")

            print(f"   📍 Age: {token['age_hours']:.1f} hours")
            print(f"   🔗 DexScreener: https://dexscreener.com/solana/{token['token_address']}")

            if token.get('is_pump_token'):
                print("   🎰 Pump.fun Graduate")

def main():
    """Run the enhanced survivor filter"""
    filter = EnhancedSurvivorFilter()

    print("🔍 Enhanced Survivor Analysis with DexScreener API")
    print("📊 Real-time price, volume, and momentum tracking")
    print("⏱️  This may take 30-60 seconds for live data...")

    # Get enhanced survivors with live data
    survivors = filter.find_enhanced_survivors(limit=10, check_live_data=True)

    # Display results
    filter.display_enhanced_results(survivors)

    print("\n" + "="*90)
    print("💡 Enhanced Investment Strategy:")
    print("- Focus on tokens with Momentum Score >60 and Risk Level LOW-MODERATE")
    print("- Look for 5min price pumps with high volume")
    print("- Strong buying pressure (>70% buy ratio) is bullish")
    print("- Pump.fun graduates have higher success rates")
    print("- Set stop losses at -30% for momentum plays")
    print("="*90)

if __name__ == "__main__":
    main()