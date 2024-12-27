# PySolDexBot Examples

This directory contains example scripts demonstrating how to use different components of the bot.

## Price Monitor Example

The `price_monitor_example.py` script shows how to:
1. Set up and configure the price monitor
2. Monitor multiple tokens
3. Handle price updates and alerts
4. Track monitoring statistics

To run the example:

```bash
# Make sure you're in the project root
python -m examples.price_monitor_example
```

### Configuration

Before running, ensure your `.env` file includes the following settings:

```env
# Price Monitor Settings
PRICE_CHECK_INTERVAL=60  # seconds
PRICE_CHANGE_THRESHOLD=1.0  # percentage
```

### Example Output

The script will output something like:

```
Starting price monitoring...

Price Update: RAY
Current Price: $0.4876
24h Volume: $1,234,567.89
---

Price Alert: BONK
Direction: 🔴 Down 1.50%
Current Price: $0.00001234

Monitor Stats:
Monitored Tokens: 3
Requests Made: 42
Errors: 0
Last Request: 2024-12-27 12:34:56
Status: Running
```
