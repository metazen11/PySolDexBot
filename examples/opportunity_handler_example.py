import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from src.config.settings import load_config
from src.services.scanner.momentum_scanner import MomentumScanner
from src.utils.price_monitor.monitor import PriceMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OpportunityHandler:
    def __init__(self, config: dict):
        self.config = config
        self.scanner = MomentumScanner(config)
        
        # Trading settings
        self.min_safety_score = config.get('min_safety_score', 80)
        self.min_momentum_score = config.get('min_momentum_score', 75)
        self.position_size_usd = config.get('position_size_usd', 100)  # $100 per trade
        self.max_positions = config.get('max_positions', 3)
        
        # Risk management
        self.stop_loss_pct = config.get('stop_loss_pct', 10)  # 10% stop loss
        self.take_profit_pct = config.get('take_profit_pct', 30)  # 30% take profit
        self.trailing_stop_pct = config.get('trailing_stop_pct', 15)  # 15% trailing stop
        
        # Track active positions
        self.active_positions = {}
        
        # Bind price update handler
        self.scanner.price_monitor.add_price_update_callback(self._handle_price_update)

    async def start(self):
        """Start the opportunity handler"""
        logger.info("Starting opportunity handler...")
        
        # Start the scanner
        await self.scanner.start()
        
        # Start position monitoring
        while True:
            try:
                await self._monitor_positions()
                await asyncio.sleep(1)  # Check positions every second
            except Exception as e:
                logger.error(f"Error monitoring positions: {e}")
                await asyncio.sleep(5)

    async def _handle_opportunity(self, token_mint: str, opportunity: dict):
        """Handle a new opportunity"""
        try:
            # Check if we can take new positions
            if len(self.active_positions) >= self.max_positions:
                logger.info(f"Maximum positions reached, skipping {opportunity['symbol']}")
                return

            # Validate scores
            if (opportunity['safety_score'] < self.min_safety_score or 
                opportunity['momentum_score'] < self.min_momentum_score):
                logger.info(f"Scores too low for {opportunity['symbol']}")
                return

            # Calculate position size
            position_size = await self._calculate_position_size(opportunity)
            if not position_size:
                return

            # Execute entry
            success = await self._execute_entry(token_mint, opportunity, position_size)
            if success:
                self._track_position(token_mint, opportunity, position_size)

        except Exception as e:
            logger.error(f"Error handling opportunity: {e}")

    async def _monitor_positions(self):
        """Monitor active positions"""
        for token_mint, position in list(self.active_positions.items()):
            try:
                current_price = position['current_price']
                entry_price = position['entry_price']
                highest_price = position['highest_price']
                
                # Update unrealized PnL
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                position['unrealized_pnl_pct'] = pnl_pct
                
                # Check stop loss
                if pnl_pct <= -self.stop_loss_pct:
                    logger.warning(f"🛑 Stop loss hit for {position['symbol']}")
                    await self._execute_exit(token_mint, position, 'stop_loss')
                    continue

                # Check take profit
                if pnl_pct >= self.take_profit_pct:
                    logger.info(f"🎯 Take profit hit for {position['symbol']}")
                    await self._execute_exit(token_mint, position, 'take_profit')
                    continue

                # Check trailing stop
                if highest_price > entry_price:
                    trail_price = highest_price * (1 - self.trailing_stop_pct/100)
                    if current_price <= trail_price:
                        logger.warning(f"🎯 Trailing stop hit for {position['symbol']}")
                        await self._execute_exit(token_mint, position, 'trailing_stop')
                        continue

            except Exception as e:
                logger.error(f"Error monitoring position {token_mint}: {e}")

    async def _handle_price_update(self, token_mint: str, price: float, price_data: dict):
        """Handle price updates"""
        if token_mint in self.active_positions:
            position = self.active_positions[token_mint]
            position['current_price'] = price
            position['highest_price'] = max(price, position['highest_price'])
            
            # Log position update
            pnl_pct = position['unrealized_pnl_pct']
            logger.info(
                f"Position Update: {position['symbol']}\n"
                f"Current Price: ${price:.6f}\n"
                f"PnL: {pnl_pct:+.2f}%"
            )

    async def _calculate_position_size(self, opportunity: dict) -> Optional[Decimal]:
        """Calculate position size based on risk parameters"""
        try:
            # Fixed position size for example
            return Decimal(self.position_size_usd)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return None

    async def _execute_entry(self, token_mint: str, opportunity: dict, size_usd: Decimal) -> bool:
        """Execute entry trade"""
        try:
            # Simulate trade execution
            logger.info(
                f"🔥 Executing entry for {opportunity['symbol']}:\n"
                f"Size: ${size_usd}\n"
                f"Price: ${opportunity['current_price']:.6f}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error executing entry: {e}")
            return False

    async def _execute_exit(self, token_mint: str, position: dict, reason: str) -> bool:
        """Execute exit trade"""
        try:
            # Simulate trade execution
            logger.info(
                f"📤 Executing exit for {position['symbol']}:\n"
                f"Reason: {reason}\n"
                f"Entry: ${position['entry_price']:.6f}\n"
                f"Exit: ${position['current_price']:.6f}\n"
                f"PnL: {position['unrealized_pnl_pct']:+.2f}%"
            )
            
            # Remove from active positions
            self.active_positions.pop(token_mint)
            return True
            
        except Exception as e:
            logger.error(f"Error executing exit: {e}")
            return False

    def _track_position(self, token_mint: str, opportunity: dict, size_usd: Decimal):
        """Track new position"""
        self.active_positions[token_mint] = {
            'symbol': opportunity['symbol'],
            'entry_time': datetime.now(),
            'entry_price': opportunity['current_price'],
            'current_price': opportunity['current_price'],
            'highest_price': opportunity['current_price'],
            'position_size': size_usd,
            'unrealized_pnl_pct': 0.0
        }

async def main():
    # Load configuration
    config = load_config()
    
    # Add trading settings
    config.update({
        'position_size_usd': 100,  # $100 per trade
        'max_positions': 3,         # Maximum 3 positions
        'stop_loss_pct': 10,        # 10% stop loss
        'take_profit_pct': 30,      # 30% take profit
        'trailing_stop_pct': 15,    # 15% trailing stop
        'min_safety_score': 80,     # Minimum 80/100 safety score
        'min_momentum_score': 75    # Minimum 75/100 momentum score
    })
    
    try:
        # Initialize and start handler
        handler = OpportunityHandler(config)
        await handler.start()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        await handler.scanner.stop()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        await handler.scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())
