import { api } from '@/lib/api';

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface StaffMe {
  id: string;
  name: string;
  phone: string;
  email: string | null;
  role: 'admin' | 'manager' | 'operator' | 'driver';
  branch_id: string | null;
  is_active: boolean;
}

export const authApi = {
  async login(phone: string, password: string): Promise<LoginResponse> {
    return (await api.post('/auth/login', { phone, password })).data;
  },
  async me(token?: string): Promise<StaffMe> {
    const config = token ? { headers: { Authorization: `Bearer ${token}` } } : undefined;
    return (await api.get('/auth/me', config)).data;
  },
};
