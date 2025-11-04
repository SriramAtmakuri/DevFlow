import React, { useState, useEffect } from 'react';
import { getSources, deleteSource, addManualDocument } from '../api/client';

function SourceManager() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ title: '', content: '', url: '' });

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const data = await getSources();
      setSources(data.sources);
    } catch (error) {
      console.error('Error loading sources:', error);
    }
  };

  const handleAddSource = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await addManualDocument(formData.title, formData.content, formData.url);
      alert('Document added successfully!');
      setFormData({ title: '', content: '', url: '' });
      loadSources();
    } catch (error) {
      alert('Error adding source: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sourceId) => {
    if (!window.confirm('Delete this source?')) return;
    try {
      await deleteSource(sourceId);
      alert('Source deleted!');
      loadSources();
    } catch (error) {
      alert('Error deleting: ' + error.message);
    }
  };

  return (
    <div>
      <div className="add-source-form">
        <h3>Add New Document</h3>
        <form onSubmit={handleAddSource}>
          <div className="form-group">
            <label>Title</label>
            <input
              type="text"
              placeholder="Document title"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Content</label>
            <textarea
              rows="6"
              placeholder="Paste your content here..."
              value={formData.content}
              onChange={(e) => setFormData({...formData, content: e.target.value})}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>URL (optional)</label>
            <input
              type="text"
              placeholder="https://example.com"
              value={formData.url}
              onChange={(e) => setFormData({...formData, url: e.target.value})}
              disabled={loading}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Adding...' : 'Add Document'}
          </button>
        </form>
      </div>

      <h3>Your Sources ({sources.length})</h3>
      <div className="sources-list">
        {sources.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📁</div>
            <p>No sources yet. Add your first document above!</p>
          </div>
        ) : (
          sources.map((source) => (
            <div key={source.id} className="source-card">
              <div className="source-info">
                <h4>{source.name || source.type}</h4>
                <p>
                  <span className="badge badge-success">{source.status}</span>
                  {source.doc_count} documents
                </p>
              </div>
              <button 
                className="btn btn-danger"
                onClick={() => handleDelete(source.id)}
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default SourceManager;