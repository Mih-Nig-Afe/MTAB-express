'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import ParcelTable from '@/components/parcels/ParcelTable';
import Link from 'next/link';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function ParcelsPage() {
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const query = new URLSearchParams({ page: page.toString(), size: '20' });
  if (status) query.append('status', status);
  if (search) query.append('search', search);

  const { data, isLoading } = useSWR(`/parcels?${query.toString()}`, fetcher);

  const statuses = ['', 'created', 'received_at_origin', 'in_transit', 'arrived_at_destination', 'ready_for_pickup', 'delivered', 'returned', 'cancelled', 'on_hold'];

  return (
    <RoleGuard>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900">Parcels</h1>
          <Link href="/parcels/new" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium text-sm inline-flex items-center">
            + New Parcel
          </Link>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col sm:flex-row gap-4">
          <input 
            type="text" 
            placeholder="Search tracking code or phone..." 
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
          <select 
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          >
            <option value="">All Statuses</option>
            {statuses.filter(Boolean).map(s => <option key={s} value={s}>{s.replace(/_/g, ' ').toUpperCase()}</option>)}
          </select>
        </div>

        {isLoading ? (
          <div className="text-center py-10 text-gray-500">Loading...</div>
        ) : (
          <>
            <ParcelTable parcels={data?.items || []} />
            
            {data && data.pages > 1 && (
              <div className="flex justify-between items-center bg-white px-4 py-3 border-t border-gray-200 sm:px-6 rounded-lg shadow-sm">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 text-sm">Previous</button>
                <span className="text-sm text-gray-700">Page {page} of {data.pages}</span>
                <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page === data.pages} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 text-sm">Next</button>
              </div>
            )}
          </>
        )}
      </div>
    </RoleGuard>
  );
}