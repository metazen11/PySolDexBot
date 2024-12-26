import pandas as pd
import numpy as np
import talib
from typing import Dict

class TechnicalIndicators:
    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index"""
        return talib.ADX(high, low, close, timeperiod=period)

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

    @staticmethod
    def calculate_momentum(close: pd.Series, period: int = 10) -> pd.Series:
        """Calculate Momentum"""
        return talib.MOM(close, timeperiod=period)

    @staticmethod
    def calculate_all(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Calculate all technical indicators"""
        df = df.copy()

        # ADX
        df['adx'] = TechnicalIndicators.calculate_adx(
            df['high'], df['low'], df['close'], 
            period=config.get('adx_period', 14)
        )

        # VWAP
        df['vwap'] = TechnicalIndicators.calculate_vwap(df)

        # Momentum
        df['momentum'] = TechnicalIndicators.calculate_momentum(
            df['close'], 
            period=config.get('momentum_period', 10)
        )

        # RSI
        df['rsi'] = talib.RSI(df['close'], timeperiod=config.get('rsi_period', 14))

        # EMAs
        for period in [9, 21, 50, 200]:
            df[f'ema_{period}'] = talib.EMA(df['close'], timeperiod=period)

        return df