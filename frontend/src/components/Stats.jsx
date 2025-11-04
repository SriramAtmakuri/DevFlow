import React, { useState, useEffect } from 'react';
import { getStats } from '../api/client';

function Stats() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  if (!stats) return null;

  return (
    <div className="stats">
      <div className="stat-card">
        <div className="stat-value">{stats.sources || 0}</div>
        <div className="stat-label">Sources</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.documents || 0}</div>
        <div className="stat-label">Documents</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.searches || 0}</div>
        <div className="stat-label">Searches</div>
      </div>
    </div>
  );
}

export default Stats;