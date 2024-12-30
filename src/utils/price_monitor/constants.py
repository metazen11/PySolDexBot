"""Constants for price monitoring configuration"""

# Default API settings
DEFAULT_UPDATE_INTERVAL = 60  # seconds between price checks
DEFAULT_JUPITER_URL = 'https://price.jup.ag/v4/price'
DEFAULT_USDC_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'

# Rate limiting defaults
DEFAULT_RATE_LIMIT_CALLS = 100  # requests per period
DEFAULT_RATE_LIMIT_PERIOD = 60  # period in seconds

# Price validation settings
DEFAULT_PRICE_CHANGE_THRESHOLD = 1.0  # minimum % change to trigger alert
DEFAULT_MAX_PRICE_DEVIATION = 30.0  # maximum % change allowed between updates
DEFAULT_MIN_PRICE_VALUE = 1e-12  # minimum valid price value

# HTTP client settings
DEFAULT_REQUEST_TIMEOUT = 10  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_MIN_WAIT = 4  # minimum seconds between retries
DEFAULT_RETRY_MAX_WAIT = 10  # maximum seconds between retries

# Batch processing
MAX_BATCH_SIZE = 100  # maximum tokens per request

# Database settings
PRICE_HISTORY_DAYS = 30  # days to keep price history
MIN_DATA_POINTS = 24  # minimum data points for analysis

# Error thresholds
MAX_CONSECUTIVE_ERRORS = 3  # maximum consecutive errors before alert
MAX_ERROR_RATE = 0.1  # maximum acceptable error rate (10%)

# Volume thresholds
MIN_24H_VOLUME = 10000  # minimum 24h volume in USDC
MIN_LIQUIDITY = 50000   # minimum liquidity in USDC

# Price impact thresholds
MAX_PRICE_IMPACT = 0.05  # maximum acceptable price impact (5%)
MIN_TICK_SIZE = 1e-6    # minimum price increment

# Rate limiting specific to Jupiter API
JUPITER_RATE_LIMIT = {
    'DEFAULT': {
        'calls': 100,
        'period': 60
    },
    'PREMIUM': {
        'calls': 300,
        'period': 60
    }
}

# Status codes
STATUS_CODES = {
    'ACTIVE': 'active',
    'PAUSED': 'paused',
    'ERROR': 'error',
    'RATE_LIMITED': 'rate_limited',
    'INVALID_DATA': 'invalid_data'
}

# Error categories
ERROR_TYPES = {
    'API_ERROR': 'api_error',
    'VALIDATION_ERROR': 'validation_error',
    'RATE_LIMIT_ERROR': 'rate_limit_error',
    'NETWORK_ERROR': 'network_error',
    'DATA_ERROR': 'data_error'
}

# Token metadata fields
REQUIRED_METADATA = [
    'mint_address',
    'symbol',
    'decimals'
]

# Price update fields
REQUIRED_PRICE_FIELDS = [
    'price',
    'timestamp'
]

# Response structure constants
RESPONSE_FIELDS = {
    'PRICE': 'price',
    'VOLUME': 'volume24h',
    'LIQUIDITY': 'liquidity',
    'TIMESTAMP': 'timestamp',
    'METADATA': 'metadata'
}
