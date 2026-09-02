import axios from 'axios';
import { getStoredToken, getRefreshToken, setTokens, logout } from './auth';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

  api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Never hijack auth-endpoint failures: a wrong password on the login page
    // must surface as an inline form error, not trigger logout + full reload.
    const url = originalRequest?.url || '';
    if (error.response?.status === 401 && url.includes('/auth/login')) {
      return Promise.reject(error);
    }
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      typeof window !== 'undefined' &&
      window.location.pathname === '/login'
    ) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = 'Bearer ' + token;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) throw new Error('No refresh token');

        const { data } = await axios.post(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: refreshToken });
        setTokens(data.access_token, data.refresh_token);
        api.defaults.headers.common['Authorization'] = 'Bearer ' + data.access_token;
        originalRequest.headers.Authorization = 'Bearer ' + data.access_token;
        processQueue(null, data.access_token);
        
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        logout();
        if (typeof window !== 'undefined') window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);