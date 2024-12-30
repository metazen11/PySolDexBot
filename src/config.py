import os
from typing import Dict
from dotenv import load_dotenv

def load_config() -> Dict:
    """Load configuration from environment variables
    
    Returns:
        Dict: Configuration dictionary
    """
    load_dotenv()
    
    # Database configuration
    db_config = {
        'database_url': f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
                       f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
        'pool_size': int(os.getenv('DB_POOL_SIZE', 5)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 10)),
        'sql_echo': os.getenv('SQL_ECHO', '').lower() == 'true'
    }
    
    # Price monitoring settings
    price_config = {
        'price_check_interval': int(os.getenv('PRICE_CHECK_INTERVAL', 60)),
        'price_change_threshold': float(os.getenv('PRICE_CHANGE_THRESHOLD', 1.0)),
        'min_liquidity_usd': float(os.getenv('MIN_LIQUIDITY_USD', 50000)),
        'min_volume_24h': float(os.getenv('MIN_VOLUME_24H', 10000))
    }
    
    # Holder requirements
    holder_config = {
        'min_holders': int(os.getenv('MIN_HOLDERS', 100)),
        'min_holder_growth': float(os.getenv('MIN_HOLDER_GROWTH', 5.0)),
        'min_active_ratio': float(os.getenv('MIN_ACTIVE_RATIO', 0.1))
    }
    
    # API settings
    api_config = {
        'solscan_api_key': os.getenv('SOLSCAN_API_KEY'),
        'helius_api_key': os.getenv('HELIUS_API_KEY'),
        'jupiter_url': os.getenv('JUPITER_API_URL', 'https://price.jup.ag/v4/price')
    }
    
    return {
        **db_config,
        **price_config,
        **holder_config,
        **api_config
    }

# Example .env file structure
ENV_EXAMPLE = """
# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=soldexbot
DB_USER=your_user
DB_PASSWORD=your_password
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
SQL_ECHO=false

# Price monitoring
PRICE_CHECK_INTERVAL=60
PRICE_CHANGE_THRESHOLD=1.0
MIN_LIQUIDITY_USD=50000
MIN_VOLUME_24H=10000

# Holder requirements
MIN_HOLDERS=100
MIN_HOLDER_GROWTH=5.0
MIN_ACTIVE_RATIO=0.1

# API keys
SOLSCAN_API_KEY=
HELIUS_API_KEY=
JUPITER_API_URL=https://price.jup.ag/v4/price
"""
