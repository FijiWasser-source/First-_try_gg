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
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT"]  # Add more as needed
TIMEFRAME = "15m"  # Binance format: 1m, 5m, 15m, 1h, 4h, 1d

# Technical Indicators
INDICATORS = {
    "sma_short": 10,      # Short-term moving average
    "sma_long": 20,       # Long-term moving average
    "ema_short": 5,       # Short-term EMA
    "ema_long": 15,       # Long-term EMA
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std_dev": 2,
}

# Risk Management
RISK_MANAGEMENT = {
    "max_daily_loss": 100,      # USD - Max loss per day
    "max_daily_profit": 500,    # USD - Max profit target per day
    "stop_loss_pct": 1.5,       # % of entry price
    "take_profit_pct": 3.0,     # % of entry price
    "position_size_usd": 100,   # USD per trade
    "max_open_positions": 3,    # Max concurrent trades
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
