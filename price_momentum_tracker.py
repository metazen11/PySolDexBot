#!/usr/bin/env python3
"""
Price Momentum Tracker - Continuously monitors and stores price data for momentum analysis
Runs alongside the main scanner to build historical price database
"""

import sqlite3
import requests
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PriceMomentumTracker:
    def __init__(self, db_path='raydium_pools.db'):
        self.db_path = db_path
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex/tokens"
        self.request_count = 0
        self.last_reset = datetime.now()
        self.setup_price_history_table()

    def setup_price_history_table(self):
        """Create price history table for momentum tracking"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    price_usd REAL,
                    liquidity_usd REAL,
                    volume_5m REAL,
                    volume_1h REAL,
                    volume_24h REAL,
                    buys_5m INTEGER,
                    sells_5m INTEGER,
                    price_change_5m REAL,
                    price_change_1h REAL,
                    price_change_24h REAL,
                    market_cap REAL,
                    FOREIGN KEY (token_address) REFERENCES pools (token_address)
                )
            ''')

            # Create indexes for efficient querying
            conn.execute('CREATE INDEX IF NOT EXISTS idx_token_timestamp ON price_history (token_address, timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON price_history (timestamp)')

            conn.commit()
            logger.info("Price history table setup complete")
        except Exception as e:
            logger.error(f"Error setting up price history table: {e}")
        finally:
            conn.close()

    def respect_rate_limits(self):
        """DexScreener: 300 requests per minute"""
        now = datetime.now()
        if (now - self.last_reset).total_seconds() >= 60:
            self.request_count = 0
            self.last_reset = now

        if self.request_count >= 290:  # Leave buffer
            wait_time = 60 - (now - self.last_reset).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                self.request_count = 0
                self.last_reset = datetime.now()

    def get_dexscreener_data(self, token_address):
        """Get comprehensive price data from DexScreener"""
        self.respect_rate_limits()

        try:
            url = f"{self.dexscreener_base}/{token_address}"
            response = requests.get(url, timeout=10)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    # Get the highest liquidity pair for most accurate data
                    best_pair = max(data['pairs'], key=lambda x: x.get('liquidity', {}).get('usd', 0))

                    return {
                        'price_usd': best_pair.get('priceUsd'),
                        'liquidity_usd': best_pair.get('liquidity', {}).get('usd'),
                        'volume_5m': best_pair.get('volume', {}).get('m5'),
                        'volume_1h': best_pair.get('volume', {}).get('h1'),
                        'volume_24h': best_pair.get('volume', {}).get('h24'),
                        'buys_5m': best_pair.get('txns', {}).get('m5', {}).get('buys', 0),
                        'sells_5m': best_pair.get('txns', {}).get('m5', {}).get('sells', 0),
                        'price_change_5m': best_pair.get('priceChange', {}).get('m5'),
                        'price_change_1h': best_pair.get('priceChange', {}).get('h1'),
                        'price_change_24h': best_pair.get('priceChange', {}).get('h24'),
                        'market_cap': best_pair.get('marketCap')
                    }
            return None
        except Exception as e:
            logger.warning(f"Error fetching DexScreener data for {token_address}: {e}")
            return None

    def store_price_data(self, token_address, price_data):
        """Store price data in the database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('''
                INSERT INTO price_history (
                    token_address, price_usd, liquidity_usd, volume_5m, volume_1h, volume_24h,
                    buys_5m, sells_5m, price_change_5m, price_change_1h, price_change_24h, market_cap
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token_address,
                price_data.get('price_usd'),
                price_data.get('liquidity_usd'),
                price_data.get('volume_5m'),
                price_data.get('volume_1h'),
                price_data.get('volume_24h'),
                price_data.get('buys_5m'),
                price_data.get('sells_5m'),
                price_data.get('price_change_5m'),
                price_data.get('price_change_1h'),
                price_data.get('price_change_24h'),
                price_data.get('market_cap')
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error storing price data for {token_address}: {e}")
        finally:
            conn.close()

    def get_active_tokens(self, hours_back=24, min_volume=100):
        """Get tokens that should be tracked (active within timeframe)"""
        conn = sqlite3.connect(self.db_path)
        try:
            cutoff = datetime.now() - timedelta(hours=hours_back)
            cursor = conn.execute('''
                SELECT DISTINCT token_address
                FROM pools
                WHERE discovered_at > ?
                AND volume24h > ?
                AND token_address IS NOT NULL
                ORDER BY volume24h DESC
                LIMIT 200
            ''', (cutoff, min_volume))

            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting active tokens: {e}")
            return []
        finally:
            conn.close()

    def calculate_momentum_score(self, token_address):
        """Calculate momentum score based on recent price history"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Get last 6 price points (30 minutes of data at 5-minute intervals)
            cursor = conn.execute('''
                SELECT price_usd, timestamp, volume_5m, buys_5m, sells_5m
                FROM price_history
                WHERE token_address = ?
                ORDER BY timestamp DESC
                LIMIT 6
            ''', (token_address,))

            history = cursor.fetchall()
            if len(history) < 3:
                return 0

            momentum_score = 0

            # Price trend (40% of score)
            prices = [row[0] for row in history if row[0] is not None]
            if len(prices) >= 3:
                recent_trend = (prices[0] - prices[2]) / prices[2] if prices[2] > 0 else 0
                momentum_score += min(recent_trend * 40, 40)

            # Volume trend (30% of score)
            volumes = [row[2] for row in history if row[2] is not None]
            if len(volumes) >= 2:
                volume_trend = (volumes[0] - volumes[1]) / volumes[1] if volumes[1] > 0 else 0
                momentum_score += min(volume_trend * 30, 30)

            # Buy/sell pressure (30% of score)
            latest = history[0]
            if latest[3] is not None and latest[4] is not None:
                total_trades = latest[3] + latest[4]
                if total_trades > 0:
                    buy_ratio = latest[3] / total_trades
                    pressure_score = (buy_ratio - 0.5) * 60  # Range: -30 to +30
                    momentum_score += pressure_score

            return max(-100, min(100, momentum_score))

        except Exception as e:
            logger.error(f"Error calculating momentum for {token_address}: {e}")
            return 0
        finally:
            conn.close()

    def run_price_tracking_cycle(self):
        """Single cycle of price tracking for all active tokens"""
        active_tokens = self.get_active_tokens()
        logger.info(f"Tracking {len(active_tokens)} active tokens")

        successful_updates = 0

        # Use ThreadPoolExecutor for parallel requests (respect rate limits)
        with ThreadPoolExecutor(max_workers=3) as executor:
            for token_address in active_tokens:
                try:
                    price_data = self.get_dexscreener_data(token_address)
                    if price_data:
                        self.store_price_data(token_address, price_data)
                        successful_updates += 1

                        # Calculate and log momentum for interesting tokens
                        momentum = self.calculate_momentum_score(token_address)
                        if abs(momentum) > 20:
                            logger.info(f"High momentum detected - {token_address}: {momentum:.1f}")

                    time.sleep(0.2)  # Respect rate limits

                except Exception as e:
                    logger.warning(f"Error processing {token_address}: {e}")

        logger.info(f"Price tracking cycle complete: {successful_updates}/{len(active_tokens)} tokens updated")

    def cleanup_old_data(self, days_to_keep=7):
        """Clean up old price history data"""
        conn = sqlite3.connect(self.db_path)
        try:
            cutoff = datetime.now() - timedelta(days=days_to_keep)
            cursor = conn.execute('DELETE FROM price_history WHERE timestamp < ?', (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted} old price history records")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
        finally:
            conn.close()

    def run_continuous(self, interval_minutes=5):
        """Run continuous price momentum tracking"""
        logger.info(f"Starting continuous price momentum tracking (every {interval_minutes} minutes)")

        while True:
            try:
                start_time = datetime.now()
                self.run_price_tracking_cycle()

                # Cleanup old data every hour
                if datetime.now().minute < 5:
                    self.cleanup_old_data()

                # Wait for next cycle
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, (interval_minutes * 60) - elapsed)

                if sleep_time > 0:
                    logger.info(f"Waiting {sleep_time/60:.1f} minutes until next cycle...")
                    time.sleep(sleep_time)

            except KeyboardInterrupt:
                logger.info("Price momentum tracking stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in tracking cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    tracker = PriceMomentumTracker()
    tracker.run_continuous()