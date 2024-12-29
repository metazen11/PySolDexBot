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
        self.config = config
        self.monitored_tokens: Set[str] = set()
        self.last_prices: Dict[str, PriceUpdate] = {}
        self.is_running = False
        
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