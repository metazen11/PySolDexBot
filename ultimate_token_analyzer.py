#!/usr/bin/env python3
"""
Ultimate Token Analyzer - The complete solution for finding exchange-worthy tokens
Combines database scanning, DexScreener live data, and comprehensive analysis
"""

import sqlite3
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import asyncio
import aiohttp

class UltimateTokenAnalyzer:
    """
    The definitive tool for finding tokens with real exchange potential
    """

    def __init__(self):
        self.database_file = 'raydium_pools.db'

        # API endpoints
        self.dexscreener_base = 'https://api.dexscreener.com/latest/dex'
        self.rugcheck_base = 'https://api.rugcheck.xyz'  # We'll implement basic checks

        # Rate limiting
        self.last_dex_request = 0
        self.min_dex_interval = 0.2  # 300 requests/minute

        # Enhanced filtering
        self.TIER_1_MIN_LIQUIDITY = 20000000  # $20M+ for Binance/Coinbase
        self.TIER_2_MIN_LIQUIDITY = 5000000   # $5M+ for major exchanges
        self.TIER_3_MIN_LIQUIDITY = 1000000   # $1M+ for mid-tier
        self.TIER_4_MIN_LIQUIDITY = 100000    # $100k+ for small exchanges

    def rate_limit_dexscreener(self):
        """Ensure we don't exceed rate limits"""
        now = time.time()
        elapsed = now - self.last_dex_request
        if elapsed < self.min_dex_interval:
            time.sleep(self.min_dex_interval - elapsed)
        self.last_dex_request = time.time()

    def get_token_data(self, token_address: str) -> Optional[Dict]:
        """Get comprehensive token data from DexScreener"""
        try:
            self.rate_limit_dexscreener()
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    # Get the highest liquidity pair
                    pairs = data['pairs']
                    best_pair = max(pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0))

                    return {
                        'price_usd': float(best_pair.get('priceUsd', 0)),
                        'price_changes': {
                            '5m': best_pair.get('priceChange', {}).get('m5', 0),
                            '1h': best_pair.get('priceChange', {}).get('h1', 0),
                            '6h': best_pair.get('priceChange', {}).get('h6', 0),
                            '24h': best_pair.get('priceChange', {}).get('h24', 0)
                        },
                        'volume': {
                            '5m': best_pair.get('volume', {}).get('m5', 0),
                            '1h': best_pair.get('volume', {}).get('h1', 0),
                            '6h': best_pair.get('volume', {}).get('h6', 0),
                            '24h': best_pair.get('volume', {}).get('h24', 0)
                        },
                        'transactions': {
                            'buys_5m': best_pair.get('txns', {}).get('m5', {}).get('buys', 0),
                            'sells_5m': best_pair.get('txns', {}).get('m5', {}).get('sells', 0),
                            'buys_1h': best_pair.get('txns', {}).get('h1', {}).get('buys', 0),
                            'sells_1h': best_pair.get('txns', {}).get('h1', {}).get('sells', 0)
                        },
                        'liquidity_usd': best_pair.get('liquidity', {}).get('usd', 0),
                        'market_cap': best_pair.get('fdv', 0),
                        'pair_address': best_pair.get('pairAddress', ''),
                        'dex': best_pair.get('dexId', ''),
                        'pair_created': best_pair.get('pairCreatedAt', 0),
                        'info': best_pair.get('info', {}),
                        'url': best_pair.get('url', '')
                    }
            return None

        except Exception as e:
            print(f"Error fetching data for {token_address}: {e}")
            return None

    def basic_security_check(self, token_data: Dict) -> Dict:
        """
        Basic security analysis (we'll enhance with Rugcheck later)
        """
        security = {
            'score': 50,  # Start neutral
            'flags': [],
            'risk_level': 'MODERATE'
        }

        if not token_data:
            security['score'] = 0
            security['risk_level'] = 'VERY HIGH'
            security['flags'].append('No trading data found')
            return security

        # Check liquidity stability (proxy for rug risk)
        liquidity = token_data.get('liquidity_usd', 0)
        if liquidity < 10000:
            security['score'] -= 30
            security['flags'].append('Very low liquidity')
        elif liquidity < 50000:
            security['score'] -= 15
            security['flags'].append('Low liquidity')

        # Check for extreme price volatility
        price_24h = token_data.get('price_changes', {}).get('24h', 0)
        if abs(price_24h) > 200:  # >200% change
            security['score'] -= 20
            security['flags'].append('Extreme volatility')
        elif abs(price_24h) > 100:  # >100% change
            security['score'] -= 10
            security['flags'].append('High volatility')

        # Check buy/sell pressure
        buys_5m = token_data.get('transactions', {}).get('buys_5m', 0)
        sells_5m = token_data.get('transactions', {}).get('sells_5m', 0)

        if buys_5m + sells_5m > 0:
            buy_ratio = buys_5m / (buys_5m + sells_5m)
            if buy_ratio < 0.2:  # Heavy selling
                security['score'] -= 15
                security['flags'].append('Heavy selling pressure')
            elif buy_ratio > 0.8:  # Strong buying
                security['score'] += 10
                security['flags'].append('Strong buying pressure')

        # Age-based security (very new = risky)
        pair_created = token_data.get('pair_created', 0)
        if pair_created > 0:
            age_hours = (time.time() - pair_created/1000) / 3600
            if age_hours < 1:
                security['score'] -= 15
                security['flags'].append('Very new token (< 1 hour)')
            elif age_hours < 6:
                security['score'] -= 5
                security['flags'].append('New token (< 6 hours)')

        # Volume consistency check
        volume_1h = token_data.get('volume', {}).get('h1', 0)
        volume_6h = token_data.get('volume', {}).get('h6', 0)

        if volume_6h > 0 and volume_1h > volume_6h/6 * 3:  # 1h volume > 50% of average
            security['score'] += 10
            security['flags'].append('Sustained volume')

        # Set risk level
        if security['score'] >= 80:
            security['risk_level'] = 'LOW'
        elif security['score'] >= 60:
            security['risk_level'] = 'MODERATE'
        elif security['score'] >= 40:
            security['risk_level'] = 'HIGH'
        else:
            security['risk_level'] = 'VERY HIGH'

        return security

    def calculate_exchange_potential(self, token_data: Dict, db_data: Dict, security: Dict) -> Dict:
        """
        Calculate potential for exchange listing
        """
        score = 0
        tier = "None"
        factors = []

        if not token_data:
            return {'score': 0, 'tier': 'None', 'factors': ['No data available']}

        liquidity = token_data.get('liquidity_usd', 0)
        market_cap = token_data.get('market_cap', 0)
        volume_24h = token_data.get('volume', {}).get('24h', 0)

        # Liquidity tier scoring
        if liquidity >= self.TIER_1_MIN_LIQUIDITY:
            score += 40
            tier = "Tier 1 (Binance/Coinbase)"
            factors.append(f"Tier 1 liquidity: ${liquidity:,.0f}")
        elif liquidity >= self.TIER_2_MIN_LIQUIDITY:
            score += 35
            tier = "Tier 2 (Major Exchange)"
            factors.append(f"Tier 2 liquidity: ${liquidity:,.0f}")
        elif liquidity >= self.TIER_3_MIN_LIQUIDITY:
            score += 25
            tier = "Tier 3 (Mid-tier Exchange)"
            factors.append(f"Tier 3 liquidity: ${liquidity:,.0f}")
        elif liquidity >= self.TIER_4_MIN_LIQUIDITY:
            score += 15
            tier = "Tier 4 (Small Exchange)"
            factors.append(f"Tier 4 liquidity: ${liquidity:,.0f}")
        else:
            score += 5
            tier = "DEX Only"

        # Market cap scoring
        if market_cap >= 100000000:  # $100M+
            score += 20
            factors.append(f"Large market cap: ${market_cap:,.0f}")
        elif market_cap >= 50000000:  # $50M+
            score += 15
            factors.append(f"Good market cap: ${market_cap:,.0f}")
        elif market_cap >= 10000000:  # $10M+
            score += 10
            factors.append(f"Decent market cap: ${market_cap:,.0f}")

        # Volume scoring
        if volume_24h > 0 and liquidity > 0:
            vol_ratio = volume_24h / liquidity
            if vol_ratio >= 2:
                score += 20
                factors.append(f"High volume ratio: {vol_ratio:.1f}x")
            elif vol_ratio >= 1:
                score += 15
                factors.append(f"Good volume ratio: {vol_ratio:.1f}x")
            elif vol_ratio >= 0.5:
                score += 10
                factors.append(f"Moderate volume ratio: {vol_ratio:.1f}x")

        # Security bonus/penalty
        security_score = security.get('score', 50)
        if security_score >= 80:
            score += 15
            factors.append("High security score")
        elif security_score >= 60:
            score += 10
            factors.append("Good security score")
        elif security_score < 40:
            score -= 10
            factors.append("Low security score")

        # Activity scoring
        buys_5m = token_data.get('transactions', {}).get('buys_5m', 0)
        sells_5m = token_data.get('transactions', {}).get('sells_5m', 0)
        total_txns = buys_5m + sells_5m

        if total_txns >= 10:
            score += 10
            factors.append(f"High activity: {total_txns} txns/5min")
        elif total_txns >= 5:
            score += 5
            factors.append(f"Good activity: {total_txns} txns/5min")

        # Pump.fun bonus
        if db_data.get('is_pump_token'):
            score += 8
            factors.append("Pump.fun graduate")

        return {
            'score': min(score, 100),
            'tier': tier,
            'factors': factors
        }

    def get_top_tokens(self, limit: int = 10) -> List[Dict]:
        """Get top tokens from database"""
        conn = sqlite3.connect(self.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row

        query = '''
            SELECT
                name,
                token_address,
                liquidity,
                volume24h,
                discovered_at,
                is_pump_token
            FROM pools
            WHERE
                discovered_at > datetime('now', '-24 hours')
                AND discovered_at < datetime('now', '-10 minutes')
                AND liquidity > 10000
                AND volume24h > 1000
                AND token_address IS NOT NULL
                AND token_address != ''
            ORDER BY
                liquidity DESC
            LIMIT ?
        '''

        cursor = conn.execute(query, (limit * 2,))
        tokens = [dict(row) for row in cursor]
        conn.close()
        return tokens

    def analyze_token(self, db_token: Dict) -> Optional[Dict]:
        """Complete analysis of a single token"""
        print(f"🔍 Analyzing {db_token['name']}...")

        # Get live data
        live_data = self.get_token_data(db_token['token_address'])
        if not live_data:
            return None

        # Security analysis
        security = self.basic_security_check(live_data)

        # Exchange potential
        exchange_potential = self.calculate_exchange_potential(live_data, db_token, security)

        # Skip low-potential tokens
        if exchange_potential['score'] < 30:
            return None

        return {
            'db_data': db_token,
            'live_data': live_data,
            'security': security,
            'exchange_potential': exchange_potential,
            'age_hours': round(
                (datetime.now() - db_token['discovered_at']).total_seconds() / 3600, 1
            )
        }

    def run_analysis(self, limit: int = 15) -> List[Dict]:
        """Run complete analysis"""
        print("🚀 Ultimate Token Analysis Starting...")
        print("📊 Fetching candidates from database...")

        candidates = self.get_top_tokens(limit * 2)
        print(f"Found {len(candidates)} candidates")

        results = []
        for candidate in candidates:
            try:
                analysis = self.analyze_token(candidate)
                if analysis:
                    results.append(analysis)

                if len(results) >= limit:
                    break

            except Exception as e:
                print(f"Error analyzing {candidate.get('name', 'Unknown')}: {e}")
                continue

        # Sort by exchange potential score
        results.sort(key=lambda x: x['exchange_potential']['score'], reverse=True)
        return results

    def display_results(self, results: List[Dict]):
        """Display comprehensive results"""
        print("\n" + "="*100)
        print("🎯 ULTIMATE TOKEN ANALYSIS - Exchange Listing Potential")
        print("="*100)

        if not results:
            print("❌ No high-potential tokens found.")
            return

        for i, result in enumerate(results, 1):
            db_data = result['db_data']
            live_data = result['live_data']
            security = result['security']
            exchange = result['exchange_potential']

            print(f"\n{i}. {db_data['name']} 🎯 Exchange Score: {exchange['score']}/100")
            print(f"   🏆 {exchange['tier']}")
            print(f"   📍 Age: {result['age_hours']:.1f} hours")

            # Price and market data
            price = live_data.get('price_usd', 0)
            liquidity = live_data.get('liquidity_usd', 0)
            market_cap = live_data.get('market_cap', 0)
            volume_24h = live_data.get('volume', {}).get('24h', 0)

            print(f"   💰 Price: ${price:.8f}")
            print(f"   🏦 Liquidity: ${liquidity:,.0f}")
            print(f"   📊 Volume 24h: ${volume_24h:,.0f}")
            print(f"   🏷️  Market Cap: ${market_cap:,.0f}")

            # Price changes
            changes = live_data.get('price_changes', {})
            change_str = []
            for period, change in changes.items():
                if change != 0:
                    change_str.append(f"{period}: {change:+.1f}%")
            if change_str:
                print(f"   📈 Changes: {' | '.join(change_str)}")

            # Security analysis
            print(f"   🛡️  Security: {security['score']}/100 ({security['risk_level']})")
            if security['flags']:
                print(f"   ⚠️  Flags: {' | '.join(security['flags'][:3])}")

            # Exchange factors
            if exchange['factors']:
                print(f"   🎯 Key Factors: {' | '.join(exchange['factors'][:3])}")

            # Trading activity
            txns = live_data.get('transactions', {})
            buys = txns.get('buys_5m', 0)
            sells = txns.get('sells_5m', 0)
            if buys + sells > 0:
                print(f"   ⚡ Activity (5min): {buys} buys, {sells} sells")

            # Investment recommendation
            if exchange['score'] >= 80:
                print("   🚀 STRONG BUY - Exceptional exchange potential")
            elif exchange['score'] >= 65:
                print("   💰 BUY - High exchange potential")
            elif exchange['score'] >= 50:
                print("   📈 CONSIDER - Good potential")
            elif exchange['score'] >= 35:
                print("   ⚠️  RISKY - Monitor closely")

            # Links
            print(f"   🔗 DexScreener: https://dexscreener.com/solana/{db_data['token_address']}")

            if db_data.get('is_pump_token'):
                print("   🎰 Pump.fun Graduate")

def main():
    """Run the ultimate analysis"""
    analyzer = UltimateTokenAnalyzer()

    print("🎯 Ultimate Token Analyzer")
    print("🔍 Finding tokens with real exchange listing potential")
    print("⏱️  This may take 1-2 minutes for comprehensive analysis...")

    results = analyzer.run_analysis(limit=10)
    analyzer.display_results(results)

    print("\n" + "="*100)
    print("💡 Investment Strategy:")
    print("- Focus on Tier 1-2 tokens with scores >65")
    print("- Look for high security scores (>60) and low risk")
    print("- Strong buying pressure and sustained volume are key")
    print("- Set stop losses at -25% for high-potential plays")
    print("- Consider diversifying across 3-5 top picks")
    print("="*100)

if __name__ == "__main__":
    main()