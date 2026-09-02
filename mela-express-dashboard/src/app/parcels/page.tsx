'use client';
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import ParcelTable from '@/components/parcels/ParcelTable';
import { ParcelStatus } from '@/types';
import { useTranslation } from '@/lib/i18n';
import Link from 'next/link';

const fetcher = (url: string) => api.get(url).then(res => res.data);

const ALL_STATUSES: ParcelStatus[] = [
  'created', 'received_at_origin', 'processed_at_origin', 'dispatched_from_origin',
  'in_transit', 'arrived_origin_airport', 'checked_in_flight', 'departed',
  'arrived_destination_airport', 'released_from_airport', 'arrived_at_destination',
  'distributed_to_branch', 'ready_for_pickup', 'delivered', 'returned', 'cancelled', 'lost', 'on_hold',
];

export default function ParcelsPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [createdFrom, setCreatedFrom] = useState('');
  const [createdTo, setCreatedTo] = useState('');
  const [page, setPage] = useState(1);
  const { t } = useTranslation();

  useEffect(() => {
    const q = searchParams.get('status');
    if (q) setStatus(q);
    const from = searchParams.get('created_from');
    const to = searchParams.get('created_to');
    if (from) setCreatedFrom(from);
    if (to) setCreatedTo(to);
  }, [searchParams]);

  const query = new URLSearchParams({ page: page.toString(), size: '20' });
  if (status) query.append('status', status);
  if (search) query.append('search', search);
  if (createdFrom) query.append('created_from', createdFrom);
  if (createdTo) query.append('created_to', createdTo);

  const { data, isLoading } = useSWR(`/parcels?${query.toString()}`, fetcher);

  return (
    <RoleGuard>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900">{t('parcels')}</h1>
          <Link href="/parcels/new" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium text-sm inline-flex items-center">
            {t('new_parcel')}
          </Link>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col sm:flex-row gap-4 flex-wrap">
          <input 
            type="text" 
            placeholder={t('search_placeholder')} 
            className="flex-1 min-w-[200px] border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
          <select 
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          >
            <option value="">{t('all_statuses')}</option>
            {ALL_STATUSES.map(s => <option key={s} value={s}>{t(`status_${s}`)}</option>)}
          </select>
          <input
            type="date"
            value={createdFrom}
            onChange={(e) => { setCreatedFrom(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            title={t('date_from')}
          />
          <input
            type="date"
            value={createdTo}
            min={createdFrom || undefined}
            onChange={(e) => { setCreatedTo(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            title={t('date_to')}
          />
        </div>

        {isLoading ? (
          <div className="text-center py-10 text-gray-500">{t('loading')}</div>
        ) : (
          <>
            <ParcelTable parcels={data?.items || []} />
            
            {data && data.pages > 1 && (
              <div className="flex justify-between items-center bg-white px-4 py-3 border-t border-gray-200 sm:px-6 rounded-lg shadow-sm">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 text-sm">{t('previous')}</button>
                <span className="text-sm text-gray-700">{t('page_word')} {page} {t('of_word')} {data.pages}</span>
                <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page === data.pages} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 text-sm">{t('next')}</button>
              </div>
            )}
          </>
        )}
      </div>
    </RoleGuard>
  );
}
