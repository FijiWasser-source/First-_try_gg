"""Trade Database Management"""
import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent.parent / "trades.db"


def init_database():
    """Initialize database schema"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            quantity REAL NOT NULL,
            entry_time TIMESTAMP NOT NULL,
            exit_time TIMESTAMP,
            stop_loss REAL NOT NULL,
            take_profit REAL NOT NULL,
            pnl REAL,
            pnl_percent REAL,
            exit_reason TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_running BOOLEAN DEFAULT 0,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            open_positions INTEGER DEFAULT 0,
            daily_pnl REAL DEFAULT 0,
            daily_loss REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def log_trade(symbol: str, side: str, entry_price: float, quantity: float,
              stop_loss: float, take_profit: float):
    """Log a new trade"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trades
        (symbol, side, entry_price, quantity, entry_time, stop_loss, take_profit, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
    """, (symbol, side, entry_price, quantity, datetime.now(), stop_loss, take_profit))

    conn.commit()
    conn.close()


def close_trade(symbol: str, exit_price: float, pnl: float, exit_reason: str):
    """Close an open trade"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE trades
        SET exit_price = ?, exit_time = ?, pnl = ?, exit_reason = ?, status = 'CLOSED'
        WHERE symbol = ? AND status = 'OPEN'
        ORDER BY entry_time DESC
        LIMIT 1
    """, (exit_price, datetime.now(), pnl, exit_reason, symbol))

    conn.commit()
    conn.close()


def get_all_trades():
    """Get all trades"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM trades ORDER BY entry_time DESC")
    trades = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return trades


def get_daily_stats():
    """Get daily P&L and stats"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            DATE(entry_time) as date,
            COUNT(*) as total_trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
            SUM(pnl) as daily_pnl
        FROM trades
        WHERE status = 'CLOSED'
        GROUP BY DATE(entry_time)
        ORDER BY date DESC
    """)

    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stats


def get_bot_status():
    """Get current bot status"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bot_status ORDER BY id DESC LIMIT 1")
    status = dict(cursor.fetchone() or {})

    conn.close()
    return status


def update_bot_status(is_running: bool, open_positions: int, daily_pnl: float, daily_loss: float):
    """Update bot status"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bot_status (is_running, open_positions, daily_pnl, daily_loss)
        VALUES (?, ?, ?, ?)
    """, (is_running, open_positions, daily_pnl, daily_loss))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
    print("✅ Database initialized!")
