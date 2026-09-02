'use client';
import { useState } from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import ParcelTable from '@/components/parcels/ParcelTable';
import DashboardDateFilter, {
  defaultDateFilter,
  dateFilterQuery,
  parcelDateQuery,
  type DateFilterValue,
} from '@/components/dashboard/DashboardDateFilter';
import { DashboardKPIs, Parcel, ParcelStatus } from '@/types';
import { useTranslation } from '@/lib/i18n';
import { useBarcodeScanner } from '@/hooks/useBarcodeScanner';
import { useToast } from '@/components/ui/Toast';

const fetcher = (url: string) => api.get(url).then(res => res.data);

/** Journey order — matches backend state machine ranks. */
const STATUS_ORDER: ParcelStatus[] = [
  'created',
  'received_at_origin',
  'processed_at_origin',
  'dispatched_from_origin',
  'in_transit',
  'arrived_origin_airport',
  'checked_in_flight',
  'departed',
  'arrived_destination_airport',
  'released_from_airport',
  'arrived_at_destination',
  'distributed_to_branch',
  'ready_for_pickup',
  'delivered',
  'returned',
  'cancelled',
  'lost',
  'on_hold',
];

const STATUS_STYLE: Record<string, { ring: string; text: string; bg: string }> = {
  created: { ring: 'ring-gray-200', text: 'text-gray-700', bg: 'bg-gray-50' },
  received_at_origin: { ring: 'ring-sky-200', text: 'text-sky-700', bg: 'bg-sky-50' },
  processed_at_origin: { ring: 'ring-sky-200', text: 'text-sky-800', bg: 'bg-sky-50' },
  dispatched_from_origin: { ring: 'ring-blue-200', text: 'text-blue-700', bg: 'bg-blue-50' },
  in_transit: { ring: 'ring-blue-200', text: 'text-blue-800', bg: 'bg-blue-50' },
  arrived_origin_airport: { ring: 'ring-indigo-200', text: 'text-indigo-700', bg: 'bg-indigo-50' },
  checked_in_flight: { ring: 'ring-indigo-200', text: 'text-indigo-800', bg: 'bg-indigo-50' },
  departed: { ring: 'ring-violet-200', text: 'text-violet-700', bg: 'bg-violet-50' },
  arrived_destination_airport: { ring: 'ring-violet-200', text: 'text-violet-800', bg: 'bg-violet-50' },
  released_from_airport: { ring: 'ring-purple-200', text: 'text-purple-700', bg: 'bg-purple-50' },
  arrived_at_destination: { ring: 'ring-emerald-200', text: 'text-emerald-700', bg: 'bg-emerald-50' },
  distributed_to_branch: { ring: 'ring-emerald-200', text: 'text-emerald-800', bg: 'bg-emerald-50' },
  ready_for_pickup: { ring: 'ring-amber-200', text: 'text-amber-700', bg: 'bg-amber-50' },
  delivered: { ring: 'ring-green-200', text: 'text-green-700', bg: 'bg-green-50' },
  returned: { ring: 'ring-orange-200', text: 'text-orange-700', bg: 'bg-orange-50' },
  cancelled: { ring: 'ring-rose-200', text: 'text-rose-700', bg: 'bg-rose-50' },
  lost: { ring: 'ring-red-200', text: 'text-red-700', bg: 'bg-red-50' },
  on_hold: { ring: 'ring-yellow-200', text: 'text-yellow-800', bg: 'bg-yellow-50' },
};

export default function Dashboard() {
  const router = useRouter();
  const toast = useToast();
  const { t } = useTranslation();
  const [dateFilter, setDateFilter] = useState<DateFilterValue>(defaultDateFilter);

  const kpiUrl = `/reports/dashboard-kpis?${dateFilterQuery(dateFilter)}`;
  const parcelsUrl = `/parcels?size=10&${parcelDateQuery(dateFilter)}`;

  const { data, error, isLoading } = useSWR<{ items: Parcel[] }>(parcelsUrl, fetcher);
  const parcels = data?.items ?? [];

  const { data: kpis, isLoading: kpisLoading } = useSWR<DashboardKPIs>(
    kpiUrl,
    fetcher,
    { refreshInterval: 30000 }
  );

  useBarcodeScanner((code) => {
    toast.info(t('scanned_barcode_msg').replace('{code}', code), t('barcode_scanner_title'));
    const matched = parcels?.find(p => p.tracking_code.toLowerCase() === code.toLowerCase());
    if (matched) {
      router.push(`/parcels/${matched.id}`);
    } else {
      router.push(`/parcels?search=${encodeURIComponent(code)}`);
    }
  });

  const counts = kpis?.status_counts ?? {};
  const parcelQs = parcelDateQuery(dateFilter);

  return (
    <RoleGuard>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-gray-900">{t('dashboard')}</h1>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">{t('dashboard_subtitle')}</p>
          </div>
          <Link
            href="/parcels/new"
            className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold py-2.5 px-4 rounded-2xl text-xs sm:text-sm shadow-md shadow-blue-500/20 transition"
          >
            {t('new_parcel')}
          </Link>
        </div>

        <DashboardDateFilter value={dateFilter} onChange={setDateFilter} />

        {/* Summary strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white rounded-2xl border border-gray-200 px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{t('kpi_network_total')}</p>
            <p className="text-xl font-black text-gray-900 mt-1">{kpisLoading ? '…' : kpis?.total_parcels ?? 0}</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{t('kpi_total_parcels')}</p>
            <p className="text-xl font-black text-blue-600 mt-1">{kpisLoading ? '…' : kpis?.parcels_created_today ?? 0}</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{t('kpi_delivered')}</p>
            <p className="text-xl font-black text-green-600 mt-1">{kpisLoading ? '…' : kpis?.parcels_delivered_today ?? 0}</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{t('kpi_ready_pickup')}</p>
            <p className="text-xl font-black text-emerald-600 mt-1">{kpisLoading ? '…' : kpis?.ready_for_pickup ?? 0}</p>
          </div>
        </div>

        {/* Full status board */}
        <div>
          <h2 className="text-sm font-extrabold text-gray-900 uppercase tracking-wide mb-3">
            {t('status_overview_title')}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {STATUS_ORDER.map((status) => {
              const style = STATUS_STYLE[status] ?? STATUS_STYLE.created;
              const count = counts[status] ?? 0;
              const label = t(`status_${status}`);
              return (
                <Link
                  key={status}
                  href={`/parcels?status=${status}&${parcelQs}`}
                  className={`rounded-2xl border p-4 ring-1 ${style.ring} ${style.bg} hover:shadow-md transition group`}
                >
                  <p className={`text-[10px] font-bold uppercase tracking-wide leading-tight ${style.text} opacity-80 group-hover:opacity-100`}>
                    {label}
                  </p>
                  <p className={`text-2xl font-black mt-2 ${style.text}`}>
                    {kpisLoading ? '…' : count}
                  </p>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-base font-extrabold text-gray-900 flex items-center gap-2">
              <span>📋</span> {t('recent_parcels')}
            </h2>
            <Link href={`/parcels?${parcelQs}`} className="text-xs font-bold text-blue-600 hover:text-blue-800 transition">
              {t('view_all')}
            </Link>
          </div>
          {isLoading ? (
            <div className="py-12 text-center text-gray-400 text-sm">{t('loading_shipments')}</div>
          ) : error ? (
            <div className="py-12 text-center text-rose-500 text-sm">{t('error_loading_shipments')}</div>
          ) : (
            <ParcelTable parcels={parcels} />
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
