# PySolDexBot Examples

## Momentum Scanner Example

The `momentum_scanner_example.py` script demonstrates how to use the momentum scanner to find trading opportunities.

### Features
- Real-time token scanning
- Safety and momentum scoring
- Opportunity tracking and display
- Configuration customization

### Configuration
Before running, ensure your `.env` file includes:

```env
# Scanner Settings
MIN_LIQUIDITY_USD=50000
MIN_VOLUME_24H=10000
MIN_HOLDERS=200
MAX_MARKET_CAP=10000000
VOLUME_SPIKE_THRESHOLD=3.0
PRICE_INCREASE_THRESHOLD=0.05

# API Keys
HELIUS_API_KEY=your_helius_key

# Network Settings
SOLANA_RPC_URL=your_rpc_url
```

### Usage
From the project root:
```bash
python -m examples.momentum_scanner_example
```

### Example Output
```
Starting momentum scanner...

Active Opportunities: 3
Blacklisted Tokens: 12

Top Opportunities:
==================================================
Token: XYZ
Price: $0.000123
Market Cap: $5,000,000
24h Volume: $250,000
Liquidity: $75,000
Safety Score: 85.5/100
Momentum Score: 92.3/100
Found: 2024-12-29 14:30:45
==================================================
```

### Understanding Scores

#### Safety Score
Factors considered:
- Contract verification
- Liquidity locks
- Holder distribution
- Trading patterns
- Contract safety checks

#### Momentum Score
Factors considered:
- Price momentum
- Volume spikes
- Technical indicators
- Market patterns