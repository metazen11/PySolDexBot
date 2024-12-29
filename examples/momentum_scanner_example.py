import asyncio
import logging
from datetime import datetime
from src.config.settings import load_config
from src.services.scanner.momentum_scanner import MomentumScanner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def print_opportunity(opportunity: dict):
    """Pretty print an opportunity"""
    print(
        f"\n{'='*50}\n"
        f"Token: {opportunity['symbol']}\n"
        f"Price: ${opportunity['current_price']:.6f}\n"
        f"Market Cap: ${opportunity['market_cap']:,.0f}\n"
        f"24h Volume: ${opportunity['volume_24h']:,.0f}\n"
        f"Liquidity: ${opportunity['liquidity_usd']:,.0f}\n"
        f"Safety Score: {opportunity['safety_score']:.1f}/100\n"
        f"Momentum Score: {opportunity['momentum_score']:.1f}/100\n"
        f"Found: {opportunity['found_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'='*50}"
    )

async def monitor_opportunities(scanner: MomentumScanner):
    """Monitor and display opportunities"""
    while True:
        print(f"\nActive Opportunities: {len(scanner.opportunities)}")
        print(f"Blacklisted Tokens: {len(scanner.blacklisted_tokens)}")
        
        # Print top 5 opportunities sorted by momentum score
        sorted_opportunities = sorted(
            scanner.opportunities.items(),
            key=lambda x: x[1]['momentum_score'],
            reverse=True
        )[:5]
        
        if sorted_opportunities:
            print("\nTop Opportunities:")
            for _, opp in sorted_opportunities:
                await print_opportunity(opp)
        
        await asyncio.sleep(60)

async def main():
    # Load configuration
    config = load_config()
    
    # Example configuration overrides
    scanner_config = {
        **config,
        'min_liquidity_usd': 50000,  # $50k minimum liquidity
        'min_volume_24h': 10000,     # $10k minimum 24h volume
        'min_holders': 200,          # Minimum holder count
        'max_market_cap': 10000000,  # $10M maximum market cap
        'volume_spike_threshold': 3.0,  # 300% volume increase
        'price_increase_threshold': 0.05,  # 5% price increase
    }
    
    try:
        # Initialize scanner
        scanner = MomentumScanner(scanner_config)
        
        # Start monitoring task
        monitor_task = asyncio.create_task(monitor_opportunities(scanner))
        
        # Start scanner
        logger.info("Starting momentum scanner...")
        await scanner.start()
        
        # Wait for monitoring task
        await monitor_task
        
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        await scanner.stop()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        await scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())
