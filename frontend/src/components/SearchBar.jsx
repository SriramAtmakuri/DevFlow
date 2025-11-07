import React, { useState } from 'react';
import { Search, Globe } from 'lucide-react';

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  const [useWeb, setUseWeb] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, useWeb);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="search-box">
        <input
          type="text"
          className="search-input"
          placeholder="Ask anything about coding..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading || !query.trim()}
        >
          <Search size={20} />
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      
      <label 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          marginTop: '12px',
          cursor: 'pointer',
          fontSize: '0.9rem',
          color: '#6b7280'
        }}
      >
        <input
          type="checkbox"
          checked={useWeb}
          onChange={(e) => setUseWeb(e.target.checked)}
          style={{ cursor: 'pointer' }}
        />
        <Globe size={16} />
        Search web if not in my documents
      </label>
    </div>
  );
}

export default SearchBar;