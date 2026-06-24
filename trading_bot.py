"""Main Trading Bot Engine - Advanced Fractal-Based Strategy"""
import logging
import sys
import time
import numpy as np
from datetime import datetime
from config import TRADING_PAIRS, TIMEFRAME, INDICATORS, RISK_MANAGEMENT
from indicators import TechnicalIndicators
from broker import BinanceBroker
from risk_manager import RiskManager
from notifications import NotificationManager

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# File handler
file_handler = logging.FileHandler("trading_bot.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Console handler for INFO/DEBUG (stdout - blue)
info_handler = logging.StreamHandler(sys.stdout)
info_handler.setLevel(logging.DEBUG)
info_handler.setFormatter(formatter)
info_handler.addFilter(lambda record: record.levelno <= logging.INFO)

# Console handler for WARNING/ERROR (stderr - red)
error_handler = logging.StreamHandler(sys.stderr)
error_handler.setLevel(logging.WARNING)
error_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(info_handler)
logger.addHandler(error_handler)

# Suppress verbose DEBUG logs from external libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


class TradingBot:
    """Main trading bot class - Fractal + MFI + Keltner Strategy"""

    def __init__(self):
        self.broker = BinanceBroker()
        self.risk_manager = RiskManager()
        self.indicators_calc = TechnicalIndicators()
        self.positions = {}  # Track open positions

    def fetch_price_data(self, symbol: str, limit: int = 100) -> dict:
        """Fetch OHLCV data"""
        klines = self.broker.get_klines(symbol, TIMEFRAME, limit)

        if not klines:
            logger.warning(f"No klines for {symbol}")
            return {}

        opens = np.array([float(k[1]) for k in klines])
        highs = np.array([float(k[2]) for k in klines])
        lows = np.array([float(k[3]) for k in klines])
        closes = np.array([float(k[4]) for k in klines])
        volumes = np.array([float(k[7]) for k in klines])

        return {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes
        }

    def check_volume(self, volumes: np.ndarray) -> bool:
        """Check if current volume is sufficient"""
        avg_volume = np.mean(volumes[:-1])
        current_volume = volumes[-1]
        threshold = RISK_MANAGEMENT.get("min_volume_threshold", 0.8)
        return current_volume > (avg_volume * threshold)

    def find_confirmed_fractal_low(self, fractal_lows: np.ndarray, current_price: float,
                                   lookback: int = 10) -> float:
        """Find most recent confirmed fractal low below current price"""
        # Start from -3 (skip last 2 unconfirmed candles)
        start_idx = max(0, len(fractal_lows) - lookback - 2)
        end_idx = len(fractal_lows) - 2

        for i in range(end_idx, start_idx - 1, -1):
            if fractal_lows[i] > 0 and fractal_lows[i] < current_price:
                return fractal_lows[i]

        return None

    def find_confirmed_fractal_high(self, fractal_highs: np.ndarray, current_price: float,
                                    lookback: int = 10) -> float:
        """Find most recent confirmed fractal high above current price"""
        start_idx = max(0, len(fractal_highs) - lookback - 2)
        end_idx = len(fractal_highs) - 2

        for i in range(end_idx, start_idx - 1, -1):
            if fractal_highs[i] > 0 and fractal_highs[i] > current_price:
                return fractal_highs[i]

        return None

    def check_mfi_cross_long(self, mfi: np.ndarray, lookback: int = 3) -> bool:
        """Check if MFI crossed above 45 (was below, now above)"""
        if len(mfi) < lookback + 1:
            return False

        current_mfi = mfi[-1]
        if current_mfi <= INDICATORS["mfi_long_threshold"]:
            return False

        # Check last 3 candles were below 45
        for i in range(1, lookback + 1):
            if mfi[-1 - i] > INDICATORS["mfi_long_threshold"]:
                return False

        return True

    def check_mfi_cross_short(self, mfi: np.ndarray, lookback: int = 3) -> bool:
        """Check if MFI crossed below 55 (was above, now below)"""
        if len(mfi) < lookback + 1:
            return False

        current_mfi = mfi[-1]
        if current_mfi >= INDICATORS["mfi_short_threshold"]:
            return False

        # Check last 3 candles were above 55
        for i in range(1, lookback + 1):
            if mfi[-1 - i] < INDICATORS["mfi_short_threshold"]:
                return False

        return True

    def generate_signals(self, symbol: str) -> dict:
        """Generate trading signals - 3 conditions must be met"""
        ohlcv = self.fetch_price_data(symbol)

        if not ohlcv or len(ohlcv["close"]) < 50:
            return {"signal": "HOLD", "reason": "Insufficient data"}

        # Calculate all indicators
        indicators = self.indicators_calc.calculate_all(ohlcv)

        current_close = ohlcv["close"][-1]
        current_high = ohlcv["high"][-1]
        current_low = ohlcv["low"][-1]
        ema20 = indicators["ema20"][-1]
        ema50 = indicators["ema50"][-1]
        kc_mid = indicators["kc_mid"][-1]
        mfi = indicators["mfi"]
        atr = indicators["atr"][-1]

        signal = {"signal": "HOLD", "reason": "", "price": current_close, "atr": atr}

        # LONG SIGNAL - 3 conditions must be met
        if symbol not in self.positions:
            # Condition 1: EMA(20) > EMA(50)
            ema_bullish = ema20 > ema50

            # Condition 2: Low touches/breaches Keltner mid, Close stays above EMA(50)
            low_touches_kc = current_low <= kc_mid
            close_above_ema50 = current_close > ema50

            # Condition 3: MFI cross above 40
            mfi_cross = self.check_mfi_cross_long(mfi, INDICATORS["mfi_lookback"])

            if ema_bullish and low_touches_kc and close_above_ema50 and mfi_cross:
                signal["signal"] = "BUY"
                signal["reason"] = f"LONG: EMA bullish, Low touches KC, MFI cross @ {current_close:.4f}"
                logger.info(f"{symbol} BUY Signal: {signal['reason']}")

        # SHORT SIGNAL - 3 conditions must be met (mirrored)
        if symbol not in self.positions:
            # Condition 1: EMA(20) < EMA(50)
            ema_bearish = ema20 < ema50

            # Condition 2: High touches/breaches Keltner mid, Close stays below EMA(50)
            high_touches_kc = current_high >= kc_mid
            close_below_ema50 = current_close < ema50

            # Condition 3: MFI cross below 50
            mfi_cross = self.check_mfi_cross_short(mfi, INDICATORS["mfi_lookback"])

            if ema_bearish and high_touches_kc and close_below_ema50 and mfi_cross:
                signal["signal"] = "SELL"
                signal["reason"] = f"SHORT: EMA bearish, High touches KC, MFI cross @ {current_close:.4f}"
                logger.info(f"{symbol} SELL Signal: {signal['reason']}")

        return signal

    def execute_entry(self, symbol: str, signal: dict):
        """Execute trade entry with Limit Order SL/TP"""
        if not self.risk_manager.can_open_position():
            logger.warning(f"Cannot open position for {symbol}")
            return

        if symbol in self.positions:
            logger.info(f"Position already open for {symbol}")
            return

        try:
            entry_price = signal["price"]
            side = "BUY" if signal["signal"] == "BUY" else "SELL"

            # Calculate SL/TP based on percentage (3% SL, 7.5% TP)
            if side == "BUY":
                sl = entry_price * 0.97  # 3% below entry
                tp = entry_price * 1.075  # 7.5% above entry
            else:  # SELL
                sl = entry_price * 1.03  # 3% above entry
                tp = entry_price * 0.925  # 7.5% below entry

            # Calculate position size based on risk
            qty = self.risk_manager.calculate_position_size(entry_price, sl)

            if qty == 0:
                logger.warning(f"Invalid position size for {symbol}")
                return

            # Place entry order (LIMIT with 1% buffer for guaranteed execution on Testnet)
            entry_limit_price = entry_price * 1.01 if side == "BUY" else entry_price * 0.99
            order = self.broker.place_order(symbol, side, "LIMIT", qty, price=entry_limit_price)
            logger.debug(f"Entry order result: {order}")

            if not order or "orderId" not in order:
                logger.error(f"Entry order failed for {symbol}, skipping SL/TP placement")
                return

            logger.info(f"Entry order successful, placing SL/TP orders...")
            # Place SL/TP as Limit Orders (separate orders for reliability)
            sl_tp_orders = self.broker.place_sl_tp_orders(
                symbol, qty, side, stop_loss=sl, take_profit=tp
            )

            # Safely get order IDs
            sl_order = sl_tp_orders.get("sl_order") if sl_tp_orders else None
            tp_order = sl_tp_orders.get("tp_order") if sl_tp_orders else None
            sl_order_id = sl_order.get("orderId") if sl_order and isinstance(sl_order, dict) else None
            tp_order_id = tp_order.get("orderId") if tp_order and isinstance(tp_order, dict) else None

            self.positions[symbol] = {
                "entry_price": entry_price,
                "quantity": qty,
                "stop_loss": sl,
                "take_profit": tp,
                "side": side,
                "entry_time": datetime.now(),
                "entry_order_id": order.get("orderId"),
                "sl_order_id": sl_order_id,
                "tp_order_id": tp_order_id,
            }

            self.risk_manager.on_position_opened()

            # Send notification with signal reason
            NotificationManager.send_trade_alert(
                side, symbol, entry_price, qty, sl, tp,
                signal.get("reason", "Trade signal triggered")
            )

            logger.info(f"✅ Entry: {symbol} {side} @ ${entry_price:.2f} | SL:${sl:.2f} TP:${tp:.2f} | Qty:{qty}")

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
            sl = position["stop_loss"]
            tp = position["take_profit"]

            exit_reason = None

            if side == "BUY":
                if current_price >= tp:
                    exit_reason = "Take Profit"
                elif current_price <= sl:
                    exit_reason = "Stop Loss"

            else:  # SELL
                if current_price <= tp:
                    exit_reason = "Take Profit"
                elif current_price >= sl:
                    exit_reason = "Stop Loss"

            if exit_reason:
                close_side = "SELL" if side == "BUY" else "BUY"
                order = self.broker.close_position(symbol, qty, close_side)

                if order:
                    pnl = (current_price - entry_price) * qty
                    if side == "SELL":
                        pnl = -pnl

                    self.risk_manager.on_position_closed(pnl)

                    NotificationManager.send_position_closed(
                        symbol, entry_price, current_price, qty, pnl, exit_reason
                    )

                    del self.positions[symbol]
                    logger.info(
                        f"❌ Exit: {symbol} {exit_reason} @ ${current_price:.2f} | P&L: ${pnl:.2f}"
                    )

                    stats = self.risk_manager.get_daily_stats()
                    logger.info(f"Daily Stats: P&L=${stats['daily_pnl']:.2f} | "
                               f"Loss=${stats['daily_loss']:.2f} | "
                               f"Positions={stats['open_positions']}")

        except Exception as e:
            logger.error(f"Exit check failed for {symbol}: {e}")

    def run(self):
        """Main bot loop"""
        logger.info("🤖 Trading Bot Started - Fractal Strategy")

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
                            self.execute_entry(symbol, signal)

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
