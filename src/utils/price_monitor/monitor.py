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