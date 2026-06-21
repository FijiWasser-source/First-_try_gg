# Trading Bot Integration Guide

How to integrate the dashboard with your trading bot.

## Step 1: Add Dashboard API Calls to Trading Bot

### In `execute_entry()` method:

After successfully placing an order, add:

```python
def execute_entry(self, symbol: str, signal: dict):
    # ... existing code ...
    
    if order and "orderId" in order:
        # ... existing position tracking code ...
        
        # Log trade to dashboard
        try:
            import requests
            requests.post("http://localhost:8000/api/trades/log", json={
                "symbol": symbol,
                "side": side,
                "entry_price": entry_price,
                "quantity": qty,
                "stop_loss": sl,
                "take_profit": tp
            }, timeout=2)
        except Exception as e:
            logger.warning(f"Dashboard logging failed: {e}")
```

### In `check_exit_conditions()` method:

After closing a position, add:

```python
def check_exit_conditions(self, symbol: str):
    # ... existing code ...
    
    if exit_reason:
        # ... existing close position code ...
        
        if order:
            # ... existing P&L calculation ...
            
            # Log exit to dashboard
            try:
                import requests
                requests.post("http://localhost:8000/api/trades/close", json={
                    "symbol": symbol,
                    "exit_price": current_price,
                    "pnl": pnl,
                    "exit_reason": exit_reason
                }, timeout=2)
            except Exception as e:
                logger.warning(f"Dashboard exit logging failed: {e}")
            
            # ... rest of code ...
```

## Step 2: Add Dashboard Requirements

Update `requirements.txt` to include requests:

```
requests==2.31.0
```

## Step 3: Run Dashboard & Bot Together

### Local Development

**Terminal 1 - Start Backend API:**
```bash
cd dashboard/backend
python app.py
```

**Terminal 2 - Start Frontend:**
```bash
cd dashboard/frontend
npm start
```

**Terminal 3 - Start Trading Bot:**
```bash
python trading_bot.py
```

### Railway Deployment

Update your `Procfile`:

```
bot: python trading_bot.py
api: cd dashboard/backend && python app.py
dashboard: cd dashboard/frontend && npm run build && serve -s build -l 3000
```

## Step 4: Access Dashboard

- **Local**: http://localhost:3000
- **Railway**: https://your-app-name.up.railway.app

## Verification

1. Start the bot
2. Wait for a trade to execute
3. Check dashboard - you should see the trade appear in Trade History
4. Check Daily Stats - P&L should update after trade closes

## Troubleshooting

### Trades not showing up?

1. Check bot logs for errors
2. Verify dashboard backend is running: `curl http://localhost:8000/api/health`
3. Check browser console for API errors
4. Ensure `trades.db` file exists in project root

### Dashboard showing old data?

1. Hard refresh browser (Ctrl+F5)
2. Clear localStorage: Open DevTools → Application → Storage → Clear All
3. Restart dashboard backend

### API connection errors?

- Make sure backend is running on port 8000
- Check firewall/network settings
- Verify requests can reach localhost

---

For more details, see README.md
