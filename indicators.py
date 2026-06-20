"""Technical Indicators Module"""
import numpy as np
import pandas as pd
from config import INDICATORS


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""

    @staticmethod
    def sma(data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        return pd.Series(data).rolling(window=period).mean().values

    @staticmethod
    def ema(data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        return pd.Series(data).ewm(span=period, adjust=False).mean().values

    @staticmethod
    def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index"""
        delta = np.diff(data)
        seed = delta[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0

        rsi = np.zeros_like(data)
        rsi[:period] = 100.0 - 100.0 / (1.0 + rs)

        for i in range(period, len(data)):
            delta = data[i] - data[i - 1]
            if delta > 0:
                up = delta
                down = 0.0
            else:
                up = 0.0
                down = -delta

            up = (up * period + up) / (period + 1)
            down = (down * period + down) / (period + 1)

            rs = up / down if down != 0 else 0
            rsi[i] = 100.0 - 100.0 / (1.0 + rs)

        return rsi

    @staticmethod
    def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = pd.Series(data).ewm(span=fast, adjust=False).mean()
        ema_slow = pd.Series(data).ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line.values, signal_line.values, histogram.values

    @staticmethod
    def bollinger_bands(data: np.ndarray, period: int = 20, std_dev: int = 2):
        """Bollinger Bands"""
        sma = pd.Series(data).rolling(window=period).mean()
        std = pd.Series(data).rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band.values, sma.values, lower_band.values

    @classmethod
    def calculate_all(cls, prices: np.ndarray) -> dict:
        """Calculate all indicators for a price series"""
        if len(prices) < INDICATORS["bb_period"]:
            return {}

        indicators = {
            "sma_short": cls.sma(prices, INDICATORS["sma_short"]),
            "sma_long": cls.sma(prices, INDICATORS["sma_long"]),
            "ema_short": cls.ema(prices, INDICATORS["ema_short"]),
            "ema_long": cls.ema(prices, INDICATORS["ema_long"]),
            "rsi": cls.rsi(prices, INDICATORS["rsi_period"]),
        }

        macd, signal, histogram = cls.macd(
            prices,
            INDICATORS["macd_fast"],
            INDICATORS["macd_slow"],
            INDICATORS["macd_signal"],
        )
        indicators["macd"] = macd
        indicators["macd_signal"] = signal
        indicators["macd_histogram"] = histogram

        upper_bb, middle_bb, lower_bb = cls.bollinger_bands(
            prices, INDICATORS["bb_period"], INDICATORS["bb_std_dev"]
        )
        indicators["bb_upper"] = upper_bb
        indicators["bb_middle"] = middle_bb
        indicators["bb_lower"] = lower_bb

        return indicators
