#!/usr/bin/env python3
"""
Holder Analytics Module
Tracks holder growth, concentration, and trading patterns for token analysis
"""

import asyncio
import aiohttp
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)

class HolderAnalytics:
    def __init__(self, database_file='raydium_pools.db'):
        self.database_file = database_file
        self.session = None

        # API endpoints for holder data
        self.solscan_api = "https://public-api.solscan.io"
        self.helius_api = "https://api.helius.xyz/v0"  # Alternative source

    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_holder_data(self, token_address: str) -> Dict:
        """Get comprehensive holder data for a token"""
        try:
            session = await self.get_session()

            # Try DexScreener first (more reliable for holder counts)
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"

            async with session.get(dex_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.process_dexscreener_data(data, token_address)

            # Fallback: estimate from transaction patterns
            return await self.estimate_holder_data(token_address)

        except Exception as e:
            logger.error(f"Error getting holder data for {token_address}: {e}")
            return await self.estimate_holder_data(token_address)

    async def process_dexscreener_data(self, dex_data: Dict, token_address: str) -> Dict:
        """Process DexScreener data for holder analytics"""
        try:
            pairs = dex_data.get('pairs', [])
            if not pairs:
                return {}

            # Use the first/best pair
            pair = pairs[0]

            # Extract available data
            txns = pair.get('txns', {})
            buys_5m = txns.get('m5', {}).get('buys', 0)
            sells_5m = txns.get('m5', {}).get('sells', 0)
            buys_1h = txns.get('h1', {}).get('buys', 0)
            sells_1h = txns.get('h1', {}).get('sells', 0)

            # Estimate unique traders from transaction patterns
            estimated_traders_5m = min(buys_5m + sells_5m, max(buys_5m, sells_5m) * 1.5)
            estimated_traders_1h = min(buys_1h + sells_1h, max(buys_1h, sells_1h) * 1.5)

            # Estimate holder count based on activity (conservative estimate)
            estimated_holders = max(estimated_traders_1h * 10, 100)  # Assume active traders are 10% of holders

            return {
                'holder_count': int(estimated_holders),
                'unique_traders_5m': int(estimated_traders_5m),
                'unique_traders_1h': int(estimated_traders_1h),
                'new_holders_5m': max(0, buys_5m - sells_5m),  # Net new buyers
                'holder_concentration_top10': 30.0,  # Default estimate
            }

        except Exception as e:
            logger.error(f"Error processing DexScreener data: {e}")
            return {}

    async def estimate_holder_data(self, token_address: str) -> Dict:
        """Estimate holder data when APIs are unavailable"""
        try:
            # Get historical volume data to estimate holder activity
            conn = sqlite3.connect(self.database_file)
            cursor = conn.execute('''
                SELECT AVG(volume_24h), AVG(buys_5m), AVG(sells_5m)
                FROM price_history
                WHERE token_address = ? AND timestamp > datetime('now', '-24 hours')
            ''', (token_address,))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                avg_volume = result[0] or 0
                avg_buys = result[1] or 0
                avg_sells = result[2] or 0

                # Estimate holders based on volume patterns
                # Higher volume typically means more holders
                estimated_holders = max(int(avg_volume / 1000), 50)  # Very rough estimate
                estimated_traders = max(int((avg_buys + avg_sells) * 2), 5)

                return {
                    'holder_count': estimated_holders,
                    'unique_traders_5m': estimated_traders,
                    'unique_traders_1h': estimated_traders * 3,
                    'new_holders_5m': max(0, int(avg_buys - avg_sells)),
                    'holder_concentration_top10': 25.0,  # Conservative estimate
                }

            return {
                'holder_count': 100,  # Default minimum
                'unique_traders_5m': 5,
                'unique_traders_1h': 15,
                'new_holders_5m': 2,
                'holder_concentration_top10': 30.0,
            }

        except Exception as e:
            logger.error(f"Error estimating holder data: {e}")
            return {}

    async def process_holder_data(self, raw_data: Dict, token_address: str) -> Dict:
        """Process raw holder data into analytics"""
        try:
            total_holders = raw_data.get('total', 0)
            holders = raw_data.get('data', [])

            if not holders:
                return {'holder_count': total_holders}

            # Calculate holder concentration
            total_supply = sum(float(holder.get('amount', 0)) for holder in holders)

            # Top 10 concentration
            top_10_amount = sum(float(holder.get('amount', 0)) for holder in holders[:10])
            top_10_concentration = (top_10_amount / total_supply * 100) if total_supply > 0 else 0

            # Analyze holder distribution
            whale_holders = sum(1 for holder in holders if float(holder.get('amount', 0)) / total_supply > 0.01)  # >1% holders

            return {
                'holder_count': total_holders,
                'holder_concentration_top10': top_10_concentration,
                'whale_count': whale_holders,
                'largest_holder_percent': (float(holders[0].get('amount', 0)) / total_supply * 100) if holders and total_supply > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error processing holder data: {e}")
            return {}

    async def get_recent_trading_activity(self, token_address: str) -> Dict:
        """Get recent trading activity to identify new vs existing holders"""
        try:
            session = await self.get_session()

            # Get recent transactions
            tx_url = f"{self.solscan_api}/account/transactions"
            params = {
                'account': token_address,
                'limit': 100  # Recent transactions
            }

            async with session.get(tx_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.analyze_trading_patterns(data)
                else:
                    return {}

        except Exception as e:
            logger.error(f"Error getting trading activity for {token_address}: {e}")
            return {}

    def analyze_trading_patterns(self, tx_data: Dict) -> Dict:
        """Analyze trading patterns from transaction data"""
        try:
            transactions = tx_data.get('data', [])

            # Count unique traders in different timeframes
            now = datetime.now()
            traders_5m = set()
            traders_1h = set()
            new_buyers = set()

            for tx in transactions:
                tx_time = datetime.fromtimestamp(tx.get('blockTime', 0))
                trader = tx.get('src')  # Transaction initiator

                if trader:
                    # 5-minute window
                    if now - tx_time <= timedelta(minutes=5):
                        traders_5m.add(trader)

                    # 1-hour window
                    if now - tx_time <= timedelta(hours=1):
                        traders_1h.add(trader)

                    # Identify potential new buyers (first-time interactions)
                    if self.is_likely_new_buyer(tx):
                        new_buyers.add(trader)

            return {
                'unique_traders_5m': len(traders_5m),
                'unique_traders_1h': len(traders_1h),
                'new_holders_5m': len(new_buyers)
            }

        except Exception as e:
            logger.error(f"Error analyzing trading patterns: {e}")
            return {}

    def is_likely_new_buyer(self, transaction: Dict) -> bool:
        """Heuristic to identify if this is likely a new buyer"""
        # Simple heuristic: small transaction amount might indicate new buyer
        # This could be enhanced with more sophisticated analysis
        try:
            amount = float(transaction.get('amount', 0))
            return 0 < amount < 100  # Small amounts might be new buyers testing
        except:
            return False

    def calculate_holder_growth(self, token_address: str) -> Dict:
        """Calculate holder growth trends from historical data"""
        conn = sqlite3.connect(self.database_file)
        try:
            # Get holder count over time
            cursor = conn.execute('''
                SELECT holder_count, timestamp
                FROM price_history
                WHERE token_address = ? AND holder_count IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 168  -- 7 days of hourly data
            ''', (token_address,))

            historical_data = cursor.fetchall()

            if len(historical_data) < 2:
                return {}

            current_holders = historical_data[0][0]

            # Calculate growth over different periods
            growth_24h = self.calculate_growth_rate(historical_data, hours=24)
            growth_7d = self.calculate_growth_rate(historical_data, hours=168)

            # Determine trend
            trend = self.determine_holder_trend(historical_data)

            return {
                'current_holder_count': current_holders,
                'holder_growth_24h': growth_24h,
                'avg_holder_growth_7d': growth_7d,
                'holder_trend': trend
            }

        except Exception as e:
            logger.error(f"Error calculating holder growth: {e}")
            return {}
        finally:
            conn.close()

    def calculate_growth_rate(self, historical_data: List, hours: int) -> float:
        """Calculate holder growth rate over specified hours"""
        try:
            if len(historical_data) < hours:
                return 0.0

            current = historical_data[0][0]
            past = historical_data[min(hours-1, len(historical_data)-1)][0]

            if past > 0:
                return ((current - past) / past) * 100
            return 0.0

        except Exception:
            return 0.0

    def determine_holder_trend(self, historical_data: List) -> str:
        """Determine overall holder trend from recent data"""
        try:
            if len(historical_data) < 24:  # Need at least 24 hours of data
                return 'insufficient_data'

            recent_24h = [row[0] for row in historical_data[:24] if row[0] is not None]

            if len(recent_24h) < 12:
                return 'insufficient_data'

            # Calculate trend: compare first half vs second half of recent data
            first_half_avg = sum(recent_24h[:12]) / 12
            second_half_avg = sum(recent_24h[12:]) / len(recent_24h[12:])

            growth_rate = ((first_half_avg - second_half_avg) / second_half_avg) * 100 if second_half_avg > 0 else 0

            if growth_rate > 5:
                return 'growing'
            elif growth_rate < -5:
                return 'declining'
            else:
                return 'stable'

        except Exception:
            return 'unknown'

    async def update_holder_analytics(self, token_address: str) -> Dict:
        """Update holder analytics for a token"""
        try:
            # Get current holder data
            holder_data = await self.get_holder_data(token_address)

            # Get trading activity data
            trading_data = await self.get_recent_trading_activity(token_address)

            # Calculate growth trends
            growth_data = self.calculate_holder_growth(token_address)

            # Combine all data
            analytics = {
                **holder_data,
                **trading_data,
                **growth_data,
                'timestamp': datetime.now()
            }

            # Store in price_history table
            await self.store_holder_analytics(token_address, analytics)

            # Update computed fields in pools table
            await self.update_pools_holder_summary(token_address, analytics)

            return analytics

        except Exception as e:
            logger.error(f"Error updating holder analytics for {token_address}: {e}")
            return {}

    async def store_holder_analytics(self, token_address: str, analytics: Dict):
        """Store holder analytics in price_history table"""
        conn = sqlite3.connect(self.database_file)
        try:
            conn.execute('''
                UPDATE price_history
                SET holder_count = ?,
                    unique_traders_5m = ?,
                    unique_traders_1h = ?,
                    new_holders_5m = ?,
                    holder_concentration_top10 = ?
                WHERE token_address = ? AND timestamp = (
                    SELECT MAX(timestamp) FROM price_history WHERE token_address = ?
                )
            ''', (
                analytics.get('holder_count'),
                analytics.get('unique_traders_5m'),
                analytics.get('unique_traders_1h'),
                analytics.get('new_holders_5m'),
                analytics.get('holder_concentration_top10'),
                token_address,
                token_address
            ))

            conn.commit()

        except Exception as e:
            logger.error(f"Error storing holder analytics: {e}")
        finally:
            conn.close()

    async def update_pools_holder_summary(self, token_address: str, analytics: Dict):
        """Update summary holder fields in pools table"""
        conn = sqlite3.connect(self.database_file)
        try:
            conn.execute('''
                UPDATE pools
                SET current_holder_count = ?,
                    holder_growth_24h = ?,
                    holder_trend = ?,
                    avg_holder_growth_7d = ?
                WHERE token_address = ?
            ''', (
                analytics.get('current_holder_count'),
                analytics.get('holder_growth_24h'),
                analytics.get('holder_trend'),
                analytics.get('avg_holder_growth_7d'),
                token_address
            ))

            conn.commit()

        except Exception as e:
            logger.error(f"Error updating pools holder summary: {e}")
        finally:
            conn.close()

# Example usage
async def main():
    analytics = HolderAnalytics()

    # Test with a known token
    test_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC

    result = await analytics.update_holder_analytics(test_token)
    print(f"Holder analytics: {result}")

    await analytics.close_session()

if __name__ == "__main__":
    asyncio.run(main())