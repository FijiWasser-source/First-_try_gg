"""Technical Indicators Module - New Setup"""
import numpy as np
import pandas as pd
from config import INDICATORS


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""

    @staticmethod
    def ema(data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        return pd.Series(data).ewm(span=period, adjust=False).mean().values

    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Average True Range"""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr.values

    @staticmethod
    def keltner_channels(close: np.ndarray, high: np.ndarray, low: np.ndarray,
                        period: int = 20, multiplier: float = 2.0):
        """Keltner Channels: EMA ± multiplier × ATR"""
        ema_basis = TechnicalIndicators.ema(close, period)
        atr_vals = TechnicalIndicators.atr(high, low, close, period)

        upper = ema_basis + (multiplier * atr_vals)
        lower = ema_basis - (multiplier * atr_vals)

        return upper, ema_basis, lower

    @staticmethod
    def mfi(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray,
            period: int = 14) -> np.ndarray:
        """Money Flow Index (0-100)"""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        volume = pd.Series(volume)

        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume

        positive_flow = raw_money_flow.copy()
        negative_flow = raw_money_flow.copy()

        for i in range(1, len(close)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                negative_flow.iloc[i] = 0
            else:
                positive_flow.iloc[i] = 0

        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()

        money_ratio = positive_mf / (negative_mf + 1e-10)
        mfi = 100 - (100 / (1 + money_ratio))

        return mfi.values

    @staticmethod
    def fractal_low(low: np.ndarray, window: int = 5) -> np.ndarray:
        """5-candle Fractal Low: Low < 2 candles left AND < 2 candles right"""
        fractal = np.full_like(low, 0.0)

        for i in range(window // 2, len(low) - window // 2):
            mid = i
            is_fractal = True

            # Check 2 candles to the left
            for j in range(1, window // 2 + 1):
                if low[mid] >= low[mid - j]:
                    is_fractal = False
                    break

            # Check 2 candles to the right
            if is_fractal:
                for j in range(1, window // 2 + 1):
                    if low[mid] >= low[mid + j]:
                        is_fractal = False
                        break

            if is_fractal:
                fractal[mid] = low[mid]

        return fractal

    @staticmethod
    def fractal_high(high: np.ndarray, window: int = 5) -> np.ndarray:
        """5-candle Fractal High: High > 2 candles left AND > 2 candles right"""
        fractal = np.full_like(high, 0.0)

        for i in range(window // 2, len(high) - window // 2):
            mid = i
            is_fractal = True

            # Check 2 candles to the left
            for j in range(1, window // 2 + 1):
                if high[mid] <= high[mid - j]:
                    is_fractal = False
                    break

            # Check 2 candles to the right
            if is_fractal:
                for j in range(1, window // 2 + 1):
                    if high[mid] <= high[mid + j]:
                        is_fractal = False
                        break

            if is_fractal:
                fractal[mid] = high[mid]

        return fractal

    @classmethod
    def calculate_all(cls, ohlcv: dict) -> dict:
        """Calculate all indicators"""
        closes = ohlcv["close"]
        highs = ohlcv["high"]
        lows = ohlcv["low"]
        volumes = ohlcv.get("volume", np.ones_like(closes))

        ema20 = cls.ema(closes, INDICATORS["ema_short"])
        ema50 = cls.ema(closes, INDICATORS["ema_long"])

        kc_upper, kc_mid, kc_lower = cls.keltner_channels(
            closes, highs, lows,
            INDICATORS["keltner_basis"],
            INDICATORS["keltner_multiplier"]
        )

        mfi = cls.mfi(highs, lows, closes, volumes, INDICATORS["mfi_period"])
        fractal_lows = cls.fractal_low(lows, INDICATORS["fractal_window"])
        fractal_highs = cls.fractal_high(highs, INDICATORS["fractal_window"])
        atr_vals = cls.atr(highs, lows, closes, INDICATORS["atr_period"])

        return {
            "ema20": ema20,
            "ema50": ema50,
            "kc_upper": kc_upper,
            "kc_mid": kc_mid,
            "kc_lower": kc_lower,
            "mfi": mfi,
            "fractal_lows": fractal_lows,
            "fractal_highs": fractal_highs,
            "atr": atr_vals,
        }
