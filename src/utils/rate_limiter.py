import asyncio
import time
from typing import List

class RateLimiter:
    """Rate limiter for API requests
    
    Ensures that API calls don't exceed specified rate limits
    by tracking request timestamps and enforcing delays when needed.
    """
    def __init__(self, calls: int, period: float):
        """Initialize rate limiter
        
        Args:
            calls: Maximum number of calls allowed in the period
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.timestamps: List[float] = []

    async def acquire(self) -> bool:
        """Try to acquire permission to make a request
        
        Checks if request can be made within rate limits.
        If not, waits appropriate time before allowing request.
        
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        
        # Remove timestamps outside current period
        self.timestamps = [ts for ts in self.timestamps 
                         if now - ts <= self.period]
        
        if len(self.timestamps) >= self.calls:
            # Calculate required wait time
            wait_time = self.timestamps[0] + self.period - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                return await self.acquire()
        
        self.timestamps.append(now)
        return True