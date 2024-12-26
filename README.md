# PySolDexBot

A Python-based Solana DEX trading bot with technical analysis capabilities. Uses Jupiter for DEX aggregation and implements various technical analysis strategies.

## Features

- Technical Analysis indicators (ADX, RSI, Momentum, VWAP)
- Jupiter DEX integration for best execution
- Multiple timeframe analysis
- Configurable trading strategies
- Async architecture for better performance

## Project Structure

```
PySolDexBot/
├── src/
│   ├── config/
│   │   ├── settings.py
│   │   └── tokens.py
│   ├── core/
│   │   ├── bot.py
│   │   └── jupiter.py
│   ├── strategies/
│   │   ├── base.py
│   │   └── momentum.py
│   ├── indicators/
│   │   ├── technical.py
│   │   └── volume.py
│   └── utils/
       ├── logger.py
       └── timeframes.py
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/metazen11/PySolDexBot.git
cd PySolDexBot
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Edit the `.env` file with your settings:

```env
# Network Settings
SOLANA_RPC_URL=your_rpc_url
NETWORK=mainnet  # or devnet

# Wallet Settings
WALLET_PRIVATE_KEY=your_private_key

# Trading Parameters
SLIPPAGE=0.5
```

## Usage

1. Configure your trading parameters in `src/config/settings.py`
2. Run the bot:
```bash
python src/main.py
```

## Development

To add a new strategy:

1. Create a new file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement `should_enter` and `should_exit` methods

Example:
```python
from .base import BaseStrategy

class MyStrategy(BaseStrategy):
    async def should_enter(self, df):
        # Implement entry logic
        pass

    async def should_exit(self, df):
        # Implement exit logic
        pass
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT