"""
Configuration file for Solana Token Security Scanner
Optimized for fastest data sources and best security filtering
"""

import os

# ===== DATA SOURCE OPTIMIZATION =====

# Primary data sources (fastest to slowest)
RAYDIUM_API_ENDPOINTS = [
    'https://api.raydium.io/v2/main/pairs',  # Primary - fastest
    'https://api-v3.raydium.io/pools/info/list',  # Backup - newer API
]

# Solana RPC endpoints (ordered by speed)
SOLANA_RPC_ENDPOINTS = [
    'https://solana-api.projectserum.com',  # Fastest free RPC
    'https://api.mainnet-beta.solana.com',  # Solana foundation
    'https://rpc.ankr.com/solana',  # Ankr backup
]

# Transaction data sources
TRANSACTION_API_ENDPOINTS = [
    'https://public-api.solscan.io/account/transactions',  # Primary
    'https://api.helius.dev/v0/addresses/{address}/transactions',  # Backup (needs API key)
]

# ===== SECURITY FILTERING OPTIMIZATION =====

class SecurityFilters:
    # Liquidity thresholds (USD)
    MIN_LIQUIDITY_DISCOVERY = 500      # Minimum to show in "Recent"
    MIN_LIQUIDITY_SAFE = 10000         # Minimum for "Safe" category
    MIN_LIQUIDITY_PREMIUM = 50000      # Premium tier filtering

    # Volume thresholds (USD, 24h)
    MIN_VOLUME_DISCOVERY = 0           # Any volume for discovery
    MIN_VOLUME_SAFE = 500              # Minimum for safe category
    MIN_VOLUME_PREMIUM = 2000          # Premium tier filtering

    # Time windows
    DISCOVERY_WINDOW_HOURS = 2         # Show discoveries from last 2 hours
    SAFE_WINDOW_HOURS = 6              # Safe tokens from last 6 hours
    TRANSACTION_CHECK_HOURS = 1        # Check transactions in last hour

    # Trading activity filters
    MIN_RECENT_TRADES_MINUTES = 30     # Must have trades in last 30 minutes
    MIN_TRADES_PER_HOUR = 5            # Minimum trades per hour for active status
    VOLUME_CONSISTENCY_HOURS = 2       # Check volume consistency over 2 hours

    # Security checks
    CHECK_MINT_AUTHORITY = True        # Flag tokens with mint authority
    CHECK_FREEZE_AUTHORITY = True      # Flag tokens with freeze authority
    BLOCK_PUMP_TOKENS = False          # Don't block pump.fun tokens (they're safer)
    REQUIRE_RECENT_ACTIVITY = True     # Require recent transactions

    # Advanced filters
    MAX_HOLDER_CONCENTRATION = 0.5     # Max % held by top holder
    MIN_HOLDERS_COUNT = 10             # Minimum number of holders
    MIN_MARKET_CAP = 50000            # Minimum market cap (USD)

# ===== PERFORMANCE OPTIMIZATION =====

class PerformanceConfig:
    # Scanning intervals
    FAST_SCAN_INTERVAL = 30           # Fast mode: every 30 seconds
    NORMAL_SCAN_INTERVAL = 60         # Normal mode: every 60 seconds
    SLOW_SCAN_INTERVAL = 120          # Slow mode: every 2 minutes

    # API rate limiting
    RAYDIUM_REQUESTS_PER_MINUTE = 120  # Conservative rate limit
    SOLSCAN_REQUESTS_PER_MINUTE = 60   # Solscan API limit
    SOLANA_RPC_REQUESTS_PER_MINUTE = 100

    # Database optimization
    BATCH_SIZE = 100                   # Process pools in batches
    MAX_DB_CONNECTIONS = 5             # Connection pool size
    DB_VACUUM_INTERVAL_HOURS = 24      # Vacuum database daily

    # Memory management
    MAX_POOLS_IN_MEMORY = 10000       # Limit memory usage
    CLEANUP_OLD_RECORDS_DAYS = 7      # Keep records for 7 days

# ===== TELEGRAM NOTIFICATIONS =====

class TelegramConfig:
    BOT_TOKEN = os.getenv('TG_API_KEY')
    CHAT_ID = os.getenv('TG_CHAT_ID')

    # Notification thresholds
    NOTIFY_LIQUIDITY_THRESHOLD = 25000  # Notify for high liquidity tokens
    NOTIFY_VOLUME_THRESHOLD = 5000      # Notify for high volume tokens
    MAX_NOTIFICATIONS_PER_HOUR = 10     # Rate limit notifications

# ===== ADVANCED SECURITY CHECKS =====

class AdvancedSecurity:
    """Advanced security analysis configuration"""

    # Contract analysis
    CHECK_CONTRACT_VERIFICATION = True  # Prefer verified contracts
    CHECK_RENOUNCED_OWNERSHIP = True   # Check if ownership renounced
    ANALYZE_TOKEN_DISTRIBUTION = True   # Analyze holder distribution

    # Market analysis
    CHECK_LIQUIDITY_LOCK = True        # Check if liquidity is locked
    MIN_LIQUIDITY_LOCK_DAYS = 30      # Minimum lock period
    CHECK_TEAM_TOKENS = True          # Analyze team token allocation

    # Social signals
    REQUIRE_SOCIAL_PRESENCE = False    # Require Twitter/Discord
    CHECK_COINGECKO_LISTING = False   # Check CoinGecko presence

    # Price analysis
    MAX_PRICE_VOLATILITY_24H = 0.5    # Max 50% price swing
    MIN_PRICE_STABILITY_HOURS = 6     # Minimum stable price period

# ===== DEFAULT CONFIGURATION =====

# Use environment variables or defaults
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', PerformanceConfig.NORMAL_SCAN_INTERVAL))
DATABASE_FILE = os.getenv('DATABASE_FILE', 'raydium_pools.db')
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 8080))

# Security mode selection
SECURITY_MODE = os.getenv('SECURITY_MODE', 'normal')  # 'conservative', 'normal', 'aggressive'

if SECURITY_MODE == 'conservative':
    SecurityFilters.MIN_LIQUIDITY_SAFE = 50000
    SecurityFilters.MIN_VOLUME_SAFE = 2000
elif SECURITY_MODE == 'aggressive':
    SecurityFilters.MIN_LIQUIDITY_SAFE = 5000
    SecurityFilters.MIN_VOLUME_SAFE = 100