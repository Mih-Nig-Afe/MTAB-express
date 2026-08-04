import { createContext, useContext } from 'react';
import { TokenResponse, User } from '@/types';

export const setTokens = (access: string, refresh: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }
};

export const getStoredToken = () => {
  if (typeof window !== 'undefined') return localStorage.getItem('access_token');
  return null;
};

export const getRefreshToken = () => {
  if (typeof window !== 'undefined') return localStorage.getItem('refresh_token');
  return null;
};

export const logout = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
};

export const setUser = (user: User) => {
  if (typeof window !== 'undefined') localStorage.setItem('user', JSON.stringify(user));
}

export const getUser = (): User | null => {
  if (typeof window !== 'undefined') {
    const user = localStorage.getItem('user');
    if (user) return JSON.parse(user);
  }
  return null;
};

export const isAuthenticated = () => !!getStoredToken();

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const AuthContext = createContext<AuthContextType>({ user: null, setUser: () => {} });
export const useAuth = () => useContext(AuthContext);