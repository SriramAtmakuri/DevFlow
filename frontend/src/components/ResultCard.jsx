import React from 'react';

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
          <h3>📚 Sources ({result.sources.length})</h3>
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
                  {source.url}
                </a>
              )}
            </div>
          ))}
        </div>
      )}

      {result.model && (
        <div style={{ marginTop: '15px', fontSize: '0.9rem', color: '#999' }}>
          Powered by {result.model}
        </div>
      )}
    </div>
  );
}

export default ResultCard;