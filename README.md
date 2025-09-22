# 🛡️ Solana Token Security Scanner

A real-time security scanner for Solana tokens that monitors new Raydium liquidity pools and filters out rug pulls, honeypots, and scam tokens to find legitimate investment opportunities.

## 🎯 What It Does

- **Monitors Raydium DEX** for new liquidity pools every 60 seconds
- **Security Analysis** - Checks for mint/freeze authorities (rug pull indicators)
- **Liquidity Filtering** - Only shows tokens with substantial liquidity ($5k+)
- **Pump.fun Detection** - Filters out pump.fun tokens
- **Real-time Dashboard** - Web interface to view safe tokens
- **Transaction Monitoring** - Verifies recent trading activity

## 🚀 Quick Start - Local Development

### 1. Prerequisites

- Python 3.7+ installed
- pip package manager
- 2GB+ free disk space (for database)
- Internet connection for API access

### 2. Installation

```bash
# Clone the repository or download the project
git clone <repository-url>
cd pythonProject

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Environment Setup (Optional)

For Telegram notifications, create a `.env` file:
```bash
TG_API_KEY=your_telegram_bot_token
TG_CHAT_ID=your_chat_id
```

### 4. Launch Methods

#### Option A: Quick Start Script (Recommended)
```bash
# Make scripts executable
chmod +x start_optimized.sh stop_services.sh

# Start everything with one command
./start_optimized.sh

# Access the dashboard at: http://localhost:8080
# Advanced dashboard at: http://localhost:8084

# Stop all services
./stop_services.sh
```

#### Option B: Manual Launch
```bash
# Terminal 1 - Start the scanner
python3 main.py
# Or use the optimized version:
python3 optimized_scanner.py

# Terminal 2 - Start the dashboard
python3 advanced_filter_dashboard.py
# Dashboard will be available at: http://localhost:8084
```

#### Option C: Background Processes
```bash
# Run scanner in background
nohup python3 main.py > scanner.log 2>&1 &

# Run dashboard in background
nohup python3 advanced_filter_dashboard.py > dashboard.log 2>&1 &

# Check processes
ps aux | grep python3

# View logs
tail -f scanner.log
tail -f dashboard.log
```

### 5. View Results

Open your browser to:
- **Basic Dashboard**: http://localhost:8080
- **Enhanced Dashboard**: http://localhost:8082
- **Advanced Filter Dashboard** (Main): http://localhost:8084

The advanced dashboard provides:
- **Real-time Filtering** - DexTools/DexScreener competitor
- **Market Cap Sorting** - Estimated market caps
- **Preset Configurations** - 5 competitive filter presets
- **Table View** - Professional data presentation

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

## 🚢 Deployment Recommendations

### Cloud Deployment Options

#### 1. VPS Deployment (Recommended for Production)

**Requirements:**
- 2 vCPUs, 4GB RAM minimum
- Ubuntu 20.04+ or similar
- 20GB+ storage for database growth

**Setup on VPS:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv nginx supervisor -y

# Clone and setup
git clone <repository-url> /opt/solana-scanner
cd /opt/solana-scanner/pythonProject
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Supervisor for auto-restart
sudo nano /etc/supervisor/conf.d/scanner.conf
```

**Supervisor Config Example:**
```ini
[program:scanner]
command=/opt/solana-scanner/pythonProject/venv/bin/python main.py
directory=/opt/solana-scanner/pythonProject
autostart=true
autorestart=true
user=ubuntu

[program:dashboard]
command=/opt/solana-scanner/pythonProject/venv/bin/python advanced_filter_dashboard.py
directory=/opt/solana-scanner/pythonProject
autostart=true
autorestart=true
user=ubuntu
```

#### 2. Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  scanner:
    build: .
    command: python main.py
    volumes:
      - ./raydium_pools.db:/app/raydium_pools.db
    restart: unless-stopped

  dashboard:
    build: .
    command: python advanced_filter_dashboard.py
    ports:
      - "8084:8084"
    volumes:
      - ./raydium_pools.db:/app/raydium_pools.db
    restart: unless-stopped
```

#### 3. Cloud Platform Deployment

**Heroku (Free Tier Available):**
```bash
# Create Procfile
echo "web: python advanced_filter_dashboard.py" > Procfile
echo "worker: python main.py" >> Procfile

# Deploy
heroku create your-scanner-app
git push heroku main
heroku ps:scale web=1 worker=1
```

**AWS EC2 / Google Cloud / DigitalOcean:**
- Use t2.medium / e2-medium / 4GB droplet minimum
- Setup with systemd services for auto-restart
- Configure security groups for port 8084

### Production Considerations

#### Security
```bash
# Use environment variables for sensitive data
export SOLANA_RPC_ENDPOINT="your-private-rpc"
export TG_API_KEY="your-telegram-key"

# Restrict dashboard access with nginx
server {
    listen 80;
    location / {
        proxy_pass http://localhost:8084;
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

#### Performance Optimization
```bash
# Database maintenance cron job
0 2 * * * sqlite3 /path/to/raydium_pools.db "VACUUM; ANALYZE;"

# Log rotation
/var/log/scanner/*.log {
    daily
    rotate 7
    compress
    missingok
}
```

#### Monitoring
```bash
# Health check endpoint
curl http://localhost:8084/api/stats

# Process monitoring
pip install prometheus-flask-exporter

# Telegram alerts for crashes
./start_with_monitoring.sh
```

### Recommended Architecture

```
┌─────────────────┐
│   Nginx/Caddy   │ ← HTTPS, Rate limiting
└────────┬────────┘
         │
┌────────▼────────┐
│  Flask Dashboard│ ← Port 8084
└────────┬────────┘
         │
┌────────▼────────┐
│  SQLite Database│ ← Consider PostgreSQL for scale
└────────┬────────┘
         │
┌────────▼────────┐
│  Scanner Process│ ← Multiple workers possible
└─────────────────┘
```

### Scaling Recommendations

1. **Database**: Migrate to PostgreSQL for better concurrency
2. **Scanner**: Run multiple scanner instances with different intervals
3. **Dashboard**: Add Redis caching for frequent queries
4. **API**: Implement rate limiting and API keys
5. **Storage**: Archive old records to S3/GCS

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