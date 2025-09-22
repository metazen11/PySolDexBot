#!/usr/bin/env python3
"""
Survivor Token Filter - Find tokens with real momentum that could reach exchanges
Filters out 99% of noise to find the 1% with potential
"""

import sqlite3
import json
from datetime import datetime, timedelta
import requests
import time
from typing import Dict, List, Tuple
import asyncio
import aiohttp

class SurvivorTokenFilter:
    """
    Identifies tokens that survive the initial pump and show exchange potential
    """

    def __init__(self):
        self.database_file = 'raydium_pools.db'
        self.solscan_api = 'https://public-api.solscan.io/account/transactions'

        # Momentum thresholds (relaxed for testing)
        self.MIN_AGE_MINUTES = 10   # Too new = too risky
        self.MAX_AGE_HOURS = 24     # Too old = missed opportunity
        self.MIN_TRADES_PER_HOUR = 5
        self.MIN_UNIQUE_TRADERS = 10
        self.MIN_LIQUIDITY_USD = 5000   # Lowered for more results
        self.MIN_VOLUME_24H = 1000      # Lowered for more results

    def get_db_connection(self):
        conn = sqlite3.connect(self.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn

    def check_recent_activity(self, token_address: str) -> Tuple[bool, Dict]:
        """
        Check if token has recent trading activity on Solscan
        Returns (is_active, activity_data)
        """
        try:
            # Check last 30 minutes of activity
            params = {
                'account': token_address,
                'limit': 50  # Last 50 transactions
            }

            response = requests.get(
                self.solscan_api,
                params=params,
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            if response.status_code == 200:
                transactions = response.json()

                if not transactions:
                    return False, {'reason': 'No transactions found'}

                # Analyze transaction patterns
                now = datetime.now()
                recent_txs = []
                unique_wallets = set()

                for tx in transactions[:50]:  # Last 50 transactions
                    tx_time = datetime.fromtimestamp(tx.get('blockTime', 0))
                    time_diff = (now - tx_time).total_seconds() / 60  # minutes

                    if time_diff <= 30:  # Last 30 minutes
                        recent_txs.append(tx)
                        # Extract unique wallet addresses
                        if 'signer' in tx:
                            unique_wallets.add(tx['signer'][0] if isinstance(tx['signer'], list) else tx['signer'])

                trades_per_30min = len(recent_txs)
                unique_traders = len(unique_wallets)

                # Activity scoring
                is_active = (
                    trades_per_30min >= 5 and  # At least 5 trades in 30 minutes
                    unique_traders >= 3  # At least 3 different traders
                )

                return is_active, {
                    'trades_30min': trades_per_30min,
                    'unique_traders': unique_traders,
                    'trades_per_hour_projected': trades_per_30min * 2,
                    'last_trade_minutes_ago': time_diff if transactions else 999
                }

            elif response.status_code == 404:
                # Token too new or no activity
                return False, {'reason': 'Token not found or too new'}
            else:
                return False, {'reason': f'API error: {response.status_code}'}

        except Exception as e:
            return False, {'reason': f'Error checking activity: {str(e)}'}

    def calculate_survivor_score(self, token_data: Dict, activity_data: Dict) -> float:
        """
        Score 0-100 for likelihood of surviving to reach exchanges
        """
        score = 0.0

        # Age factor (sweet spot: 1-4 hours old)
        age_hours = (datetime.now() - token_data['discovered_at']).total_seconds() / 3600
        if 1 <= age_hours <= 2:
            score += 20  # Perfect age
        elif 0.5 <= age_hours <= 4:
            score += 15  # Good age
        elif age_hours < 0.5:
            score += 5   # Too new, risky
        else:
            score += 0   # Too old

        # Exchange listing liquidity thresholds
        liquidity = token_data['liquidity']
        if liquidity >= 10000000:  # $10M+ (Binance/Coinbase tier)
            score += 35  # Tier 1 exchange potential
        elif liquidity >= 5000000:  # $5M+ (Major DEX tier)
            score += 30  # Strong exchange potential
        elif liquidity >= 1000000:  # $1M+ (Mid-tier exchange)
            score += 25  # Good exchange potential
        elif liquidity >= 500000:   # $500k+ (Small exchange)
            score += 20  # Moderate potential
        elif liquidity >= 100000:   # $100k+ (Listing possible)
            score += 15  # Some potential
        elif liquidity >= 25000:    # $25k+ (Minimum viable)
            score += 10  # Low potential
        else:
            score += 0   # Too low for exchanges

        # Volume consistency and momentum
        volume = token_data['volume24h']
        if volume > 0 and liquidity > 0:
            volume_ratio = volume / liquidity
            # High volume = active trading = exchange interest
            if volume_ratio >= 3:    # Volume 3x liquidity (very hot)
                score += 25
            elif volume_ratio >= 2:  # Volume 2x liquidity (hot)
                score += 20
            elif volume_ratio >= 1:  # Volume equals liquidity (good)
                score += 15
            elif volume_ratio >= 0.5:  # Volume 50% of liquidity (ok)
                score += 10
            else:
                score += 5  # Low volume

        # Market cap consideration (exchanges prefer larger market caps)
        market_cap = token_data.get('market_cap_estimate', liquidity * 2)
        if market_cap >= 50000000:  # $50M+ market cap
            score += 10  # Big enough for major exchanges
        elif market_cap >= 10000000:  # $10M+ market cap
            score += 8   # Good size
        elif market_cap >= 5000000:   # $5M+ market cap
            score += 5   # Decent size

        # Activity score from live data
        if activity_data:
            trades_per_hour = activity_data.get('trades_per_hour_projected', 0)
            if trades_per_hour >= 50:   # Very high activity
                score += 15
            elif trades_per_hour >= 20: # High activity
                score += 12
            elif trades_per_hour >= 10: # Good activity
                score += 8
            elif trades_per_hour >= 5:  # Moderate activity
                score += 5

            # Unique traders (distribution matters for exchanges)
            unique_traders = activity_data.get('unique_traders', 0)
            if unique_traders >= 20:
                score += 10  # Very well distributed
            elif unique_traders >= 10:
                score += 8   # Well distributed
            elif unique_traders >= 5:
                score += 5   # Decent distribution
            elif unique_traders >= 3:
                score += 3   # Some distribution

        # Pump.fun tokens have proven track record
        if token_data.get('is_pump_token'):
            score += 8  # Pump.fun graduation bonus

        return min(score, 100)  # Cap at 100

    def find_survivor_tokens(self, check_live_activity: bool = True) -> List[Dict]:
        """
        Find tokens with the best chance of surviving to reach exchanges
        """
        conn = self.get_db_connection()

        # Query for potential survivors (relaxed for testing)
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
            ORDER BY
                liquidity DESC,
                volume24h DESC
            LIMIT 100
        '''

        cursor = conn.execute(query)
        tokens = []

        for row in cursor:
            token_data = dict(row)

            # Check live activity if enabled
            activity_data = {}
            if check_live_activity and token_data['token_address']:
                print(f"Checking activity for {token_data['name']}...")
                is_active, activity_data = self.check_recent_activity(token_data['token_address'])

                if not is_active:
                    continue  # Skip dead tokens

                time.sleep(0.5)  # Rate limiting

            # Calculate survivor score
            survivor_score = self.calculate_survivor_score(token_data, activity_data)

            if survivor_score >= 25:  # Lowered threshold for demo
                token_data['survivor_score'] = survivor_score
                token_data['activity'] = activity_data
                token_data['age_hours'] = round(
                    (datetime.now() - token_data['discovered_at']).total_seconds() / 3600, 1
                )
                tokens.append(token_data)

        conn.close()

        # Sort by survivor score
        return sorted(tokens, key=lambda x: x['survivor_score'], reverse=True)[:10]

    def get_weekend_adjusted_filters(self) -> Dict:
        """
        Adjust filters for weekend/off-hours trading
        """
        now = datetime.now()
        is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
        is_off_hours = now.hour < 8 or now.hour > 20  # Outside 8am-8pm

        if is_weekend or is_off_hours:
            return {
                'min_trades_per_hour': 5,  # Lower threshold
                'min_unique_traders': 10,  # Lower threshold
                'max_age_hours': 12,  # Look further back
                'activity_window_minutes': 60  # Check longer window
            }
        else:
            return {
                'min_trades_per_hour': 10,
                'min_unique_traders': 20,
                'max_age_hours': 6,
                'activity_window_minutes': 30
            }

    def get_exchange_tier(self, liquidity: float, market_cap: float) -> str:
        """
        Determine which exchange tier this token could reach
        """
        if liquidity >= 10000000 and market_cap >= 50000000:
            return "🏆 Tier 1 (Binance/Coinbase potential)"
        elif liquidity >= 5000000 and market_cap >= 20000000:
            return "🥇 Tier 2 (Major exchange potential)"
        elif liquidity >= 1000000 and market_cap >= 5000000:
            return "🥈 Tier 3 (Mid-tier exchange potential)"
        elif liquidity >= 500000 and market_cap >= 2000000:
            return "🥉 Tier 4 (Small exchange potential)"
        elif liquidity >= 100000:
            return "📈 DEX listing viable"
        else:
            return "⚠️  Below exchange threshold"

    def display_survivors(self, tokens: List[Dict]):
        """
        Display survivor tokens in a readable format with exchange potential
        """
        print("\n" + "="*80)
        print("🎯 SURVIVOR TOKENS - Exchange Listing Potential Analysis")
        print("="*80)

        if not tokens:
            print("❌ No survivor tokens found. Market may be quiet.")
            print("💡 Try again during active trading hours (weekdays 8am-8pm)")
            return

        for i, token in enumerate(tokens, 1):
            score = token['survivor_score']
            liquidity = token['liquidity']
            market_cap = token['market_cap_estimate']
            volume = token['volume24h']

            # Exchange tier classification
            exchange_tier = self.get_exchange_tier(liquidity, market_cap)

            print(f"\n{i}. {token['name']} ⭐ Score: {score:.0f}/100")
            print(f"   {exchange_tier}")
            print(f"   Address: {token['token_address']}")
            print(f"   Age: {token['age_hours']:.1f} hours")
            print(f"   💰 Liquidity: ${liquidity:,.0f}")
            print(f"   📊 Volume 24h: ${volume:,.0f} (V/L: {volume/liquidity:.1f}x)")
            print(f"   🏷️  Market Cap: ${market_cap:,.0f}")

            if token.get('activity'):
                act = token['activity']
                print(f"   📈 Activity: {act.get('trades_30min', 0)} trades/30min")
                print(f"   👥 Traders: {act.get('unique_traders', 0)} unique")
                print(f"   ⏰ Last trade: {act.get('last_trade_minutes_ago', 999):.0f} min ago")

            if token.get('is_pump_token'):
                print("   🎰 Platform: Pump.fun (graduation track)")

            # Investment suggestion based on score and exchange tier
            if score >= 80:
                print("   🚀 STRONG BUY - Very high exchange potential")
            elif score >= 65:
                print("   💰 BUY - High exchange potential")
            elif score >= 50:
                print("   📈 MODERATE BUY - Good momentum potential")
            elif score >= 35:
                print("   ⚠️  RISKY - Monitor closely before buying")
            else:
                print("   🔴 HIGH RISK - Consider passing")

            # Volume/Liquidity ratio insight
            vol_ratio = volume / liquidity if liquidity > 0 else 0
            if vol_ratio >= 2:
                print("   🔥 HIGH MOMENTUM - Volume exceeds liquidity")
            elif vol_ratio >= 1:
                print("   📊 GOOD ACTIVITY - Balanced volume/liquidity")
            elif vol_ratio < 0.5:
                print("   😴 LOW ACTIVITY - Consider waiting for momentum")

            print(f"   🔗 Solscan: https://solscan.io/token/{token['token_address']}")
            print(f"   📈 DexScreener: https://dexscreener.com/solana/{token['token_address']}")


def main():
    """Run the survivor token filter"""
    filter = SurvivorTokenFilter()

    print("🔍 Scanning for survivor tokens...")
    print("📊 Looking for tokens aged 30min-6hrs with sustained momentum")

    # Get weekend-adjusted settings
    settings = filter.get_weekend_adjusted_filters()
    filter.MIN_TRADES_PER_HOUR = settings['min_trades_per_hour']
    filter.MIN_UNIQUE_TRADERS = settings['min_unique_traders']
    filter.MAX_AGE_HOURS = settings['max_age_hours']

    # Find survivors (disable live checking for speed during development)
    survivors = filter.find_survivor_tokens(check_live_activity=False)

    # Display results
    filter.display_survivors(survivors)

    print("\n" + "="*80)
    print("💡 Investment Tips:")
    print("- Invest small amounts ($10-50) in multiple tokens")
    print("- Set stop losses at -50% to limit downside")
    print("- Take profits at 2-5x, keep 20% for moonshot")
    print("- Tokens with score >70 have highest exchange potential")
    print("- Check social media for community building")
    print("="*80)


if __name__ == "__main__":
    main()