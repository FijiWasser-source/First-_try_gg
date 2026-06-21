import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/TradeHistory.css';

function TradeHistory({ apiBase }) {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrades();
    const interval = setInterval(fetchTrades, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchTrades = async () => {
    try {
      const res = await axios.get(`${apiBase}/api/trades`);
      setTrades(res.data.trades || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching trades:', error);
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading trades...</div>;

  return (
    <div className="trade-history">
      <h2>Trade History</h2>
      {trades.length === 0 ? (
        <p className="no-data">No trades yet</p>
      ) : (
        <table className="trades-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Side</th>
              <th>Entry Price</th>
              <th>Exit Price</th>
              <th>Qty</th>
              <th>SL</th>
              <th>TP</th>
              <th>P&L</th>
              <th>Status</th>
              <th>Exit Reason</th>
              <th>Entry Time</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, idx) => (
              <tr key={idx} className={`trade-row ${trade.status.toLowerCase()}`}>
                <td className="symbol">{trade.symbol}</td>
                <td className={`side ${trade.side.toLowerCase()}`}>{trade.side}</td>
                <td>${trade.entry_price.toFixed(2)}</td>
                <td>{trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}</td>
                <td>{trade.quantity.toFixed(2)}</td>
                <td>${trade.stop_loss.toFixed(2)}</td>
                <td>${trade.take_profit.toFixed(2)}</td>
                <td className={`pnl ${trade.pnl > 0 ? 'positive' : trade.pnl < 0 ? 'negative' : ''}`}>
                  {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                </td>
                <td className={`status ${trade.status.toLowerCase()}`}>{trade.status}</td>
                <td>{trade.exit_reason || '-'}</td>
                <td>{new Date(trade.entry_time).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default TradeHistory;
