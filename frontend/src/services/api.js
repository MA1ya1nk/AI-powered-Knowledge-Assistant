// services/api.js
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ka_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ka_token');
      localStorage.removeItem('ka_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  changePassword: (data) => api.put('/auth/change-password', data),
};

// Documents
export const documentsAPI = {
  upload: (formData, onProgress) => api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
    }
  }),
  list: (page = 1, limit = 20) => api.get(`/documents/list?page=${page}&limit=${limit}`),
  get: (id) => api.get(`/documents/${id}`),
  delete: (id) => api.delete(`/documents/${id}`),
  checkStatus: (id) => api.get(`/documents/${id}/status`),
};

// Chat
export const chatAPI = {
  ask: (data) => api.post('/chat/ask', data),
  listSessions: (page = 1) => api.get(`/chat/sessions?page=${page}`),
  getSession: (id) => api.get(`/chat/sessions/${id}`),
  deleteSession: (id) => api.delete(`/chat/sessions/${id}`),
  history: () => api.get('/chat/history'),
};

// Admin
export const adminAPI = {
  stats: () => api.get('/admin/stats'),
  listUsers: (page = 1) => api.get(`/admin/users?page=${page}`),
  toggleUser: (id) => api.put(`/admin/users/${id}/toggle`),
  listDocuments: (page = 1, status) => api.get(`/admin/documents?page=${page}${status ? `&status=${status}` : ''}`),
  toggleDocument: (id) => api.put(`/admin/documents/${id}/toggle`),
  listQueries: (page = 1) => api.get(`/admin/queries?page=${page}`),
};

export default api;