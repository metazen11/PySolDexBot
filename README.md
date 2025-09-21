# 🛡️ Solana Token Security Scanner

A real-time security scanner for Solana tokens that monitors new Raydium liquidity pools and filters out rug pulls, honeypots, and scam tokens to find legitimate investment opportunities.

## 🎯 What It Does

- **Monitors Raydium DEX** for new liquidity pools every 60 seconds
- **Security Analysis** - Checks for mint/freeze authorities (rug pull indicators)
- **Liquidity Filtering** - Only shows tokens with substantial liquidity ($5k+)
- **Pump.fun Detection** - Filters out pump.fun tokens
- **Real-time Dashboard** - Web interface to view safe tokens
- **Transaction Monitoring** - Verifies recent trading activity

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd solana-token-scanner

# Install Python dependencies
pip install -r requirements.txt

# Optional: Set up Telegram notifications
cp .env.example .env
# Edit .env with your Telegram bot credentials
```

### 2. Environment Setup

Create a `.env` file (optional, for Telegram alerts):
```bash
TG_API_KEY=your_telegram_bot_token
TG_CHAT_ID=your_chat_id
```

### 3. Run the Scanner

```bash
# Start the token scanner (runs continuously)
python3 main.py

# In another terminal, start the dashboard
python3 dashboard.py
```

### 4. View Results

Open your browser to: **http://localhost:8080**

The dashboard shows:
- **Recent Discoveries** - Tokens found in last 2 hours
- **Safe Tokens** - Filtered list passing security checks
- **Real-time Stats** - Pool counts and discovery metrics

## 📊 Dashboard Features

### Recent Token Discoveries
- Shows tokens discovered in last 2 hours
- Minimum $500 liquidity requirement
- Direct links to Solscan and DexScreener
- Pump.fun token indicators

### Safe Token List
- **High Liquidity**: $10,000+ minimum
- **Trading Volume**: $500+ daily volume
- **No Pump Tokens**: Filters out pump.fun launches
- **Safety Score**: 1-10 rating system
- **Fresh Data**: Last 6 hours only

## 🔒 Security Filters

The scanner applies multiple security checks:

### ✅ **Safe Token Criteria**
- ❌ No mint authority (can't create infinite supply)
- ❌ No freeze authority (can't freeze user funds)
- ✅ Substantial liquidity ($10k+)
- ✅ Active trading volume ($500+)
- ✅ Not a pump.fun token
- ✅ Recent trading activity

### 🚨 **Red Flags Detected**
- Mint authority present
- Freeze authority present
- Low liquidity pools
- Pump.fun launches
- No recent transactions

## 🛠️ Project Structure

```
├── main.py              # Core scanner logic
├── dashboard.py         # Web dashboard
├── alterdb.py          # Database migrations
├── requirements.txt    # Python dependencies
├── .env               # Telegram config (optional)
├── templates/
│   └── dashboard.html # Dashboard UI
└── raydium_pools.db   # SQLite database
```

## 🔧 Configuration

### Scanner Settings (main.py)
```python
CHECK_INTERVAL = 60        # Scan every 60 seconds
RAYDIUM_API_ENDPOINT      # Raydium pools API
SOLANA_RPC_ENDPOINT       # Solana RPC for token analysis
SOLSCAN_API_ENDPOINT      # Transaction verification
```

### Dashboard Filters (dashboard.py)
```python
# Recent tokens (last 2 hours, $500+ liquidity)
# Safe tokens (last 6 hours, $10k+ liquidity, $500+ volume)
```

## 📈 Performance Tips

### Database Optimization
```bash
# The database grows large over time. To optimize:
sqlite3 raydium_pools.db "VACUUM;"
sqlite3 raydium_pools.db "REINDEX;"
```

### API Rate Limiting
- Raydium API: No strict limits observed
- Solscan API: 120 requests/minute
- Solana RPC: Varies by provider

## 🚀 Advanced Usage

### Running Multiple Instances
```bash
# Different scan intervals
CHECK_INTERVAL=30 python3 main.py  # Scan every 30 seconds

# Different database
DATABASE_FILE=fast_scan.db python3 main.py
```

### Custom Security Filters
Edit `dashboard.py` to adjust filtering criteria:
```python
# More conservative (higher liquidity)
AND liquidity > 50000
AND volume24h > 2000

# More aggressive (lower requirements)
AND liquidity > 1000
AND volume24h > 100
```

## 🔍 Monitoring & Logs

### Scanner Output
```
2025-09-20 06:11:58 - INFO - Current pools fetched: 701535
2025-09-20 06:12:03 - INFO - Found 5 new untradable pools
2025-09-20 06:12:05 - INFO - Safe token found: TokenName (address)
```

### Database Queries
```sql
-- Check recent discoveries
SELECT COUNT(*) FROM pools WHERE discovered_at > datetime('now', '-1 hour');

-- View safe tokens
SELECT name, liquidity, volume24h FROM pools
WHERE liquidity > 10000 AND is_pump_token = 0
ORDER BY discovered_at DESC LIMIT 10;
```

## ⚠️ Important Notes

### Security Disclaimers
- **This tool provides analysis, not investment advice**
- **Always DYOR (Do Your Own Research)**
- **Check contract source code when available**
- **Verify team/project legitimacy**
- **Start with small amounts**

### API Dependencies
- Requires internet connection for real-time data
- Raydium API availability affects discovery speed
- Solscan API needed for transaction verification

### Database Growth
- Database grows ~1MB per day
- Contains 700k+ historical pool records
- Consider periodic cleanup for old records

## 🚨 Troubleshooting

### Common Issues

**"Database is locked"**
```bash
# Kill all scanner processes
pkill -f "python3 main.py"
# Restart scanner
python3 main.py
```

**"Port already in use"**
```bash
# Change dashboard port
# Edit dashboard.py: app.run(port=8081)
```

**"No recent tokens found"**
- Wait 5-10 minutes for new pool discoveries
- Check scanner logs for API errors
- Verify internet connection

### Performance Issues
```bash
# Check system resources
top -p $(pgrep -f "python3 main.py")

# Database optimization
sqlite3 raydium_pools.db "ANALYZE;"
```

## 📞 Support

For issues or improvements:
1. Check the troubleshooting section
2. Review scanner logs for errors
3. Verify API endpoints are accessible
4. Consider adjusting scan intervals

## 🎉 Success Metrics

A well-configured scanner should:
- Discover 5-20 new tokens per hour
- Find 1-5 "safe" tokens per day
- Maintain <5% false positives
- Complete scans in under 30 seconds

---

**Happy safe token hunting! 🚀**