"""Main Trading Bot Engine"""
import logging
import time
import numpy as np
from datetime import datetime
from config import TRADING_PAIRS, TIMEFRAME, INDICATORS, STRATEGY
from indicators import TechnicalIndicators
from broker import BinanceBroker
from risk_manager import RiskManager
from notifications import NotificationManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot class"""

    def __init__(self):
        self.broker = BinanceBroker()
        self.risk_manager = RiskManager()
        self.indicators_calc = TechnicalIndicators()
        self.positions = {}  # Track open positions
        self.last_signals = {}  # Track last signal to avoid duplicates

    def fetch_price_data(self, symbol: str, limit: int = 100) -> dict:
        """Fetch OHLCV data and return OHLCV as dict"""
        klines = self.broker.get_klines(symbol, TIMEFRAME, limit)

        if not klines:
            logger.warning(f"No klines for {symbol}")
            return {}

        # klines format: [time, open, high, low, close, volume]
        opens = np.array([float(k[1]) for k in klines])
        highs = np.array([float(k[2]) for k in klines])
        lows = np.array([float(k[3]) for k in klines])
        closes = np.array([float(k[4]) for k in klines])
        volumes = np.array([float(k[7]) for k in klines])  # Quote asset volume

        return {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes
        }

    def check_volume(self, volumes: np.ndarray) -> bool:
        """Check if current volume is sufficient"""
        avg_volume = np.mean(volumes[:-1])  # Average of previous candles
        current_volume = volumes[-1]
        threshold = RISK_MANAGEMENT["min_volume_threshold"]

        return current_volume > (avg_volume * threshold)

    def generate_signals(self, symbol: str) -> dict:
        """Generate trading signals: SMA + RSI + MACD (need all 3)"""
        ohlcv = self.fetch_price_data(symbol)

        if not ohlcv or len(ohlcv["close"]) < INDICATORS["atr_period"]:
            return {"signal": "HOLD", "reason": "Insufficient data"}

        # Check volume first
        if not self.check_volume(ohlcv["volume"]):
            return {"signal": "HOLD", "reason": "Volume too low"}

        # Calculate indicators
        closes = ohlcv["close"]
        sma_short = self.indicators_calc.sma(closes, INDICATORS["sma_short"])
        sma_long = self.indicators_calc.sma(closes, INDICATORS["sma_long"])
        current_rsi = self.indicators_calc.rsi(closes, INDICATORS["rsi_period"])[-1]
        macd, macd_signal, _ = self.indicators_calc.macd(
            closes, INDICATORS["macd_fast"], INDICATORS["macd_slow"], INDICATORS["macd_signal"]
        )
        atr = self.indicators_calc.atr(ohlcv["high"], ohlcv["low"], closes, INDICATORS["atr_period"])

        current_price = closes[-1]
        current_sma_short = sma_short[-1]
        current_sma_long = sma_long[-1]
        current_macd = macd[-1]
        current_macd_signal = macd_signal[-1]
        current_atr = atr[-1]

        signal = {"signal": "HOLD", "reason": "", "price": current_price, "atr": current_atr}

        # 3 Signals: SMA + RSI + MACD (need 2 out of 3)

        # Signal 1: SMA Trend
        sma_bullish = current_sma_short > current_sma_long
        sma_bearish = not sma_bullish

        # Signal 2: RSI (not overbought/oversold)
        rsi_bullish = current_rsi < INDICATORS["rsi_overbought"]
        rsi_bearish = current_rsi > INDICATORS["rsi_oversold"]

        # Signal 3: MACD Momentum
        macd_bullish = current_macd > current_macd_signal
        macd_bearish = not macd_bullish

        # BUY: Need 2+ bullish signals
        bullish_count = sum([sma_bullish, rsi_bullish, macd_bullish])
        bearish_count = sum([sma_bearish, rsi_bearish, macd_bearish])

        if bullish_count >= 2 and symbol not in self.positions:
            signal["signal"] = "BUY"
            signal["reason"] = f"Bullish (2/3): SMA:{sma_bullish} RSI:{rsi_bullish} MACD:{macd_bullish} | ATR:{current_atr:.2f}"
            logger.info(f"{symbol} BUY Signal: {signal['reason']}")

        # SELL: Need 2+ bearish signals
        elif bearish_count >= 2 and symbol not in self.positions:
            signal["signal"] = "SELL"
            signal["reason"] = f"Bearish (2/3): SMA:{sma_bearish} RSI:{rsi_bearish} MACD:{macd_bearish} | ATR:{current_atr:.2f}"
            logger.info(f"{symbol} SELL Signal: {signal['reason']}")

        return signal

    def execute_entry(self, symbol: str, signal: dict):
        """Execute trade entry"""
        if not self.risk_manager.can_open_position():
            logger.warning(f"Cannot open position for {symbol}")
            return

        if symbol in self.positions:
            logger.info(f"Position already open for {symbol}")
            return

        try:
            entry_price = signal["price"]
            atr = signal.get("atr", 500)  # Default 500 if not available

            side = "BUY" if signal["signal"] == "BUY" else "SELL"

            # Calculate SL/TP based on ATR
            if RISK_MANAGEMENT["use_atr"]:
                sl_atr_sl = RISK_MANAGEMENT["atr_sl_multiplier"]
                tp_atr_tp = RISK_MANAGEMENT["atr_tp_multiplier"]

                if side == "BUY":
                    sl = entry_price - (atr * sl_atr_sl)
                    tp = entry_price + (atr * tp_atr_tp)
                else:  # SELL
                    sl = entry_price + (atr * sl_atr_sl)
                    tp = entry_price - (atr * tp_atr_tp)
            else:
                # Fallback to percentage-based
                sl = self.risk_manager.calculate_stop_loss(entry_price, side)
                tp = self.risk_manager.calculate_take_profit(entry_price, side)

            # Calculate position size based on risk (1% rule)
            qty = self.risk_manager.calculate_position_size(entry_price, sl)

            if qty == 0:
                logger.warning(f"Invalid position size for {symbol}")
                return

            # Place order
            order = self.broker.place_order(
                symbol,
                side,
                "MARKET",
                qty,
            )

            if order and "orderId" in order:
                self.positions[symbol] = {
                    "entry_price": entry_price,
                    "quantity": qty,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "side": side,
                    "entry_time": datetime.now(),
                }

                self.risk_manager.on_position_opened()

                # Set SL/TP
                self.broker.set_stop_loss_take_profit(symbol, sl, tp)

                # Send notification
                NotificationManager.send_trade_alert(
                    side,
                    symbol,
                    entry_price,
                    qty,
                    sl,
                    tp,
                    signal["reason"],
                )

                logger.info(f"✅ Entry: {symbol} {side} @ ${entry_price:.2f}")

        except Exception as e:
            logger.error(f"Entry execution failed: {e}")

    def check_exit_conditions(self, symbol: str):
        """Check if position should be closed"""
        if symbol not in self.positions:
            return

        try:
            position = self.positions[symbol]
            current_price = self.broker.get_latest_price(symbol)

            if current_price == 0:
                return

            entry_price = position["entry_price"]
            qty = position["quantity"]
            side = position["side"]

            exit_reason = None

            if side == "Buy":
                if current_price >= position["take_profit"]:
                    exit_reason = "Take Profit"
                elif current_price <= position["stop_loss"]:
                    exit_reason = "Stop Loss"

            else:  # Sell
                if current_price <= position["take_profit"]:
                    exit_reason = "Take Profit"
                elif current_price >= position["stop_loss"]:
                    exit_reason = "Stop Loss"

            if exit_reason:
                close_side = "SELL" if side == "BUY" else "BUY"
                order = self.broker.close_position(symbol, qty, close_side)

                if order:
                    pnl = (current_price - entry_price) * qty
                    if side == "Sell":
                        pnl = -pnl

                    self.risk_manager.on_position_closed(pnl)

                    NotificationManager.send_position_closed(
                        symbol,
                        entry_price,
                        current_price,
                        qty,
                        pnl,
                        exit_reason,
                    )

                    del self.positions[symbol]
                    logger.info(
                        f"❌ Exit: {symbol} {exit_reason} @ ${current_price:.2f} | P&L: ${pnl:.2f}"
                    )

        except Exception as e:
            logger.error(f"Exit check failed for {symbol}: {e}")

    def run(self):
        """Main bot loop"""
        logger.info("🤖 Trading Bot Started")

        try:
            while True:
                try:
                    for symbol in TRADING_PAIRS:
                        # Check exits first
                        self.check_exit_conditions(symbol)

                        # Generate signals
                        signal = self.generate_signals(symbol)

                        # Execute entry if signal
                        if signal["signal"] in ["BUY", "SELL"]:
                            logger.info(f"{symbol}: {signal['reason']}")
                            self.execute_entry(symbol, signal)

                    # Log daily stats every hour
                    stats = self.risk_manager.get_daily_stats()
                    logger.info(f"Daily Stats: P&L=${stats['daily_pnl']:.2f} | "
                               f"Loss=${stats['daily_loss']:.2f} | "
                               f"Positions={stats['open_positions']}")

                    # Sleep before next iteration
                    time.sleep(60)  # Check every minute

                except KeyboardInterrupt:
                    logger.info("Bot stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in bot loop: {e}")
                    time.sleep(5)

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            NotificationManager.send_daily_stats(self.risk_manager.get_daily_stats())


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
