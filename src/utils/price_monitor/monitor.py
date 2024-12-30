import asyncio
from typing import Dict, Set, Optional, Callable, List
import aiohttp
from datetime import datetime
import logging
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential

from ...db.services import TokenService
from ...db.base import db
from ..rate_limiter import RateLimiter
from .constants import *

logger = logging.getLogger(__name__)

class PriceMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.monitored_tokens: Set[str] = set()
        self.is_running = False
        
        # Initialize database service
        self.token_service = TokenService(db.session)
        
        # Enhanced settings
        self.update_interval = config.get('price_check_interval', DEFAULT_UPDATE_INTERVAL)
        self.jupiter_url = config.get('jupiter_url', DEFAULT_JUPITER_URL)
        self.usdc_mint = config.get('usdc_mint', DEFAULT_USDC_MINT)
        self.price_change_threshold = config.get('price_change_threshold', DEFAULT_PRICE_CHANGE_THRESHOLD)
        self.max_price_deviation = config.get('max_price_deviation', DEFAULT_MAX_PRICE_DEVIATION)
        self.min_price_value = config.get('min_price_value', DEFAULT_MIN_PRICE_VALUE)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            calls=config.get('rate_limit_calls', DEFAULT_RATE_LIMIT_CALLS),
            period=config.get('rate_limit_period', DEFAULT_RATE_LIMIT_PERIOD)
        )
        
        # HTTP session configuration
        self.timeout = ClientTimeout(total=config.get('request_timeout', DEFAULT_REQUEST_TIMEOUT))
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Price update callbacks
        self.price_update_callbacks: List[Callable] = []
        
    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=DEFAULT_RETRY_MIN_WAIT, max=DEFAULT_RETRY_MAX_WAIT)
    )
    async def _make_request(self, url: str, params: Dict) -> Dict:
        """Make HTTP request with retry logic and rate limiting"""
        await self.rate_limiter.acquire()
        
        async with self.session.get(url, params=params, timeout=self.timeout) as response:
            if response.status != 200:
                raise aiohttp.ClientError(f"Jupiter API error: {response.status}")
            return await response.json()

    async def _process_price_update(self, token_mint: str, price_data: Dict):
        """Process and store price updates"""
        try:
            current_price = float(price_data.get('price', 0))
            if current_price < self.min_price_value:
                logger.warning(f"Price below minimum threshold for {token_mint}: {current_price}")
                return
            
            # Get previous price for change calculation
            prev_price_data = await self.token_service.get_latest_price(token_mint)
            prev_price = prev_price_data.price if prev_price_data else None
            
            # Calculate price change
            price_change_24h = None
            if prev_price:
                price_change_24h = ((current_price - prev_price) / prev_price) * 100
                
                # Check for excessive deviation
                if abs(price_change_24h) > self.max_price_deviation:
                    logger.warning(f"Price deviation too high for {token_mint}: {price_change_24h}%")
                    return
            
            # Store price update
            await self.token_service.process_price_update(
                mint_address=token_mint,
                price=current_price,
                metadata=price_data.get('metadata', {}),
                price_change_24h=price_change_24h
            )
            
            # Notify callbacks
            for callback in self.price_update_callbacks:
                try:
                    await callback(token_mint, current_price, price_data)
                except Exception as e:
                    logger.error(f"Error in price update callback: {e}")

        except Exception as e:
            logger.error(f"Error processing price update for {token_mint}: {e}")

    async def start(self):
        """Start the price monitoring service"""
        if self.is_running:
            return

        logger.info("Starting price monitor service...")
        self.is_running = True
        self.session = aiohttp.ClientSession()
        
        try:
            while self.is_running:
                if self.monitored_tokens:
                    await self._check_prices()
                await asyncio.sleep(self.update_interval)
        except Exception as e:
            logger.error(f"Fatal error in price monitor loop: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the price monitoring service"""
        logger.info("Stopping price monitor service...")
        self.is_running = False
        if self.session:
            await self.session.close()
            self.session = None

    async def _check_prices(self):
        """Check prices for all monitored tokens"""
        if not self.monitored_tokens:
            return

        try:
            # Batch tokens into groups to avoid URL length limits
            token_batches = [list(self.monitored_tokens)[i:i + MAX_BATCH_SIZE] 
                           for i in range(0, len(self.monitored_tokens), MAX_BATCH_SIZE)]
            
            for token_batch in token_batches:
                params = {
                    "ids": ','.join(token_batch),
                    "vsToken": self.usdc_mint
                }

                data = await self._make_request(self.jupiter_url, params)
                
                for token_mint, price_data in data.get('data', {}).items():
                    await self._process_price_update(token_mint, price_data)

        except Exception as e:
            logger.error(f"Error checking prices: {e}")

    def add_price_update_callback(self, callback: Callable):
        """Register a new price update callback"""
        self.price_update_callbacks.append(callback)

    async def add_token(self, token_mint: str):
        """Add a token to monitor"""
        logger.info(f"Adding token to monitor: {token_mint}")
        self.monitored_tokens.add(token_mint)
        if self.session:
            await self._check_prices()

    async def remove_token(self, token_mint: str):
        """Remove a token from monitoring"""
        logger.info(f"Removing token from monitor: {token_mint}")
        self.monitored_tokens.discard(token_mint)

    async def get_monitored_prices(self) -> Dict[str, float]:
        """Get latest prices for all monitored tokens"""
        prices = {}
        for token_mint in self.monitored_tokens:
            price_data = await self.token_service.get_latest_price(token_mint)
            if price_data:
                prices[token_mint] = price_data.price
        return prices