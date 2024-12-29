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
        self.max_price_deviation = config.get('max_price_deviation', 30.0)
        self.min_price_value = config.get('min_price_value', 1e-12)
        
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