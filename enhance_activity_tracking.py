#!/usr/bin/env python3
"""
Enhanced Activity Tracking for Tokens
Adds recent trading activity detection
"""

import sqlite3
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from config import SecurityFilters

DATABASE_FILE = 'raydium_pools.db'

def enhance_database_schema():
    """Add columns for tracking trading activity"""
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    # Add new columns for activity tracking
    new_columns = [
        ('last_trade_time', 'TIMESTAMP'),
        ('trades_last_hour', 'INTEGER DEFAULT 0'),
        ('volume_last_hour', 'REAL DEFAULT 0'),
        ('price_change_1h', 'REAL DEFAULT 0'),
        ('is_active', 'INTEGER DEFAULT 0'),
        ('activity_score', 'INTEGER DEFAULT 0'),
        ('momentum_indicator', 'TEXT DEFAULT "unknown"')
    ]

    # Check existing columns
    c.execute("PRAGMA table_info(pools)")
    existing_columns = [col[1] for col in c.fetchall()]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            c.execute(f"ALTER TABLE pools ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name}")

    # Create indexes for activity queries
    activity_indexes = [
        'CREATE INDEX IF NOT EXISTS idx_last_trade_time ON pools(last_trade_time)',
        'CREATE INDEX IF NOT EXISTS idx_is_active ON pools(is_active)',
        'CREATE INDEX IF NOT EXISTS idx_activity_score ON pools(activity_score)',
        'CREATE INDEX IF NOT EXISTS idx_momentum ON pools(momentum_indicator)'
    ]

    for index in activity_indexes:
        c.execute(index)

    conn.commit()
    conn.close()
    print("Database schema enhanced for activity tracking!")

async def check_token_activity(session: aiohttp.ClientSession, token_address: str) -> Dict:
    """Check recent trading activity for a token"""
    activity_data = {
        'last_trade_time': None,
        'trades_last_hour': 0,
        'volume_last_hour': 0.0,
        'price_change_1h': 0.0,
        'is_active': False,
        'activity_score': 0,
        'momentum_indicator': 'unknown'
    }

    try:
        # Check DexScreener for recent activity
        dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"

        async with session.get(dex_url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()

                if data.get('pairs'):
                    pair = data['pairs'][0]  # Get the main pair

                    # Extract activity metrics
                    volume_1h = float(pair.get('volume', {}).get('h1', 0))
                    price_change_1h = float(pair.get('priceChange', {}).get('h1', 0))

                    # Calculate activity score based on multiple factors
                    score = 0

                    # Volume activity (0-4 points)
                    if volume_1h > 10000:
                        score += 4
                    elif volume_1h > 5000:
                        score += 3
                    elif volume_1h > 1000:
                        score += 2
                    elif volume_1h > 100:
                        score += 1

                    # Price movement indicates activity (0-3 points)
                    abs_change = abs(price_change_1h)
                    if abs_change > 20:
                        score += 3
                    elif abs_change > 10:
                        score += 2
                    elif abs_change > 5:
                        score += 1

                    # Check if trades are recent (0-3 points)
                    current_time = datetime.now()
                    if volume_1h > 0:  # Any recent volume indicates trades
                        score += 3
                        activity_data['last_trade_time'] = current_time
                        activity_data['is_active'] = True

                    # Momentum indicator
                    if score >= 8:
                        momentum = "hot"
                    elif score >= 5:
                        momentum = "active"
                    elif score >= 2:
                        momentum = "moderate"
                    else:
                        momentum = "low"

                    activity_data.update({
                        'volume_last_hour': volume_1h,
                        'price_change_1h': price_change_1h,
                        'activity_score': score,
                        'momentum_indicator': momentum,
                        'is_active': score >= 3  # Active if score 3+
                    })

        # Additional check via Solscan for transaction count
        solscan_url = f"https://public-api.solscan.io/account/transactions?account={token_address}&limit=50"

        async with session.get(solscan_url, timeout=10) as response:
            if response.status == 200:
                transactions = await response.json()

                if transactions:
                    # Count recent transactions
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    recent_txs = 0

                    for tx in transactions[:20]:  # Check last 20 transactions
                        tx_time = datetime.fromtimestamp(tx.get('blockTime', 0))
                        if tx_time > one_hour_ago:
                            recent_txs += 1

                    activity_data['trades_last_hour'] = recent_txs

                    # Boost activity score based on transaction frequency
                    if recent_txs >= 10:
                        activity_data['activity_score'] += 2
                    elif recent_txs >= 5:
                        activity_data['activity_score'] += 1

    except Exception as e:
        logging.debug(f"Activity check failed for {token_address}: {e}")

    return activity_data

async def update_token_activity(token_address: str, lp_mint: str):
    """Update activity data for a single token"""
    async with aiohttp.ClientSession() as session:
        activity_data = await check_token_activity(session, token_address)

        # Update database
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()

        c.execute('''
            UPDATE pools SET
                last_trade_time = ?,
                trades_last_hour = ?,
                volume_last_hour = ?,
                price_change_1h = ?,
                is_active = ?,
                activity_score = ?,
                momentum_indicator = ?
            WHERE lp_mint = ?
        ''', (
            activity_data['last_trade_time'],
            activity_data['trades_last_hour'],
            activity_data['volume_last_hour'],
            activity_data['price_change_1h'],
            1 if activity_data['is_active'] else 0,
            activity_data['activity_score'],
            activity_data['momentum_indicator'],
            lp_mint
        ))

        conn.commit()
        conn.close()

        return activity_data

async def scan_recent_tokens_for_activity():
    """Scan recent tokens and update their activity status"""
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    # Get recent tokens that need activity checking
    two_hours_ago = datetime.now() - timedelta(hours=2)
    c.execute('''
        SELECT lp_mint, token_address, name
        FROM pools
        WHERE discovered_at > ?
        AND token_address IS NOT NULL
        AND liquidity > 1000
        ORDER BY discovered_at DESC
        LIMIT 50
    ''', (two_hours_ago,))

    tokens = c.fetchall()
    conn.close()

    print(f"Checking activity for {len(tokens)} recent tokens...")

    active_tokens = []

    async with aiohttp.ClientSession() as session:
        for lp_mint, token_address, name in tokens:
            try:
                activity_data = await check_token_activity(session, token_address)

                # Update database
                conn = sqlite3.connect(DATABASE_FILE)
                c = conn.cursor()

                c.execute('''
                    UPDATE pools SET
                        last_trade_time = ?,
                        trades_last_hour = ?,
                        volume_last_hour = ?,
                        price_change_1h = ?,
                        is_active = ?,
                        activity_score = ?,
                        momentum_indicator = ?
                    WHERE lp_mint = ?
                ''', (
                    activity_data['last_trade_time'],
                    activity_data['trades_last_hour'],
                    activity_data['volume_last_hour'],
                    activity_data['price_change_1h'],
                    1 if activity_data['is_active'] else 0,
                    activity_data['activity_score'],
                    activity_data['momentum_indicator'],
                    lp_mint
                ))

                conn.commit()
                conn.close()

                if activity_data['is_active']:
                    active_tokens.append({
                        'name': name,
                        'token_address': token_address,
                        'activity_score': activity_data['activity_score'],
                        'momentum': activity_data['momentum_indicator'],
                        'volume_1h': activity_data['volume_last_hour'],
                        'trades_1h': activity_data['trades_last_hour']
                    })

                # Rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logging.error(f"Failed to check activity for {name}: {e}")

    # Report findings
    print(f"\n🔥 Found {len(active_tokens)} ACTIVE tokens:")
    for token in sorted(active_tokens, key=lambda x: x['activity_score'], reverse=True):
        print(f"  {token['name']} - Score: {token['activity_score']} - "
              f"Momentum: {token['momentum']} - Volume 1h: ${token['volume_1h']:,.0f}")

    return active_tokens

if __name__ == "__main__":
    print("Enhancing database for activity tracking...")
    enhance_database_schema()

    print("Scanning recent tokens for trading activity...")
    asyncio.run(scan_recent_tokens_for_activity())