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
    # Previous methods remain the same...
    
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