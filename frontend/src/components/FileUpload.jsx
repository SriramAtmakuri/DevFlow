import React, { useState } from 'react';
import { Upload, File, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

function FileUpload({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['.pdf', '.docx', '.txt'];
    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!validTypes.includes(fileExt)) {
      setError('Please upload a PDF, DOCX, or TXT file');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB');
      return;
    }

    setUploading(true);
    setError(null);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        'https://devflow-1b2h.onrender.com/api/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setMessage(`✅ ${response.data.message} (${response.data.chunks} chunks indexed)`);
      
      // Reset file input
      e.target.value = '';
      
      // Notify parent component
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload-section">
      <h3 style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Upload size={20} />
        Upload Document
      </h3>
      
      <div style={{ marginBottom: '20px' }}>
        <label 
          htmlFor="file-upload" 
          className="btn btn-primary"
          style={{ 
            cursor: uploading ? 'not-allowed' : 'pointer',
            opacity: uploading ? 0.6 : 1,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <File size={18} />
          {uploading ? 'Uploading...' : 'Choose File (PDF, DOCX, TXT)'}
        </label>
        <input
          id="file-upload"
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          disabled={uploading}
          style={{ display: 'none' }}
        />
      </div>

      {message && (
        <div style={{
          background: '#d1fae5',
          color: '#065f46',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '15px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          border: '1px solid #6ee7b7'
        }}>
          <CheckCircle size={20} />
          {message}
        </div>
      )}

      {error && (
        <div className="error">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      <p style={{ fontSize: '0.9rem', color: '#6b7280', marginTop: '10px' }}>
        Supported formats: PDF, DOCX, TXT • Max size: 10MB
      </p>
    </div>
  );
}

export default FileUpload;