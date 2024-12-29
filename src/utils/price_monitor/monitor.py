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
            self.stats['error_count'] += 1
            self.stats['last_error_time'] = datetime.now()
            self.stats['last_error_message'] = str(e)

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