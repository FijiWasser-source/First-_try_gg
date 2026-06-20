"""Trading Bot Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# Broker Configuration
BROKER = "binance"  # Binance Futures
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
BINANCE_TESTNET = True  # Set to False for live trading

# Debug: Check if env vars are loaded
import logging
logger = logging.getLogger(__name__)
logger.info(f"BINANCE_API_KEY loaded: {bool(BINANCE_API_KEY)}")
logger.info(f"BINANCE_API_SECRET loaded: {bool(BINANCE_API_SECRET)}")

# Trading Pairs
TRADING_PAIRS = ["BTCUSDT"]  # Only BTC for focused trading
TIMEFRAME = "1h"  # 1 hour candles for better trends

# Technical Indicators
INDICATORS = {
    "sma_short": 20,      # Short-term moving average (improved for 1h)
    "sma_long": 50,       # Long-term moving average (classic setup)
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "stoch_rsi_period": 14,
    "stoch_rsi_smooth_k": 3,
    "stoch_rsi_smooth_d": 3,
    "atr_period": 14,
    "volume_period": 20,
}

# Risk Management
ACCOUNT_SIZE = 5000  # USD
RISK_PER_TRADE_PCT = 1.0  # 1% risk per trade = $50
MAX_RISK_PER_TRADE = ACCOUNT_SIZE * (RISK_PER_TRADE_PCT / 100)  # $50

RISK_MANAGEMENT = {
    "max_daily_loss": MAX_RISK_PER_TRADE * 3,  # Stop after 3 losses
    "max_daily_profit": MAX_RISK_PER_TRADE * 10,  # Target 10 wins per day
    "use_atr": True,            # Use ATR for dynamic SL/TP
    "atr_sl_multiplier": 1.0,   # SL = Entry - (ATR × 1.0)
    "atr_tp_multiplier": 2.3,   # TP = Entry + (ATR × 2.3) = 1:2.3 ratio
    "min_volume_threshold": 0.8,  # Only trade if volume > 80% of average
    "max_open_positions": 1,    # Only 1 BTC position at a time
}

# Notifications
NOTIFICATIONS = {
    "enabled": True,
    "email": os.getenv("ALERT_EMAIL"),
    "webhook_url": os.getenv("WEBHOOK_URL"),  # Slack/Discord webhook
    "telegram_token": os.getenv("TELEGRAM_TOKEN"),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
}

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "trading_bot.log"

# Strategy Settings
STRATEGY = {
    "mode": "paper",  # "paper" or "live"
    "entry_signal": "ma_cross",  # SMA cross, RSI, or MACD
    "exit_signal": "tp_sl",       # Take profit/stop loss
}
