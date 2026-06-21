import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/BotControl.css';

function BotControl({ apiBase }) {
  const [botStatus, setBotStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBotStatus();
    const interval = setInterval(fetchBotStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchBotStatus = async () => {
    try {
      const res = await axios.get(`${apiBase}/api/bot/status`);
      setBotStatus(res.data || {});
      setLoading(false);
    } catch (error) {
      console.error('Error fetching bot status:', error);
      setLoading(false);
    }
  };

  const handleBotAction = async (action) => {
    try {
      await axios.post(`${apiBase}/api/bot/status`, {
        is_running: action === 'start',
        open_positions: botStatus?.open_positions || 0,
        daily_pnl: botStatus?.daily_pnl || 0,
        daily_loss: botStatus?.daily_loss || 0
      });
      fetchBotStatus();
    } catch (error) {
      console.error('Error updating bot status:', error);
    }
  };

  if (loading) return <div className="loading">Loading bot status...</div>;

  return (
    <div className="bot-control">
      <h2>🤖 Bot Control</h2>

      {botStatus && (
        <div className="status-panel">
          <div className={`status-badge ${botStatus.is_running ? 'running' : 'stopped'}`}>
            {botStatus.is_running ? '🟢 RUNNING' : '🔴 STOPPED'}
          </div>

          <div className="status-info">
            <div className="info-row">
              <span>Open Positions:</span>
              <strong>{botStatus.open_positions || 0}</strong>
            </div>
            <div className="info-row">
              <span>Daily P&L:</span>
              <strong className={botStatus.daily_pnl >= 0 ? 'positive' : 'negative'}>
                ${(botStatus.daily_pnl || 0).toFixed(2)}
              </strong>
            </div>
            <div className="info-row">
              <span>Daily Loss:</span>
              <strong>${(botStatus.daily_loss || 0).toFixed(2)}</strong>
            </div>
            <div className="info-row">
              <span>Last Update:</span>
              <strong>{botStatus.last_update ? new Date(botStatus.last_update).toLocaleString() : 'N/A'}</strong>
            </div>
          </div>

          <div className="control-buttons">
            <button
              className="btn btn-success"
              onClick={() => handleBotAction('start')}
              disabled={botStatus.is_running}
            >
              ▶️ Start Bot
            </button>
            <button
              className="btn btn-danger"
              onClick={() => handleBotAction('stop')}
              disabled={!botStatus.is_running}
            >
              ⏹️ Stop Bot
            </button>
          </div>

          <div className="info-box">
            <h4>⚠️ Info</h4>
            <p>The Bot Control buttons are for status tracking.</p>
            <p>To actually start/stop the bot, use Railway or your server management.</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default BotControl;
