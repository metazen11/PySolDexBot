"""Constants for price monitoring configuration"""

# Default API settings
DEFAULT_UPDATE_INTERVAL = 60  # seconds
DEFAULT_JUPITER_URL = 'https://price.jup.ag/v4/price'
DEFAULT_USDC_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'

# Rate limiting defaults
DEFAULT_RATE_LIMIT_CALLS = 100  # requests
DEFAULT_RATE_LIMIT_PERIOD = 60  # seconds

# Price validation settings
DEFAULT_PRICE_CHANGE_THRESHOLD = 1.0  # percent
DEFAULT_MAX_PRICE_DEVIATION = 30.0  # percent
DEFAULT_MIN_PRICE_VALUE = 1e-12  # minimum valid price

# HTTP client settings
DEFAULT_REQUEST_TIMEOUT = 10  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_MIN_WAIT = 4  # seconds
DEFAULT_RETRY_MAX_WAIT = 10  # seconds

# Batch processing
MAX_BATCH_SIZE = 100  # maximum tokens per request