import asyncio
from core.bot import TradingBot
from config.settings import load_config

async def main():
    # Load configuration
    config = load_config()
    
    # Initialize bot
    bot = TradingBot(config)
    
    # Run the bot
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())