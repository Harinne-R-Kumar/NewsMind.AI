/**
 * NewsMind AI - API Service
 * Handles all HTTP requests to the FastAPI backend.
 */

import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  refresh: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  verifyEmail: (token) => api.get(`/auth/verify-email?token=${token}`),
  forgotPassword: (email) => api.post(`/auth/forgot-password?email=${email}`),
  resetPassword: (token, newPassword) => api.post(`/auth/reset-password?token=${token}&new_password=${newPassword}`),
  deleteAccount: () => api.delete("/auth/delete-account"),
  resendVerification: () => api.post("/auth/resend-verification"),
  verifyEmail: (token) =>
    api.get(`/auth/verify-email?token=${token}`),
};

// Preferences API
export const preferencesAPI = {
  get: () => api.get('/preferences'),
  update: (data) => api.put('/preferences', data),
  getInterests: () => api.get('/preferences/interests'),
  addInterest: (topic) => api.post('/preferences/interests', { topic }),
  removeInterest: (id) => api.delete(`/preferences/interests/${id}`),
  getSources: () => api.get('/preferences/sources'),
  addSource: (sourceName) => api.post('/preferences/sources', { source_name: sourceName }),
  removeSource: (id) => api.delete(`/preferences/sources/${id}`),
  getExcluded: () => api.get('/preferences/excluded'),
  addExcluded: (topic) => api.post('/preferences/excluded', { topic }),
  removeExcluded: (id) => api.delete(`/preferences/excluded/${id}`),
  completeOnboarding: (data) => api.post('/preferences/onboarding', data),
};

// Schedules API
export const schedulesAPI = {
  get: () => api.get('/schedules'),
  create: (data) => api.post('/schedules', data),
  update: (id, data) => api.put(`/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedules/${id}`),
};

// Feedback API
export const feedbackAPI = {
  submitArticle: (data) => api.post('/feedback/article', data),
  submitReport: (reportId, data) => api.post(`/feedback/report/${reportId}`, data),
  getArticle: () => api.get('/feedback/article'),
};

// Reports API
export const reportsAPI = {
  list: () => api.get('/reports'),
  get: (id) => api.get(`/reports/${id}`),
  download: async (id) => {
    const response = await api.get(`/reports/${id}/download`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `newspaper_${id}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
  generate: () => api.post('/reports/generate'),
};

// Health API
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
