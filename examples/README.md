# PySolDexBot Examples

This directory contains example scripts demonstrating how to use various components of the PySolDexBot.

## Prerequisites

1. Set up your environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r ../requirements.txt
```

2. Create a `.env` file in the project root with your configuration:
```env
# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=soldexbot
DB_USER=your_user
DB_PASSWORD=your_password

# Price monitoring
PRICE_CHECK_INTERVAL=60
PRICE_CHANGE_THRESHOLD=1.0
MIN_LIQUIDITY_USD=50000
MIN_VOLUME_24H=10000
```

## Available Examples

### 1. Price Monitoring (`monitor_prices.py`)

Demonstrates real-time price monitoring with database integration:

```bash
python monitor_prices.py
```

Features demonstrated:
- Database initialization
- Price monitor setup and configuration
- Token monitoring
- Price update callbacks
- Error handling
- Data persistence

Output example:
```
2024-12-30 12:00:01 - root - INFO - Starting price monitoring...
2024-12-30 12:00:02 - root - INFO - Added So11111111111111111111111111111111111111112 to monitoring
2024-12-30 12:00:02 - root - INFO - Price update for So11111111111111111111111111111111111111112: $95.420000 USD
2024-12-30 12:00:02 - root - INFO - 24h change: 2.50%
```

## Creating New Examples

When creating new examples:
1. Create a new Python file in this directory
2. Add proper error handling
3. Include logging
4. Document the example in this README
5. Test with a clean environment

## Notes

- Examples are meant for demonstration and may need modification for production use
- Always use proper error handling in production
- Consider rate limits and API quotas
- Monitor resource usage when running long-term