import axios from 'axios';

const API_BASE_URL = 'https://devflow-1b2h.onrender.com/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
});

export const searchDocuments = async (query, nResults = 5) => {
  const response = await api.post('/search', { query, n_results: nResults });
  return response.data;
};

export const addManualDocument = async (title, content, url = null) => {
  const response = await api.post('/index/manual', { title, content, url });
  return response.data;
};

export const getSources = async () => {
  const response = await api.get('/sources');
  return response.data;
};

export const deleteSource = async (sourceId) => {
  const response = await api.delete(`/sources/${sourceId}`);
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

export default api;