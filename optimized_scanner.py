#!/usr/bin/env python3
"""
Optimized Solana Token Security Scanner
Enhanced for speed, security, and efficiency
"""

import os
import sqlite3
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import json

from config import SecurityFilters, PerformanceConfig, RAYDIUM_API_ENDPOINTS, SOLANA_RPC_ENDPOINTS

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedTokenScanner:
    def __init__(self):
        self.database_file = 'raydium_pools.db'
        self.session = None
        self.performance_stats = {
            'pools_processed': 0,
            'new_tokens_found': 0,
            'safe_tokens_found': 0,
            'scan_time': 0
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; TokenScanner/1.0)'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def create_optimized_database(self):
        """Create database with optimized schema and indexes"""
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()

        # Enhanced table schema
        c.execute('''
            CREATE TABLE IF NOT EXISTS pools (
                lp_mint TEXT PRIMARY KEY,
                name TEXT,
                liquidity REAL,
                volume24h REAL,
                created_at TIMESTAMP,
                discovered_at TIMESTAMP,
                token_address TEXT,
                base_mint TEXT,
                quote_mint TEXT,
                is_pump_token INTEGER DEFAULT 0,
                is_safe INTEGER DEFAULT 0,
                safety_score INTEGER DEFAULT 0,
                holder_count INTEGER,
                top_holder_percent REAL,
                mint_authority_renounced INTEGER DEFAULT 0,
                freeze_authority_renounced INTEGER DEFAULT 0,
                contract_verified INTEGER DEFAULT 0,
                last_transaction_time TIMESTAMP,
                market_cap REAL,
                price_change_24h REAL
            )
        ''')

        # Create optimized indexes
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_discovered_at ON pools(discovered_at)',
            'CREATE INDEX IF NOT EXISTS idx_is_safe ON pools(is_safe)',
            'CREATE INDEX IF NOT EXISTS idx_liquidity ON pools(liquidity)',
            'CREATE INDEX IF NOT EXISTS idx_volume24h ON pools(volume24h)',
            'CREATE INDEX IF NOT EXISTS idx_token_address ON pools(token_address)',
            'CREATE INDEX IF NOT EXISTS idx_safety_score ON pools(safety_score)',
            'CREATE INDEX IF NOT EXISTS idx_composite_safe ON pools(is_safe, liquidity, volume24h)',
        ]

        for index in indexes:
            c.execute(index)

        conn.commit()
        conn.close()

    async def fetch_raydium_pools_optimized(self) -> List[Dict]:
        """Fetch pools with failover and retry logic"""
        for attempt, endpoint in enumerate(RAYDIUM_API_ENDPOINTS):
            try:
                logger.info(f"Fetching from endpoint {attempt + 1}: {endpoint}")
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched {len(data)} pools")
                        return data
                    else:
                        logger.warning(f"Endpoint returned status {response.status}")
            except Exception as e:
                logger.error(f"Failed to fetch from {endpoint}: {e}")
                if attempt < len(RAYDIUM_API_ENDPOINTS) - 1:
                    await asyncio.sleep(2)  # Wait before retry

        logger.error("All endpoints failed")
        return []

    async def analyze_token_security(self, token_address: str) -> Dict:
        """Enhanced security analysis for tokens"""
        security_data = {
            'mint_authority_renounced': False,
            'freeze_authority_renounced': False,
            'holder_count': 0,
            'top_holder_percent': 1.0,
            'contract_verified': False,
            'has_recent_activity': False,
            'safety_score': 0
        }

        try:
            # Check Solana token program data
            for rpc_endpoint in SOLANA_RPC_ENDPOINTS:
                try:
                    async with self.session.post(rpc_endpoint, json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getAccountInfo",
                        "params": [token_address, {"encoding": "base64"}]
                    }) as response:
                        if response.status == 200:
                            result = await response.json()
                            # Parse token authority data
                            # This would need specific implementation based on token program structure
                            break
                except Exception as e:
                    logger.debug(f"RPC check failed for {rpc_endpoint}: {e}")
                    continue

            # Calculate safety score
            score = 0
            if security_data['mint_authority_renounced']:
                score += 3
            if security_data['freeze_authority_renounced']:
                score += 3
            if security_data['holder_count'] > SecurityFilters.MIN_HOLDERS_COUNT:
                score += 2
            if security_data['top_holder_percent'] < SecurityFilters.MAX_HOLDER_CONCENTRATION:
                score += 2

            security_data['safety_score'] = min(score, 10)

        except Exception as e:
            logger.error(f"Security analysis failed for {token_address}: {e}")

        return security_data

    async def save_pool_optimized(self, pool: Dict, security_data: Dict = None):
        """Optimized pool saving with security data"""
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()

        token_address = pool['quoteMint'] if pool.get('baseMint') == "So11111111111111111111111111111111111111112" else pool.get('baseMint')
        current_time = datetime.now()

        # Check if pool exists
        c.execute('SELECT lp_mint FROM pools WHERE lp_mint = ?', (pool['lpMint'],))
        exists = c.fetchone()

        is_pump_token = token_address and token_address.lower().endswith('pump')
        is_safe = False
        safety_score = 0

        if security_data:
            safety_score = security_data.get('safety_score', 0)
            is_safe = (
                safety_score >= 6 and
                pool.get('liquidity', 0) >= SecurityFilters.MIN_LIQUIDITY_SAFE and
                pool.get('volume24h', 0) >= SecurityFilters.MIN_VOLUME_SAFE and
                not is_pump_token
            )

        if exists:
            # Update existing
            c.execute('''
                UPDATE pools SET
                    liquidity = ?, volume24h = ?, created_at = ?,
                    is_safe = ?, safety_score = ?,
                    holder_count = ?, top_holder_percent = ?,
                    mint_authority_renounced = ?, freeze_authority_renounced = ?
                WHERE lp_mint = ?
            ''', (
                pool.get('liquidity', 0),
                pool.get('volume24h', 0),
                current_time,
                1 if is_safe else 0,
                safety_score,
                security_data.get('holder_count', 0) if security_data else 0,
                security_data.get('top_holder_percent', 1.0) if security_data else 1.0,
                1 if security_data and security_data.get('mint_authority_renounced') else 0,
                1 if security_data and security_data.get('freeze_authority_renounced') else 0,
                pool['lpMint']
            ))
        else:
            # Insert new
            c.execute('''
                INSERT INTO pools (
                    lp_mint, name, liquidity, volume24h, created_at, discovered_at,
                    token_address, base_mint, quote_mint, is_pump_token, is_safe,
                    safety_score, holder_count, top_holder_percent,
                    mint_authority_renounced, freeze_authority_renounced
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pool['lpMint'],
                pool.get('name', 'Unknown'),
                pool.get('liquidity', 0),
                pool.get('volume24h', 0),
                current_time,
                current_time,
                token_address,
                pool.get('baseMint'),
                pool.get('quoteMint'),
                1 if is_pump_token else 0,
                1 if is_safe else 0,
                safety_score,
                security_data.get('holder_count', 0) if security_data else 0,
                security_data.get('top_holder_percent', 1.0) if security_data else 1.0,
                1 if security_data and security_data.get('mint_authority_renounced') else 0,
                1 if security_data and security_data.get('freeze_authority_renounced') else 0
            ))

            self.performance_stats['new_tokens_found'] += 1
            if is_safe:
                self.performance_stats['safe_tokens_found'] += 1

        conn.commit()
        conn.close()

    async def process_pools_batch(self, pools: List[Dict]):
        """Process pools in optimized batches"""
        batch_size = PerformanceConfig.BATCH_SIZE

        for i in range(0, len(pools), batch_size):
            batch = pools[i:i + batch_size]
            tasks = []

            for pool in batch:
                # Only analyze security for promising tokens
                if (pool.get('liquidity', 0) >= SecurityFilters.MIN_LIQUIDITY_DISCOVERY and
                    pool.get('volume24h', 0) >= SecurityFilters.MIN_VOLUME_DISCOVERY):

                    token_address = pool['quoteMint'] if pool.get('baseMint') == "So11111111111111111111111111111111111111112" else pool.get('baseMint')
                    if token_address:
                        task = self.analyze_and_save(pool, token_address)
                        tasks.append(task)
                else:
                    # Save without detailed analysis for low-value tokens
                    tasks.append(self.save_pool_optimized(pool))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def analyze_and_save(self, pool: Dict, token_address: str):
        """Analyze token security and save"""
        try:
            security_data = await self.analyze_token_security(token_address)
            await self.save_pool_optimized(pool, security_data)
        except Exception as e:
            logger.error(f"Failed to analyze {token_address}: {e}")
            await self.save_pool_optimized(pool)

    async def scan_tokens(self):
        """Main scanning loop with performance tracking"""
        start_time = time.time()

        try:
            # Fetch pools
            pools = await self.fetch_raydium_pools_optimized()
            if not pools:
                logger.warning("No pools fetched, skipping scan")
                return

            self.performance_stats['pools_processed'] = len(pools)

            # Process in batches
            await self.process_pools_batch(pools)

            scan_time = time.time() - start_time
            self.performance_stats['scan_time'] = scan_time

            logger.info(f"Scan complete: {len(pools)} pools processed in {scan_time:.2f}s")
            logger.info(f"New tokens: {self.performance_stats['new_tokens_found']}, "
                       f"Safe tokens: {self.performance_stats['safe_tokens_found']}")

        except Exception as e:
            logger.error(f"Scan failed: {e}")

    async def run_continuous(self):
        """Run continuous scanning with optimized intervals"""
        self.create_optimized_database()

        while True:
            try:
                await self.scan_tokens()

                # Dynamic interval based on discovery rate
                if self.performance_stats['new_tokens_found'] > 10:
                    interval = PerformanceConfig.FAST_SCAN_INTERVAL
                elif self.performance_stats['new_tokens_found'] > 5:
                    interval = PerformanceConfig.NORMAL_SCAN_INTERVAL
                else:
                    interval = PerformanceConfig.SLOW_SCAN_INTERVAL

                logger.info(f"Next scan in {interval} seconds")
                await asyncio.sleep(interval)

                # Reset stats for next round
                self.performance_stats = {
                    'pools_processed': 0,
                    'new_tokens_found': 0,
                    'safe_tokens_found': 0,
                    'scan_time': 0
                }

            except Exception as e:
                logger.error(f"Scanner error: {e}")
                await asyncio.sleep(60)  # Wait before retry

async def main():
    """Main entry point"""
    async with OptimizedTokenScanner() as scanner:
        await scanner.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())