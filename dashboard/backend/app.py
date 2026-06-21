"""Trading Dashboard API - FastAPI Backend"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import logging
from database import (
    init_database, log_trade, close_trade, get_all_trades,
    get_daily_stats, get_bot_status, update_bot_status
)

# Initialize database
init_database()

app = FastAPI(title="Trading Dashboard API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


# ============ TRADE ENDPOINTS ============

@app.post("/api/trades/log")
async def log_new_trade(data: dict):
    """Log a new trade entry"""
    try:
        log_trade(
            symbol=data["symbol"],
            side=data["side"],
            entry_price=data["entry_price"],
            quantity=data["quantity"],
            stop_loss=data["stop_loss"],
            take_profit=data["take_profit"]
        )
        return {"status": "success", "message": "Trade logged"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/trades/close")
async def close_existing_trade(data: dict):
    """Close an open trade"""
    try:
        close_trade(
            symbol=data["symbol"],
            exit_price=data["exit_price"],
            pnl=data["pnl"],
            exit_reason=data["exit_reason"]
        )
        return {"status": "success", "message": "Trade closed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/trades")
async def get_trades():
    """Get all trades"""
    trades = get_all_trades()
    return {"trades": trades}


@app.get("/api/trades/recent")
async def get_recent_trades(limit: int = 20):
    """Get recent trades"""
    all_trades = get_all_trades()
    return {"trades": all_trades[:limit]}


# ============ STATISTICS ENDPOINTS ============

@app.get("/api/stats/daily")
async def get_daily_performance():
    """Get daily P&L stats"""
    stats = get_daily_stats()

    # Calculate totals
    total_pnl = sum(s["daily_pnl"] or 0 for s in stats)
    total_trades = sum(s["total_trades"] or 0 for s in stats)
    total_wins = sum(s["winning_trades"] or 0 for s in stats)
    total_losses = sum(s["losing_trades"] or 0 for s in stats)

    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0

    return {
        "daily_stats": stats,
        "summary": {
            "total_pnl": round(total_pnl, 2),
            "total_trades": total_trades,
            "winning_trades": total_wins,
            "losing_trades": total_losses,
            "win_rate": round(win_rate, 2)
        }
    }


@app.get("/api/stats/monthly")
async def get_monthly_performance():
    """Get monthly P&L stats"""
    trades = get_all_trades()

    # Group by month
    monthly_stats = {}
    for trade in trades:
        if trade["status"] == "CLOSED" and trade["pnl"]:
            entry_date = datetime.fromisoformat(trade["entry_time"])
            month_key = entry_date.strftime("%Y-%m")

            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    "month": month_key,
                    "pnl": 0,
                    "trades": 0,
                    "wins": 0,
                    "losses": 0
                }

            monthly_stats[month_key]["pnl"] += trade["pnl"]
            monthly_stats[month_key]["trades"] += 1
            if trade["pnl"] > 0:
                monthly_stats[month_key]["wins"] += 1
            else:
                monthly_stats[month_key]["losses"] += 1

    return {"monthly_stats": list(monthly_stats.values())}


@app.get("/api/stats/summary")
async def get_summary_stats():
    """Get overall summary stats"""
    trades = get_all_trades()
    closed_trades = [t for t in trades if t["status"] == "CLOSED"]

    total_pnl = sum(t["pnl"] or 0 for t in closed_trades)
    total_trades = len(closed_trades)
    winning = sum(1 for t in closed_trades if t["pnl"] and t["pnl"] > 0)
    losing = sum(1 for t in closed_trades if t["pnl"] and t["pnl"] < 0)

    win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
    avg_win = (sum(t["pnl"] for t in closed_trades if t["pnl"] and t["pnl"] > 0) / winning) if winning > 0 else 0
    avg_loss = (sum(t["pnl"] for t in closed_trades if t["pnl"] and t["pnl"] < 0) / losing) if losing > 0 else 0

    return {
        "total_pnl": round(total_pnl, 2),
        "total_trades": total_trades,
        "winning_trades": winning,
        "losing_trades": losing,
        "win_rate": round(win_rate, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
    }


# ============ BOT STATUS ENDPOINTS ============

@app.get("/api/bot/status")
async def get_bot_current_status():
    """Get bot status"""
    status = get_bot_status()
    return status


@app.post("/api/bot/status")
async def update_bot_current_status(data: dict):
    """Update bot status"""
    try:
        update_bot_status(
            is_running=data.get("is_running", False),
            open_positions=data.get("open_positions", 0),
            daily_pnl=data.get("daily_pnl", 0),
            daily_loss=data.get("daily_loss", 0)
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ HEALTH CHECK ============

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
