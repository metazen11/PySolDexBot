from typing import Dict, Optional
import pandas as pd
from .base import BaseStrategy
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class MomentumStrategy(BaseStrategy):
    def __init__(self, config: Dict):
        super().__init__(config)
        # Load strategy parameters from config
        self.buy_adx_threshold = config.get('buy_adx_threshold', 25)
        self.buy_rsi_threshold = config.get('buy_rsi_threshold', 30)
        self.sell_rsi_threshold = config.get('sell_rsi_threshold', 70)

    async def should_enter(self, df: pd.DataFrame) -> bool:
        """Check entry conditions"""
        try:
            # Get the latest candle
            last_candle = df.iloc[-1]

            # Market condition checks
            market_condition = (
                not self._is_high_volatility(df) and
                last_candle['adx'] > self.buy_adx_threshold and
                last_candle['rsi'] < self.buy_rsi_threshold and
                last_candle['momentum'] > 0
            )

            # Volume confirmation
            volume_condition = (
                last_candle['volume'] > df['volume'].rolling(window=20).mean().iloc[-1]
            )

            # Trend confirmation
            trend_condition = (
                last_candle['ema_9'] > last_candle['ema_21'] and
                last_candle['close'] > last_candle['vwap']
            )

            return market_condition and volume_condition and trend_condition

        except Exception as e:
            logger.error(f'Error in should_enter: {e}')
            return False

    async def should_exit(self, df: pd.DataFrame) -> bool:
        """Check exit conditions"""
        try:
            last_candle = df.iloc[-1]

            # Exit conditions
            return (
                last_candle['rsi'] > self.sell_rsi_threshold or
                last_candle['momentum'] <= 0 or
                self._is_high_volatility(df)
            )

        except Exception as e:
            logger.error(f'Error in should_exit: {e}')
            return True  # Exit on error to be safe

    def _is_high_volatility(self, df: pd.DataFrame) -> bool:
        """Check if current volatility is too high"""
        try:
            # Calculate ATR-based volatility
            atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            current_volatility = atr.iloc[-1] / df['close'].iloc[-1]
            return current_volatility > self.config.get('max_volatility', 0.03)

        except Exception as e:
            logger.error(f'Error in _is_high_volatility: {e}')
            return True  # Assume high volatility on error

    async def get_position_size(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate position size based on risk parameters"""
        try:
            # Get available balance (implement this based on your wallet integration)
            balance = await self._get_available_balance()
            
            # Calculate position size based on risk
            risk_per_trade = self.config.get('risk_per_trade', 0.02)  # 2% risk per trade
            position_size = balance * risk_per_trade
            
            # Apply maximum position size limit
            max_position = balance * self.config.get('max_position_size', 0.1)
            return min(position_size, max_position)

        except Exception as e:
            logger.error(f'Error calculating position size: {e}')
            return None