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

# Trading Pairs - Top 10 Cryptocurrencies
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT"]
TIMEFRAME = "1m"  # 1 minute candles

# Technical Indicators - New Setup
INDICATORS = {
    # EMA
    "ema_short": 20,
    "ema_long": 50,

    # Keltner Channels
    "keltner_basis": 20,  # EMA(20)
    "keltner_multiplier": 1.5,  # ±1.5 × ATR

    # MFI
    "mfi_period": 14,
    "mfi_long_threshold": 40,    # Below this = oversold
    "mfi_short_threshold": 50,   # Above this = overbought
    "mfi_lookback": 1,           # Last 1 candle

    # Fractal
    "fractal_window": 5,         # 5-candle fractal (2L, Mid, 2R)
    "fractal_lookback": 25,      # Look back 25 candles for confirmed fractals

    # ATR
    "atr_period": 14,
    "atr_sl_puffer": 0.5,        # SL = Fractal ± 0.5 × ATR

    # Risk/Reward
    "risk_reward_ratio": 2.3,    # TP = Entry + 2.3 × R
}

# Risk Management
ACCOUNT_SIZE = 100000  # USD
RISK_PER_TRADE_PCT = 1.0  # 1% risk per trade = $1000
MAX_RISK_PER_TRADE = ACCOUNT_SIZE * (RISK_PER_TRADE_PCT / 100)  # $1000

RISK_MANAGEMENT = {
    "leverage": 20,              # Binance default leverage (risk adjusted by this)
    "max_daily_loss": MAX_RISK_PER_TRADE * 3,  # Stop after 3 losses
    "max_daily_profit": 999999,  # Unlimited daily profit
    "use_atr": True,            # Use ATR for dynamic SL/TP
    "atr_sl_multiplier": 1.0,   # SL = Entry - (ATR × 1.0)
    "atr_tp_multiplier": 2.3,   # TP = Entry + (ATR × 2.3) = 1:2.3 ratio
    "min_volume_threshold": 0.8,  # Only trade if volume > 80% of average
    "max_open_positions": 5,    # Max 5 open positions at a time
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

# Asset Precision (decimals for order quantity)
ASSET_PRECISION = {
    "BTCUSDT": 0,      # Bitcoin - whole numbers only
    "ETHUSDT": 0,      # Ethereum - whole numbers only
    "BNBUSDT": 0,      # Binance Coin - whole numbers only
    "SOLUSDT": 0,      # Solana - whole numbers only
    "XRPUSDT": 0,      # Ripple - whole numbers only
    "DOGEUSDT": 0,     # Dogecoin - whole numbers only
    "ADAUSDT": 0,      # Cardano - whole numbers only
    "AVAXUSDT": 0,     # Avalanche - whole numbers only
    "LINKUSDT": 0,     # Chainlink - whole numbers only
    "DOTUSDT": 0,      # Polkadot - whole numbers only
}  # Default fallback: 0
