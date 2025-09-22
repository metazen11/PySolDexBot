# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Solana Token Security Scanner that monitors new Raydium liquidity pools and filters out potential scam tokens to find legitimate investment opportunities. The system consists of:

- **Token Scanner** (`optimized_scanner.py`): Continuously monitors Raydium DEX for new liquidity pools + **integrated price tracking** from DexScreener API
- **Dashboard** (`advanced_filter_dashboard.py`): Flask-based web interface with **real-time momentum analysis**
- **Database** (`raydium_pools.db`): SQLite database storing 700K+ pool records + **price history for momentum tracking**

## Tech Stack

- **Backend Framework**: Flask (lightweight Python web framework)
- **Database**: SQLite with 700K+ token records
- **Frontend**: HTML templates with vanilla JavaScript (no heavy frameworks)
- **Python Libraries**:
  - `aiohttp` for async HTTP requests
  - `solana` SDK for blockchain interaction
  - `flask` for web dashboard
  - `python-telegram-bot` for optional notifications

## Development Commands

### Running the Scanner

```bash
# Standard version
python3 main.py

# Optimized version with enhanced features
python3 optimized_scanner.py

# Using startup script (recommended)
./start_optimized.sh

# With activity tracking
./start_with_activity.sh

# Stop all services
./stop_services.sh
```

### Running the Dashboard

```bash
# Basic dashboard
python3 dashboard.py

# Enhanced dashboard with better filtering
python3 enhanced_dashboard.py

# Advanced filter dashboard
python3 advanced_filter_dashboard.py
```

### Database Operations

```bash
# Optimize database (when it gets large)
sqlite3 raydium_pools.db "VACUUM;"
sqlite3 raydium_pools.db "REINDEX;"
sqlite3 raydium_pools.db "ANALYZE;"

# Check database size and recent entries
sqlite3 raydium_pools.db "SELECT COUNT(*) FROM pools WHERE discovered_at > datetime('now', '-1 hour');"
```

### Installing Dependencies

```bash
pip install -r requirements.txt
```

## Code Architecture

### Core Components

1. **Scanner Module** (`main.py`/`optimized_scanner.py`):
   - Fetches pool data from Raydium API every 30-60 seconds
   - Checks token security (mint/freeze authorities) via Solana RPC
   - Verifies trading activity through Solscan API
   - Stores discovered tokens in SQLite database
   - Optionally sends Telegram notifications

2. **Configuration** (`config.py`):
   - Centralized configuration for security filters, API endpoints, and performance settings
   - Security modes: `conservative`, `normal`, `aggressive`
   - Configurable liquidity/volume thresholds

3. **Database Schema** (SQLite):
   - Table: `pools`
   - Key columns: `lp_mint`, `name`, `liquidity`, `volume24h`, `token_address`, `is_pump_token`, `discovered_at`, `has_mint_authority`, `has_freeze_authority`

### API Integrations

- **Raydium API** (`https://api.raydium.io/v2/main/pairs`): Pool discovery
- **Solana RPC** (`https://api.mainnet-beta.solana.com`): Token metadata and authority checks
- **Solscan API** (`https://public-api.solscan.io/account/transactions`): Transaction verification
- **DexScreener API** (`https://api.dexscreener.com/latest/dex/tokens`): **Real-time price data and momentum tracking** (300 req/min limit)

### Security Filtering Logic

The scanner applies multiple security checks:
- No mint authority (prevents infinite supply creation)
- No freeze authority (prevents fund freezing)
- Minimum liquidity thresholds ($500-$10,000+)
- Active trading volume requirements
- Recent transaction verification
- Pump.fun token detection

## Environment Variables

Optional `.env` file for Telegram notifications:
```
TG_API_KEY=your_telegram_bot_token
TG_CHAT_ID=your_chat_id
```

Configuration via environment:
```bash
CHECK_INTERVAL=30  # Scan interval in seconds
SECURITY_MODE=normal  # conservative/normal/aggressive
DATABASE_FILE=raydium_pools.db
DASHBOARD_PORT=8080
```

## Momentum Tracking System

The scanner now includes **integrated price momentum tracking**:

### Price History Database
- **Table**: `price_history` - stores comprehensive price data every scan cycle
- **Fields**: price_usd, volume_5m/1h/24h, buy/sell ratios, market_cap, momentum_score
- **Retention**: 7 days of historical data for trend analysis

### Momentum Calculation
- **Price Momentum** (50%): Recent price trend analysis
- **Volume Momentum** (25%): Trading volume trends
- **Buy Pressure** (25%): Buy vs sell ratio analysis
- **Score Range**: -100 (bearish) to +100 (bullish)

### Time-Aware Filtering
- **Weekend/Evening Mode**: Lower thresholds for meme token activity
- **Business Hours Mode**: Stricter criteria for utility tokens
- **Exchange Worthy Filter**: Tokens 6+ hours old with sustained activity
- **Survivors Filter**: Tokens that maintain momentum over time

## Important Notes

- Database grows ~1MB per day with continuous scanning + price history
- Raydium API has no strict rate limits observed
- Solscan API limited to 120 requests/minute
- **DexScreener API limited to 300 requests/minute** (integrated price tracking)
- Dashboard runs on port 8084 (advanced dashboard with momentum features)
- Scanner logs to stdout or `logs/scanner.log` when using startup scripts
- Project uses Flask (not Django) for lightweight web serving
- No heavy frontend frameworks - uses vanilla JavaScript for simplicity

## Project Memory

See `MEMORY.txt` for detailed session history, achievements, and current state. Key highlights:
- 701,524+ tokens tracked in database
- Multiple dashboard versions with advanced filtering capabilities
- Competitive advantages over DexTools/DexScreener
- Real-time scanning every 30-60 seconds
- Advanced filtering dashboard is the primary interface (port 8084)