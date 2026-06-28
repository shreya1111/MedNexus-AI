import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('accessToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) throw new Error('No refresh token');
        const { data } = await axios.post(`${API_URL}/auth/refresh`, { refreshToken });
        localStorage.setItem('accessToken', data.data.accessToken);
        localStorage.setItem('refreshToken', data.data.refreshToken);
        if (original.headers) {
          original.headers.Authorization = `Bearer ${data.data.accessToken}`;
        }
        return api(original);
      } catch {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  register: (data: Record<string, unknown>) => api.post('/auth/register', data),
  login: (data: Record<string, unknown>) => api.post('/auth/login', data),
  logout: (refreshToken: string) => api.post('/auth/logout', { refreshToken }),
  getMe: () => api.get('/auth/me'),
  updateProfile: (data: Record<string, unknown>) => api.put('/auth/me', data),
  changePassword: (data: Record<string, unknown>) => api.put('/auth/me/password', data),
};

// Records
export const recordsApi = {
  getAll: (params?: Record<string, unknown>) => api.get('/records', { params }),
  getById: (id: string) => api.get(`/records/${id}`),
  create: (data: FormData) => api.post('/records', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id: string, data: Record<string, unknown>) => api.put(`/records/${id}`, data),
  delete: (id: string) => api.delete(`/records/${id}`),
  search: (q: string, params?: Record<string, unknown>) => api.get('/records/search', { params: { q, ...params } }),
};

// Appointments
export const appointmentsApi = {
  getAll: (params?: Record<string, unknown>) => api.get('/appointments', { params }),
  create: (data: Record<string, unknown>) => api.post('/appointments', data),
  updateStatus: (id: string, status: string) => api.put(`/appointments/${id}/status`, { status }),
  cancel: (id: string) => api.put(`/appointments/${id}/cancel`),
};

// Patients (doctor/admin)
export const patientsApi = {
  getAll: (params?: Record<string, unknown>) => api.get('/patients', { params }),
  getById: (id: string) => api.get(`/patients/${id}`),
  getMyProfile: () => api.get('/patients/profile'),
  updateMyProfile: (data: Record<string, unknown>) => api.put('/patients/profile', data),
};

// Analytics
export const analyticsApi = {
  getDashboard: () => api.get('/analytics/dashboard'),
};

// AI Services
export const aiApi = {
  query: (question: string, sessionId?: string) =>
    api.post(`${process.env.NEXT_PUBLIC_AI_URL || 'http://localhost:8000'}/api/rag/query`, { question, session_id: sessionId }),
  summarize: (recordId: string) =>
    api.post(`${process.env.NEXT_PUBLIC_AI_URL || 'http://localhost:8000'}/api/rag/summarize`, { record_id: recordId }),
  predict: (type: string, features: Record<string, number>) =>
    api.post(`${process.env.NEXT_PUBLIC_AI_URL || 'http://localhost:8000'}/api/ml/predict/${type}`, { features }),
};
