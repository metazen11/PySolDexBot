import asyncio
import logging
from datetime import datetime
from typing import Dict

from src.config import load_config
from src.db.base import db
from src.utils.price_monitor.monitor import PriceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Example callback for price updates
async def price_update_callback(token_mint: str, price: float, price_data: Dict):
    logger.info(f"Price update for {token_mint}: ${price:.6f} USD")
    if price_data.get('price_change_24h'):
        logger.info(f"24h change: {price_data['price_change_24h']:.2f}%")

# Example callback for significant price changes
async def price_alert_callback(token_mint: str, price: float, price_change: float):
    logger.warning(f"Significant price movement for {token_mint}!")
    logger.warning(f"Current price: ${price:.6f} USD")
    logger.warning(f"Price change: {price_change:.2f}%")

async def main():
    try:
        # Load configuration
        config = load_config()
        
        # Initialize database
        db.init(config['database_url'])
        
        # Create price monitor instance
        monitor = PriceMonitor(config)
        
        # Add callbacks
        monitor.add_price_update_callback(price_update_callback)
        
        # Add some tokens to monitor
        # SOL, BONK, and ORCA as examples
        tokens_to_monitor = [
            'So11111111111111111111111111111111111111112',  # Wrapped SOL
            'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',  # BONK
            'orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE',  # ORCA
        ]
        
        for token in tokens_to_monitor:
            await monitor.add_token(token)
            logger.info(f"Added {token} to monitoring")
        
        # Start monitoring
        logger.info("Starting price monitoring...")
        await monitor.start()
        
        # Keep script running
        while True:
            await asyncio.sleep(60)
            
            # Print current prices every minute
            prices = await monitor.get_monitored_prices()
            logger.info("\nCurrent prices:")
            for token, price in prices.items():
                logger.info(f"{token}: ${price:.6f} USD")
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await monitor.stop()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())
