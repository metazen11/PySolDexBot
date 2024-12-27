import asyncio
from typing import Dict, Set, Optional, Callable, List
import aiohttp
from datetime import datetime
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class PriceMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.monitored_tokens: Set[str] = set()
        self.last_prices: Dict[str, float] = {}
        self.is_running = False
        
        # Settings
        self.update_interval = config.get('price_check_interval', 60)
        self.jupiter_url = config.get('jupiter_url', 'https://price.jup.ag/v4/price')
        self.usdc_mint = config.get('usdc_mint', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
        self.price_change_threshold = config.get('price_change_threshold', 1.0)
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Callbacks
        self.price_update_callbacks: List[Callable] = []
        self.price_alert_callbacks: List[Callable] = []
        
        # Statistics
        self.request_count = 0
        self.error_count = 0
        self.last_request_time: Optional[datetime] = None

    async def start(self):
        if self.is_running:
            return

        logger.info("Starting price monitor service...")
        self.is_running = True
        self.session = aiohttp.ClientSession()
        
        try:
            while self.is_running:
                await self._check_prices()
                await asyncio.sleep(self.update_interval)
        except Exception as e:
            logger.error(f"Error in price monitor loop: {e}")
            await self.stop()

    async def stop(self):
        logger.info("Stopping price monitor service...")
        self.is_running = False
        if self.session:
            await self.session.close()
            self.session = None

    async def add_token(self, token_mint: str):
        logger.info(f"Adding token to monitor: {token_mint}")
        self.monitored_tokens.add(token_mint)
        if self.session:
            await self._check_single_token(token_mint)

    async def remove_token(self, token_mint: str):
        logger.info(f"Removing token from monitor: {token_mint}")
        self.monitored_tokens.discard(token_mint)
        self.last_prices.pop(token_mint, None)

    async def _check_prices(self):
        if not self.monitored_tokens:
            return

        try:
            self.request_count += 1
            self.last_request_time = datetime.now()
            
            # Batch tokens into groups of 100 to avoid URL length limits
            token_batches = [list(self.monitored_tokens)[i:i + 100] 
                           for i in range(0, len(self.monitored_tokens), 100)]
            
            for token_batch in token_batches:
                params = {
                    "ids": ','.join(token_batch),
                    "vsToken": self.usdc_mint
                }

                async with self.session.get(self.jupiter_url, params=params) as response:
                    if response.status != 200:
                        self.error_count += 1
                        logger.error(f"Jupiter API error: {response.status}")
                        continue

                    data = await response.json()
                    
                    for token_mint, price_data in data.get('data', {}).items():
                        await self._process_price_update(token_mint, price_data)

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error checking prices: {e}")

    async def _check_single_token(self, token_mint: str):
        """Check price for a single token"""
        try:
            params = {
                "ids": token_mint,
                "vsToken": self.usdc_mint
            }

            async with self.session.get(self.jupiter_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Jupiter API error for {token_mint}: {response.status}")
                    return

                data = await response.json()
                price_data = data.get('data', {}).get(token_mint)
                
                if price_data:
                    await self._process_price_update(token_mint, price_data)

        except Exception as e:
            logger.error(f"Error checking single token {token_mint}: {e}")

    async def _process_price_update(self, token_mint: str, price_data: Dict):
        try:
            current_price = float(price_data['price'])
            
            # Calculate price change if we have previous price
            if token_mint in self.last_prices:
                last_price = self.last_prices[token_mint]
                price_change = ((current_price - last_price) / last_price) * 100
                
                if abs(price_change) >= self.price_change_threshold:
                    await self._notify_price_alert(token_mint, current_price, price_change)

            # Update last price and notify
            self.last_prices[token_mint] = current_price
            await self._notify_price_update(token_mint, current_price, price_data)

        except Exception as e:
            logger.error(f"Error processing price update for {token_mint}: {e}")

    async def _notify_price_update(self, token_mint: str, price: float, price_data: Dict):
        for callback in self.price_update_callbacks:
            try:
                await callback(token_mint, price, price_data)
            except Exception as e:
                logger.error(f"Error in price update callback: {e}")

    async def _notify_price_alert(self, token_mint: str, price: float, price_change: float):
        for callback in self.price_alert_callbacks:
            try:
                await callback(token_mint, price, price_change)
            except Exception as e:
                logger.error(f"Error in price alert callback: {e}")

    def add_price_update_callback(self, callback: Callable):
        self.price_update_callbacks.append(callback)

    def add_price_alert_callback(self, callback: Callable):
        self.price_alert_callbacks.append(callback)

    def get_stats(self) -> Dict:
        return {
            'monitored_tokens': len(self.monitored_tokens),
            'request_count': self.request_count,
            'error_count': self.error_count,
            'last_request_time': self.last_request_time,
            'is_running': self.is_running
        }