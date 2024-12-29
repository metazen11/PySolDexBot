import asyncio
from typing import Dict, Set, Optional, Callable, List
import aiohttp
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import time
from dataclasses import dataclass
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@dataclass
class PriceUpdate:
    token_mint: str
    price: float
    timestamp: datetime
    raw_data: Dict
    is_valid: bool = True
    validation_errors: List[str] = None

class RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.timestamps = []

    async def acquire(self):
        now = time.time()
        self.timestamps = [ts for ts in self.timestamps if now - ts <= self.period]
        
        if len(self.timestamps) >= self.calls:
            wait_time = self.timestamps[0] + self.period - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                return await self.acquire()
        
        self.timestamps.append(now)
        return True

class PriceMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.monitored_tokens: Set[str] = set()
        self.last_prices: Dict[str, PriceUpdate] = {}
        self.is_running = False
        
        # Enhanced settings
        self.update_interval = config.get('price_check_interval', 60)
        self.jupiter_url = config.get('jupiter_url', 'https://price.jup.ag/v4/price')
        self.usdc_mint = config.get('usdc_mint', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
        self.price_change_threshold = config.get('price_change_threshold', 1.0)
        self.max_price_deviation = config.get('max_price_deviation', 30.0)  # Max allowed % deviation
        self.min_price_value = config.get('min_price_value', 1e-12)  # Minimum valid price
        
        # Rate limiting - 100 requests per minute by default
        self.rate_limiter = RateLimiter(
            calls=config.get('rate_limit_calls', 100),
            period=config.get('rate_limit_period', 60)
        )
        
        # HTTP session configuration
        self.timeout = ClientTimeout(total=10)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Callbacks
        self.price_update_callbacks: List[Callable] = []
        self.price_alert_callbacks: List[Callable] = []
        
        # Statistics and monitoring
        self.stats = {
            'request_count': 0,
            'error_count': 0,
            'invalid_data_count': 0,
            'last_request_time': None,
            'last_error_time': None,
            'last_error_message': None
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(self, url: str, params: Dict) -> Dict:
        """Make HTTP request with retry logic and rate limiting"""
        await self.rate_limiter.acquire()
        
        async with self.session.get(url, params=params, timeout=self.timeout) as response:
            if response.status != 200:
                self.stats['error_count'] += 1
                self.stats['last_error_time'] = datetime.now()
                self.stats['last_error_message'] = f"HTTP {response.status}"
                raise aiohttp.ClientError(f"Jupiter API error: {response.status}")
            
            return await response.json()

    def _validate_price_data(self, token_mint: str, price_data: Dict) -> PriceUpdate:
        """Validate price data and return structured update"""
        errors = []
        current_price = float(price_data.get('price', 0))
        
        # Price range validation
        if current_price < self.min_price_value:
            errors.append(f"Price below minimum threshold: {current_price}")
        
        # Price deviation check if we have previous data
        if token_mint in self.last_prices:
            last_update = self.last_prices[token_mint]
            price_change = abs((current_price - last_update.price) / last_update.price * 100)
            if price_change > self.max_price_deviation:
                errors.append(f"Price deviation too high: {price_change}%")
        
        return PriceUpdate(
            token_mint=token_mint,
            price=current_price,
            timestamp=datetime.now(),
            raw_data=price_data,
            is_valid=len(errors) == 0,
            validation_errors=errors if errors else None
        )

    async def _process_price_update(self, token_mint: str, price_data: Dict):
        """Process and validate price updates"""
        try:
            price_update = self._validate_price_data(token_mint, price_data)
            
            if not price_update.is_valid:
                self.stats['invalid_data_count'] += 1
                logger.warning(f"Invalid price data for {token_mint}: {price_update.validation_errors}")
                return
            
            # Calculate price change if we have previous valid price
            if token_mint in self.last_prices:
                last_update = self.last_prices[token_mint]
                price_change = ((price_update.price - last_update.price) / last_update.price) * 100
                
                if abs(price_change) >= self.price_change_threshold:
                    await self._notify_price_alert(token_mint, price_update.price, price_change)
            
            # Update last price and notify
            self.last_prices[token_mint] = price_update
            await self._notify_price_update(token_mint, price_update)

        except Exception as e:
            logger.error(f"Error processing price update for {token_mint}: {e}")
            self.stats['error_count'] += 1
            self.stats['last_error_time'] = datetime.now()
            self.stats['last_error_message'] = str(e)

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
            self.stats['last_error_time'] = datetime.now()
            self.stats['last_error_message'] = str(e)
        finally:
            await self.stop()

    async def stop(self):
        """Stop the price monitoring service"""
        logger.info("Stopping price monitor service...")
        self.is_running = False
        if self.session:
            await self.session.close()
            self.session = None

    def get_stats(self) -> Dict:
        """Get current monitoring statistics"""
        return {
            **self.stats,
            'monitored_tokens': len(self.monitored_tokens),
            'is_running': self.is_running
        }

    def get_token_price(self, token_mint: str) -> Optional[PriceUpdate]:
        """Get the latest price update for a specific token"""
        return self.last_prices.get(token_mint)

    async def _check_prices(self):
        """Check prices for all monitored tokens"""
        if not self.monitored_tokens:
            return

        try:
            # Batch tokens into groups of 100 to avoid URL length limits
            token_batches = [list(self.monitored_tokens)[i:i + 100] 
                           for i in range(0, len(self.monitored_tokens), 100)]
            
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
            self.stats['error_count'] += 1
            self.stats['last_error_time'] = datetime.now()
            self.stats['last_error_message'] = str(e)

    async def _notify_price_update(self, token_mint: str, price_update: PriceUpdate):
        """Notify all registered callbacks about price updates"""
        for callback in self.price_update_callbacks:
            try:
                await callback(token_mint, price_update.price, price_update.raw_data)
            except Exception as e:
                logger.error(f"Error in price update callback: {e}")

    async def _notify_price_alert(self, token_mint: str, price: float, price_change: float):
        """Notify all registered callbacks about price alerts"""
        for callback in self.price_alert_callbacks:
            try:
                await callback(token_mint, price, price_change)
            except Exception as e:
                logger.error(f"Error in price alert callback: {e}")

    def add_price_update_callback(self, callback: Callable):
        """Register a new price update callback"""
        self.price_update_callbacks.append(callback)

    def add_price_alert_callback(self, callback: Callable):
        """Register a new price alert callback"""
        self.price_alert_callbacks.append(callback)

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
        self.last_prices.pop(token_mint, None)