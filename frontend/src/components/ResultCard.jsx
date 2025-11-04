import React from 'react';
import { BookOpen, ExternalLink } from 'lucide-react';

function ResultCard({ result }) {
  if (!result) return null;

  return (
    <div className="result-card">
      <div className="answer">
        <strong>Answer:</strong>
        <p>{result.answer}</p>
      </div>

      {result.sources && result.sources.length > 0 && (
        <div className="sources">
          <h3>
            <BookOpen size={18} />
            Sources ({result.sources.length})
          </h3>
          {result.sources.map((source, index) => (
            <div key={index} className="source-item">
              <div className="source-title">
                {index + 1}. {source.title}
              </div>
              {source.url && (
                <a 
                  href={source.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="source-url"
                >
                  <ExternalLink size={14} />
                  {source.url}
                </a>
              )}
            </div>
          ))}
        </div>
      )}

      {result.model && (
        <div style={{ marginTop: '15px', fontSize: '0.85rem', color: '#9ca3af' }}>
          Powered by {result.model}
        </div>
      )}
    </div>
  );
}

export default ResultCard;