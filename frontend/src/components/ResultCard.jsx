import React, { useState } from 'react';
import { ExternalLink, BookOpen, Globe, Save, CheckCircle } from 'lucide-react';
import { saveWebResult } from '../api/client';

function ResultCard({ result }) {
  const [savedResults, setSavedResults] = useState(new Set());
  const [saving, setSaving] = useState(null);

  const handleSave = async (webResult) => {
    setSaving(webResult.url);
    try {
      await saveWebResult(webResult);
      setSavedResults(new Set([...savedResults, webResult.url]));
      alert(`✅ Saved "${webResult.title}" to your knowledge base!`);
    } catch (error) {
      alert('❌ Failed to save: ' + error.message);
    } finally {
      setSaving(null);
    }
  };

  const docSources = result.doc_sources || [];
  const webSources = result.web_sources || [];
  const webResultsFull = result.web_results_full || [];

  return (
    <div className="result-card">
      <div className="result-header">
        <h3>Answer</h3>
      </div>

      <div className="result-content">
        <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
          {result.answer}
        </p>
      </div>

      {/* Document Sources */}
      {docSources.length > 0 && (
        <div className="sources-section">
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={18} />
            From Your Documents ({docSources.length})
          </h4>
          <div className="sources-list">
            {docSources.map((source, index) => (
              <div key={index} className="source-item">
                <span className="source-title">{source.title || source.url}</span>
                {source.url && source.url !== 'manual' && (
                  <a 
                    href={source.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Web Sources */}
      {webSources.length > 0 && (
        <div className="sources-section">
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe size={18} />
            From the Web ({webSources.length})
          </h4>
          <div className="sources-list">
            {webResultsFull.map((result, index) => {
              const isSaved = savedResults.has(result.url);
              const isSaving = saving === result.url;
              
              return (
                <div key={index} className="source-item web-source">
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      fontWeight: 500, 
                      marginBottom: '4px',
                      color: '#111827'
                    }}>
                      {result.title}
                    </div>
                    <div style={{ 
                      fontSize: '0.85rem', 
                      color: '#6b7280',
                      marginBottom: '8px'
                    }}>
                      {result.description}
                    </div>
                    <a 
                      href={result.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ 
                        fontSize: '0.85rem',
                        color: '#3b82f6',
                        textDecoration: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      {result.url}
                      <ExternalLink size={12} />
                    </a>
                  </div>
                  
                  {isSaved ? (
                    <button 
                      className="btn btn-success"
                      disabled
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '6px',
                        minWidth: '100px'
                      }}
                    >
                      <CheckCircle size={16} />
                      Saved
                    </button>
                  ) : (
                    <button 
                      className="btn btn-primary"
                      onClick={() => handleSave(result)}
                      disabled={isSaving}
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '6px',
                        minWidth: '100px'
                      }}
                    >
                      <Save size={16} />
                      {isSaving ? 'Saving...' : 'Save'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {docSources.length === 0 && webSources.length === 0 && (
        <div className="empty-state" style={{ marginTop: '20px' }}>
          <p>No sources available</p>
        </div>
      )}
    </div>
  );
}

export default ResultCard;