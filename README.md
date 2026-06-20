# MetaTrader5 / ByBit Automated Trading Bot

A professional Python-based trading bot for automated trading on ByBit with technical indicators, risk management, and Prop Firm Challenge support.

## Features

✅ **Technical Indicators**
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Relative Strength Index (RSI)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands

✅ **Risk Management**
- Stop Loss & Take Profit levels
- Position sizing based on account risk
- Max daily loss limits
- Max open positions limit
- Daily profit targets

✅ **Trading Signals**
- MA Crossover strategy
- RSI confirmation
- MACD divergence detection
- Multi-timeframe support

✅ **Notifications**
- Webhook alerts (Slack/Discord)
- Email notifications
- Trade execution alerts
- Daily P&L summary

## Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd First-_try_gg
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your ByBit API credentials
```

4. **Set up trading parameters**
Edit `config.py`:
- `TRADING_PAIRS`: Symbols to trade
- `INDICATORS`: Adjust indicator periods
- `RISK_MANAGEMENT`: Risk parameters
- `STRATEGY`: Trading mode (paper/live)

## Quick Start

### Testnet Mode (Recommended for Prop Firms)
```python
# In config.py, set:
BYBIT_TESTNET = True  # Use testnet
STRATEGY["mode"] = "paper"  # Paper trading
```

### Run the Bot
```bash
python trading_bot.py
```

The bot will:
1. Connect to ByBit testnet
2. Monitor configured trading pairs
3. Generate signals based on technical indicators
4. Execute trades with automatic SL/TP
5. Send notifications on entries/exits
6. Log all activity to `trading_bot.log`

## Configuration Guide

### Trading Pairs
```python
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
```

### Risk Parameters
```python
RISK_MANAGEMENT = {
    "max_daily_loss": 100,        # Stop trading if daily loss reaches $100
    "max_daily_profit": 500,      # Close all positions if daily profit reaches $500
    "stop_loss_pct": 1.5,         # SL at 1.5% below entry
    "take_profit_pct": 3.0,       # TP at 3% above entry
    "position_size_usd": 100,     # $100 per trade
    "max_open_positions": 3,      # Max 3 concurrent trades
}
```

### Indicators
```python
INDICATORS = {
    "sma_short": 10,      # Fast SMA
    "sma_long": 20,       # Slow SMA
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
}
```

## Prop Firm Challenge Tips

1. **Start with testnet** - No real money risk
2. **Use daily loss limits** - Protect drawdown limits
3. **Conservative position sizing** - $50-100 per trade initially
4. **Monitor accuracy** - Track win rate and risk/reward
5. **Backtest first** - Test strategy before going live

## Monitoring

Check logs in real-time:
```bash
tail -f trading_bot.log
```

## Performance Metrics

The bot tracks:
- Daily P&L
- Daily losses
- Number of trades
- Open positions
- Win/loss statistics

## Supported Symbols

- BTCUSDT, ETHUSDT
- XRPUSDT, DOGEUSDT
- ADAUSDT, SOLUSDT
- Any ByBit linear perpetual

## API Integration

### ByBit
- Unified Trading API
- Support for testnet & live
- Real-time price data
- Order management

### Notifications
- Slack webhooks
- Discord webhooks
- Email (setup required)

## Safety Notes

⚠️ **IMPORTANT**
- Always test on testnet first
- Start with small position sizes
- Monitor the bot actively
- Keep API keys secure
- Never share credentials
- Use testnet for prop firm challenges

## Troubleshooting

### No signals generated
- Check if prices are updating
- Verify indicators.py calculations
- Review log files

### Orders not executing
- Check ByBit API permissions
- Verify balance/margin
- Check trading pair is available

### Notifications not working
- Verify webhook URL is valid
- Check internet connection
- Review notification settings

## Future Enhancements

- [ ] Multiple timeframe analysis
- [ ] Machine learning signal generation
- [ ] Backtesting engine
- [ ] Paper trading mode
- [ ] Discord bot commands
- [ ] Advanced risk metrics

## License

Private use only. Not for redistribution.

## Support

For issues or questions, review the code comments and check `trading_bot.log` for detailed error messages.
