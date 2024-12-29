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