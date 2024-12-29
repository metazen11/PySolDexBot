import asyncio
from typing import Dict, Set, Optional, Callable, List
import aiohttp
from datetime import datetime
import logging
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import PriceUpdate
from .constants import *
from ..rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class PriceMonitor:
    """Monitors token prices using Jupiter API
    
    Provides real-time price monitoring with:
    - Rate limiting
    - Data validation
    - Error handling
    - Statistics tracking
    """
    def __init__(self, config: Dict):
        # Previous implementation...
        pass
        
    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=DEFAULT_RETRY_MIN_WAIT, max=DEFAULT_RETRY_MAX_WAIT)
    )
    async def _make_request(self, url: str, params: Dict) -> Dict:
        """Make HTTP request with retry logic and rate limiting
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            Dict: Response JSON data
            
        Raises:
            aiohttp.ClientError: On failed requests
        """
        await self.rate_limiter.acquire()
        
        async with self.session.get(url, params=params, timeout=self.timeout) as response:
            if response.status != 200:
                self.stats['error_count'] += 1
                self.stats['last_error_time'] = datetime.now()
                self.stats['last_error_message'] = f"HTTP {response.status}"
                raise aiohttp.ClientError(f"Jupiter API error: {response.status}")
            
            return await response.json()
            
    def _validate_price_data(self, token_mint: str, price_data: Dict) -> PriceUpdate:
        """Validate price data and return structured update
        
        Args:
            token_mint: Token mint address
            price_data: Raw price data from API
            
        Returns:
            PriceUpdate: Validated price update object
        """
        current_price = float(price_data.get('price', 0))
        update = PriceUpdate(
            token_mint=token_mint,
            price=current_price,
            timestamp=datetime.now(),
            raw_data=price_data
        )
        
        # Price range validation
        if current_price < self.min_price_value:
            update.add_error(f"Price below minimum threshold: {current_price}")
        
        # Price deviation check if we have previous data
        if token_mint in self.last_prices:
            last_update = self.last_prices[token_mint]
            price_change = abs((current_price - last_update.price) / last_update.price * 100)
            if price_change > self.max_price_deviation:
                update.add_error(f"Price deviation too high: {price_change}%")
        
        return update