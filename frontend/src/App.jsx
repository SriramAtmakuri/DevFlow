import React, { useState } from 'react';
import SearchBar from './components/SearchBar';
import ResultCard from './components/ResultCard';
import SourceManager from './components/SourceManager';
import Stats from './components/Stats';
import { searchDocuments } from './api/client';

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [searchResult, setSearchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    setSearchResult(null);

    try {
      const result = await searchDocuments(query);
      setSearchResult(result);
    } catch (err) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1>🧠 DevFlow</h1>
        <p>Your Personal Coding Knowledge Base</p>
      </div>

      <div className="main-content">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            🔍 Search
          </button>
          <button 
            className={`tab ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
          >
            📚 Sources
          </button>
        </div>

        {activeTab === 'search' && (
          <div>
            <SearchBar onSearch={handleSearch} loading={loading} />

            {error && <div className="error">⚠️ {error}</div>}
            {loading && <div className="loading">🔎 Searching...</div>}
            {searchResult && !loading && <ResultCard result={searchResult} />}
            
            {!searchResult && !loading && !error && (
              <div className="empty-state">
                <div className="empty-state-icon">💡</div>
                <h3>Ask me anything!</h3>
                <p>Search through your saved coding resources.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'sources' && (
          <>
            <Stats />
            <SourceManager />
          </>
        )}
      </div>
    </div>
  );
}

export default App;