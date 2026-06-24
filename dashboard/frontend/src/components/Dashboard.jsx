import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import '../styles/Dashboard.css';

function Dashboard({ apiBase }) {
  const [summary, setSummary] = useState(null);
  const [dailyStats, setDailyStats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const summaryRes = await axios.get(`${apiBase}/api/stats/summary`);
      setSummary(summaryRes.data);

      const dailyRes = await axios.get(`${apiBase}/api/stats/daily`);
      setDailyStats(dailyRes.data.daily_stats || []);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (!summary) return <div className="error">No data available</div>;

  return (
    <div className="dashboard">
      {/* Summary Cards */}
      <div className="cards-grid">
        <div className="card success">
          <div className="card-label">Total P&L</div>
          <div className="card-value">${summary.total_pnl.toFixed(2)}</div>
        </div>

        <div className="card info">
          <div className="card-label">Total Trades</div>
          <div className="card-value">{summary.total_trades}</div>
        </div>

        <div className="card success">
          <div className="card-label">Win Rate</div>
          <div className="card-value">{summary.win_rate.toFixed(1)}%</div>
        </div>

        <div className="card info">
          <div className="card-label">Winning Trades</div>
          <div className="card-value">{summary.winning_trades}</div>
          <div className="card-subtext">Losing: {summary.losing_trades}</div>
        </div>

        <div className="card info">
          <div className="card-label">Avg Win</div>
          <div className="card-value">${summary.avg_win.toFixed(2)}</div>
        </div>

        <div className="card warning">
          <div className="card-label">Avg Loss</div>
          <div className="card-value">${summary.avg_loss.toFixed(2)}</div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Daily P&L Chart */}
        <div className="chart-container">
          <h3>Daily P&L</h3>
          {dailyStats.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="daily_pnl" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="no-data">No daily data yet</p>
          )}
        </div>

        {/* Winning vs Losing Trades */}
        <div className="chart-container">
          <h3>Wins vs Losses per Day</h3>
          {dailyStats.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="winning_trades" fill="#4caf50" name="Wins" />
                <Bar dataKey="losing_trades" fill="#f44336" name="Losses" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="no-data">No trade data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
