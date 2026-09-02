import { api } from '@/lib/api';

export interface ParcelListQuery {
  page?: number;
  size?: number;
  status?: string;
  search?: string;
}

export const parcelsApi = {
  async list(query: ParcelListQuery = {}) {
    return (await api.get('/parcels', { params: query })).data as {
      items: unknown[]; total: number; page: number; size: number; pages: number;
    };
  },
  async get(id: string) {
    return (await api.get(`/parcels/${id}`)).data;
  },
  async updateStatus(id: string, to_status: string, note?: string) {
    return (await api.patch(`/parcels/${id}/status`, { to_status, note })).data;
  },
};

export default parcelsApi;
