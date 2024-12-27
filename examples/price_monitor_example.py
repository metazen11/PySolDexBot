import asyncio
import logging
from datetime import datetime
from src.utils.price_monitor.monitor import PriceMonitor
from src.config.settings import load_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example callback for price updates
async def handle_price_update(token_mint: str, price: float, price_data: dict):
    logger.info(f"Price Update: {token_mint}")
    logger.info(f"Current Price: ${price:.4f}")
    logger.info(f"24h Volume: ${price_data.get('volume24h', 0):,.2f}")
    logger.info("---")

# Example callback for price alerts
async def handle_price_alert(token_mint: str, price: float, price_change: float):
    direction = "🟢 Up" if price_change > 0 else "🔴 Down"
    logger.warning(
        f"Price Alert: {token_mint}\n"
        f"Direction: {direction} {abs(price_change):.2f}%\n"
        f"Current Price: ${price:.4f}"
    )

async def main():
    # Load configuration
    config = load_config()
    
    # Example tokens to monitor
    tokens_to_monitor = [
        "RAY",  # Raydium
        "BONK",  # Bonk
        "JUP"   # Jupiter
    ]
    
    try:
        # Initialize price monitor
        monitor = PriceMonitor(config['price_monitor'])
        
        # Add callbacks
        monitor.add_price_update_callback(handle_price_update)
        monitor.add_price_alert_callback(handle_price_alert)
        
        # Start monitoring
        logger.info("Starting price monitoring...")
        
        # Add tokens to monitor
        for token in tokens_to_monitor:
            await monitor.add_token(token)
        
        # Start the monitor
        await monitor.start()
        
        # Keep running
        while True:
            # Print stats every minute
            stats = monitor.get_stats()
            logger.info(
                f"\nMonitor Stats:\n"
                f"Monitored Tokens: {stats['monitored_tokens']}\n"
                f"Requests Made: {stats['request_count']}\n"
                f"Errors: {stats['error_count']}\n"
                f"Last Request: {stats['last_request_time']}\n"
                f"Status: {'Running' if stats['is_running'] else 'Stopped'}"
            )
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        await monitor.stop()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())
