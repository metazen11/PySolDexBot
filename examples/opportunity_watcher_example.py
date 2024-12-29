import asyncio
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path
from src.config.settings import load_config
from src.services.scanner.momentum_scanner import MomentumScanner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OpportunityWatcher:
    def __init__(self, config: dict):
        self.config = config
        self.scanner = MomentumScanner(config)
        self.opportunities_file = Path('data/opportunities.json')
        self.opportunities_file.parent.mkdir(exist_ok=True)
        
        # Load previous opportunities if exist
        self.historical_opportunities = self.load_opportunities()
        
        # Price update callback
        self.scanner.price_monitor.add_price_update_callback(self._handle_price_update)
        self.scanner.price_monitor.add_price_alert_callback(self._handle_price_alert)

    def load_opportunities(self) -> dict:
        """Load historical opportunities from file"""
        if self.opportunities_file.exists():
            try:
                with open(self.opportunities_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading opportunities: {e}")
        return {}

    def save_opportunities(self):
        """Save opportunities to file"""
        try:
            with open(self.opportunities_file, 'w') as f:
                json.dump(self.historical_opportunities, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving opportunities: {e}")

    async def start(self):
        """Start watching for opportunities"""
        logger.info("Starting opportunity watcher...")
        
        # Start the scanner
        await self.scanner.start()
        
        # Start monitoring and logging
        while True:
            try:
                await self._log_current_state()
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _handle_price_update(self, token_mint: str, price: float, price_data: dict):
        """Handle price updates"""
        if token_mint in self.scanner.opportunities:
            opp = self.scanner.opportunities[token_mint]
            entry_price = opp['found_price']
            price_change = ((price - entry_price) / entry_price) * 100
            
            # Update historical tracking
            if token_mint not in self.historical_opportunities:
                self.historical_opportunities[token_mint] = {
                    'symbol': opp['symbol'],
                    'found_at': str(opp['found_at']),
                    'entry_price': entry_price,
                    'highest_price': price if price > entry_price else entry_price,
                    'lowest_price': price if price < entry_price else entry_price,
                    'current_price': price,
                    'max_gain_pct': 0,
                    'max_loss_pct': 0,
                    'volume_history': [],
                    'updates': 1
                }
            else:
                hist = self.historical_opportunities[token_mint]
                hist['current_price'] = price
                hist['highest_price'] = max(price, float(hist['highest_price']))
                hist['lowest_price'] = min(price, float(hist['lowest_price']))
                hist['max_gain_pct'] = max(
                    ((float(hist['highest_price']) - float(hist['entry_price'])) 
                     / float(hist['entry_price']) * 100),
                    float(hist['max_gain_pct'])
                )
                hist['max_loss_pct'] = min(
                    ((float(hist['lowest_price']) - float(hist['entry_price'])) 
                     / float(hist['entry_price']) * 100),
                    float(hist['max_loss_pct'])
                )
                hist['volume_history'].append({
                    'timestamp': str(datetime.now()),
                    'volume': price_data.get('volume24h', 0)
                })
                hist['updates'] += 1
                
                # Prune volume history to last 24 hours
                hist['volume_history'] = [
                    v for v in hist['volume_history']
                    if datetime.strptime(v['timestamp'], '%Y-%m-%d %H:%M:%S.%f') > 
                       datetime.now() - timedelta(hours=24)
                ]
            
            self.save_opportunities()

    async def _handle_price_alert(self, token_mint: str, price: float, price_change: float):
        """Handle significant price changes"""
        if token_mint in self.scanner.opportunities:
            opp = self.scanner.opportunities[token_mint]
            direction = "🟢 Up" if price_change > 0 else "🔴 Down"
            logger.warning(
                f"\nPrice Alert: {opp['symbol']}\n"
                f"Direction: {direction} {abs(price_change):.2f}%\n"
                f"Current Price: ${price:.6f}\n"
                f"Safety Score: {opp['safety_score']:.1f}\n"
                f"Momentum Score: {opp['momentum_score']:.1f}"
            )

    async def _log_current_state(self):
        """Log current opportunities and statistics"""
        current_time = datetime.now()
        logger.info(f"\n{'='*50}")
        logger.info(f"Status Update: {current_time}")
        logger.info(f"Active Opportunities: {len(self.scanner.opportunities)}")
        logger.info(f"Historical Opportunities: {len(self.historical_opportunities)}")
        logger.info(f"Blacklisted Tokens: {len(self.scanner.blacklisted_tokens)}")
        
        if self.scanner.opportunities:
            logger.info("\nCurrent Opportunities:")
            sorted_opps = sorted(
                self.scanner.opportunities.items(),
                key=lambda x: x[1]['momentum_score'],
                reverse=True
            )
            
            for token_mint, opp in sorted_opps:
                historical = self.historical_opportunities.get(token_mint, {})
                max_gain = historical.get('max_gain_pct', 0)
                max_loss = historical.get('max_loss_pct', 0)
                
                logger.info(
                    f"\nToken: {opp['symbol']}\n"
                    f"Price: ${opp['current_price']:.6f}\n"
                    f"24h Volume: ${opp['volume_24h']:,.0f}\n"
                    f"Safety: {opp['safety_score']:.1f}/100\n"
                    f"Momentum: {opp['momentum_score']:.1f}/100\n"
                    f"Max Gain: {max_gain:+.2f}%\n"
                    f"Max Loss: {max_loss:+.2f}%"
                )

async def main():
    # Load configuration
    config = load_config()
    
    try:
        # Initialize and start watcher
        watcher = OpportunityWatcher(config)
        await watcher.start()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        await watcher.scanner.stop()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        await watcher.scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())