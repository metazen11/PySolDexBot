#!/usr/bin/env python3
"""
Test script to populate some holder data
"""

import sqlite3
import asyncio
from holder_analytics import HolderAnalytics

async def populate_holder_data():
    """Populate holder data for some real tokens in the database"""
    analytics = HolderAnalytics()

    # Get some real tokens from the database
    conn = sqlite3.connect('raydium_pools.db')
    cursor = conn.execute('''
        SELECT token_address, name
        FROM pools
        WHERE volume24h > 50000
        AND liquidity > 100000
        ORDER BY volume24h DESC
        LIMIT 10
    ''')

    tokens = cursor.fetchall()
    conn.close()

    print(f"Found {len(tokens)} tokens to update with holder data")

    for token_address, name in tokens:
        print(f"Updating holder data for {name} ({token_address[:8]}...)")

        try:
            result = await analytics.update_holder_analytics(token_address)
            print(f"  ✅ Updated: {result}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    await analytics.close_session()

    # Check results
    conn = sqlite3.connect('raydium_pools.db')
    cursor = conn.execute('''
        SELECT COUNT(*) FROM pools WHERE current_holder_count IS NOT NULL
    ''')
    count = cursor.fetchone()[0]
    conn.close()

    print(f"\n🎉 Total tokens with holder data: {count}")

if __name__ == "__main__":
    asyncio.run(populate_holder_data())