# Trading Bot Dashboard

A modern web-based dashboard for monitoring and controlling your trading bot.

## Features

✅ **Daily P&L Dashboard** - Visualize profits and losses with interactive charts
✅ **Trade Statistics** - Win rate, winning/losing trades breakdown
✅ **Trade History** - Complete trade log with entry/exit details
✅ **Bot Control** - Monitor bot status and control settings
✅ **Real-time Updates** - Auto-refresh data every 30 seconds

## Project Structure

```
dashboard/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── database.py         # SQLite database management
│   └── requirements.txt    # Python dependencies
└── frontend/
    ├── package.json        # React dependencies
    ├── public/
    └── src/
        ├── components/
        │   ├── Dashboard.jsx
        │   ├── TradeHistory.jsx
        │   └── BotControl.jsx
        └── styles/
```

## Setup

### Backend (FastAPI)

```bash
cd dashboard/backend
pip install -r requirements.txt
python app.py
```

API runs on: `http://localhost:8000`

### Frontend (React)

```bash
cd dashboard/frontend
npm install
npm start
```

Dashboard runs on: `http://localhost:3000`

## API Integration

The trading bot needs to log trades to the database. Add this to `trading_bot.py`:

```python
import requests

API_BASE = "http://localhost:8000"

# In execute_entry():
requests.post(f"{API_BASE}/api/trades/log", json={
    "symbol": symbol,
    "side": side,
    "entry_price": entry_price,
    "quantity": qty,
    "stop_loss": sl,
    "take_profit": tp
})

# In check_exit_conditions():
requests.post(f"{API_BASE}/api/trades/close", json={
    "symbol": symbol,
    "exit_price": current_price,
    "pnl": pnl,
    "exit_reason": exit_reason
})
```

## Database

SQLite database automatically created at: `/First-_try_gg/trades.db`

### Tables

- **trades**: All trade records (entry, exit, P&L)
- **bot_status**: Bot status snapshots (running, positions, daily stats)

## API Endpoints

### Trades
- `POST /api/trades/log` - Log new trade
- `POST /api/trades/close` - Close a trade
- `GET /api/trades` - Get all trades
- `GET /api/trades/recent?limit=20` - Get recent trades

### Statistics
- `GET /api/stats/daily` - Daily P&L breakdown
- `GET /api/stats/monthly` - Monthly performance
- `GET /api/stats/summary` - Overall statistics

### Bot Control
- `GET /api/bot/status` - Get bot status
- `POST /api/bot/status` - Update bot status

### Health
- `GET /api/health` - Health check

## Deployment

### Railway Deployment

1. Add dashboard backend to Procfile:
```
web: python trading_bot.py
api: cd dashboard/backend && python app.py
```

2. Add dashboard frontend to Procfile:
```
dashboard: cd dashboard/frontend && npm run build && npm install -g serve && serve -s build -l 3000
```

## Next Steps

- [ ] Connect trading bot to dashboard API
- [ ] Add more advanced charts (Equity curve, Drawdown)
- [ ] Add parameter tuning interface
- [ ] Add performance metrics (Sharpe ratio, Sortino ratio)
- [ ] Add trade filtering/sorting

---

Built with ❤️ for your trading bot
