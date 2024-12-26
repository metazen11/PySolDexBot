import os
from typing import Dict
from dotenv import load_dotenv

def load_config() -> Dict:
    """Load configuration from environment variables"""
    load_dotenv()

    return {
        # Network settings
        'rpc_url': os.getenv('SOLANA_RPC_URL'),
        'network': os.getenv('NETWORK', 'mainnet'),

        # Wallet settings
        'wallet_private_key': os.getenv('WALLET_PRIVATE_KEY'),

        # Trading parameters
        'slippage': float(os.getenv('SLIPPAGE', '0.5')),
        'max_slippage': float(os.getenv('MAX_SLIPPAGE', '1.0')),

        # Technical analysis parameters
        'timeframe': os.getenv('TIMEFRAME', '5m'),
        'adx_period': int(os.getenv('ADX_PERIOD', '14')),
        'rsi_period': int(os.getenv('RSI_PERIOD', '14')),
        'momentum_period': int(os.getenv('MOMENTUM_PERIOD', '10')),

        # Strategy parameters
        'buy_adx_threshold': float(os.getenv('BUY_ADX_THRESHOLD', '25')),
        'buy_rsi_threshold': float(os.getenv('BUY_RSI_THRESHOLD', '30')),
        'sell_rsi_threshold': float(os.getenv('SELL_RSI_THRESHOLD', '70')),

        # Risk management
        'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '0.1')),
        'stop_loss_percentage': float(os.getenv('STOP_LOSS_PERCENTAGE', '2.0')),
        'take_profit_percentage': float(os.getenv('TAKE_PROFIT_PERCENTAGE', '4.0')),

        # Bot settings
        'check_interval': int(os.getenv('CHECK_INTERVAL', '60'))
    }