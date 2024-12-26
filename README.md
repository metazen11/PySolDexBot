# PySolDexBot

A Python-based Solana DEX trading bot with technical analysis capabilities. Uses Jupiter for DEX aggregation and implements various technical analysis strategies.

## Features

- Technical Analysis indicators (ADX, RSI, Momentum, VWAP)
- Jupiter DEX integration for best execution
- Multiple timeframe analysis
- Configurable trading strategies
- Async architecture for better performance

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

## License

MIT