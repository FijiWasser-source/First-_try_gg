"""Main Trading Bot Engine"""
import logging
import time
import numpy as np
from datetime import datetime
from config import TRADING_PAIRS, TIMEFRAME, INDICATORS, STRATEGY
from indicators import TechnicalIndicators
from broker import ByBitBroker
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
        self.broker = ByBitBroker()
        self.risk_manager = RiskManager()
        self.indicators_calc = TechnicalIndicators()
        self.positions = {}  # Track open positions
        self.last_signals = {}  # Track last signal to avoid duplicates

    def fetch_price_data(self, symbol: str, limit: int = 100) -> np.ndarray:
        """Fetch OHLCV data and return closing prices"""
        klines = self.broker.get_klines(symbol, TIMEFRAME, limit)

        if not klines:
            logger.warning(f"No klines for {symbol}")
            return np.array([])

        # klines format: [time, open, high, low, close, volume]
        closes = np.array([float(k[4]) for k in klines])
        return closes

    def generate_signals(self, symbol: str) -> dict:
        """Generate trading signals based on technical indicators"""
        prices = self.fetch_price_data(symbol)

        if len(prices) < INDICATORS["bb_period"]:
            return {"signal": "HOLD", "reason": "Insufficient data"}

        indicators = self.indicators_calc.calculate_all(prices)

        if not indicators:
            return {"signal": "HOLD", "reason": "Indicator calculation failed"}

        current_price = prices[-1]
        current_rsi = indicators["rsi"][-1]
        current_macd = indicators["macd"][-1]
        current_signal = indicators["macd_signal"][-1]
        sma_short = indicators["sma_short"][-1]
        sma_long = indicators["sma_long"][-1]

        signal = {"signal": "HOLD", "reason": "", "price": current_price}

        # Strategy: Moving Average Crossover + RSI confirmation
        if sma_short > sma_long:
            if current_rsi < INDICATORS["rsi_overbought"]:
                if current_macd > current_signal:
                    signal["signal"] = "BUY"
                    signal["reason"] = f"MA cross up, RSI: {current_rsi:.2f}, MACD bullish"

        elif sma_short < sma_long:
            if current_rsi > INDICATORS["rsi_oversold"]:
                if current_macd < current_signal:
                    signal["signal"] = "SELL"
                    signal["reason"] = f"MA cross down, RSI: {current_rsi:.2f}, MACD bearish"

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
            qty = self.risk_manager.calculate_position_size(entry_price, 10000)

            if qty == 0:
                logger.warning(f"Invalid position size for {symbol}")
                return

            side = "Buy" if signal["signal"] == "BUY" else "Sell"
            sl = self.risk_manager.calculate_stop_loss(
                entry_price,
                "LONG" if signal["signal"] == "BUY" else "SHORT"
            )
            tp = self.risk_manager.calculate_take_profit(
                entry_price,
                "LONG" if signal["signal"] == "BUY" else "SHORT"
            )

            # Place order
            order = self.broker.place_order(
                symbol,
                side,
                "Market",
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
                close_side = "Sell" if side == "Buy" else "Buy"
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
