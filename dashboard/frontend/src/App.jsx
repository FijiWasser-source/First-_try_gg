import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Dashboard from './components/Dashboard';
import TradeHistory from './components/TradeHistory';
import BotControl from './components/BotControl';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    // Initial data load
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch stats and bot status
      const statsRes = await axios.get(`${API_BASE}/api/stats/summary`);
      console.log('Stats:', statsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 Trading Bot Dashboard</h1>
        <nav className="nav-tabs">
          <button
            className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            className={`tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            📋 Trade History
          </button>
          <button
            className={`tab ${activeTab === 'control' ? 'active' : ''}`}
            onClick={() => setActiveTab('control')}
          >
            ⚙️ Bot Control
          </button>
        </nav>
      </header>

      <main className="main">
        {loading && <div className="loading">Loading...</div>}
        {activeTab === 'dashboard' && <Dashboard apiBase={API_BASE} />}
        {activeTab === 'history' && <TradeHistory apiBase={API_BASE} />}
        {activeTab === 'control' && <BotControl apiBase={API_BASE} />}
      </main>
    </div>
  );
}

export default App;
