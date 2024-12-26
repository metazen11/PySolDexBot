from typing import Dict, List
from datetime import datetime, timedelta

class TimeframeUtils:
    TIMEFRAME_MINUTES = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1d': 1440
    }

    @staticmethod
    def get_timeframe_minutes(timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        return TimeframeUtils.TIMEFRAME_MINUTES.get(timeframe, 5)

    @staticmethod
    def get_candle_start_time(timestamp: datetime, timeframe: str) -> datetime:
        """Get the start time of the current candle"""
        minutes = TimeframeUtils.get_timeframe_minutes(timeframe)
        return timestamp - timedelta(minutes=timestamp.minute % minutes,
                                   seconds=timestamp.second,
                                   microseconds=timestamp.microsecond)

    @staticmethod
    def get_timeframe_delta(timeframe: str) -> timedelta:
        """Get timedelta object for timeframe"""
        minutes = TimeframeUtils.get_timeframe_minutes(timeframe)
        return timedelta(minutes=minutes)