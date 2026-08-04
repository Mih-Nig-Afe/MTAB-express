'use client';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { formatCurrency } from '@/lib/utils';
import { DashboardKPIs } from '@/types';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function Dashboard() {
  const { data, error, isLoading } = useSWR<DashboardKPIs>('/reports/dashboard-kpis', fetcher);

  return (
    <RoleGuard>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
            {[1,2,3,4].map(i => <div key={i} className="bg-white h-24 rounded-lg shadow-sm"></div>)}
          </div>
        ) : error ? (
          <div className="text-red-500">Failed to load KPIs.</div>
        ) : data ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard title="Created Today" value={data.parcels_created_today} icon="📦" color="blue" />
            <KpiCard title="Delivered Today" value={data.parcels_delivered_today} icon="✅" color="green" />
            <KpiCard title="In Transit" value={data.parcels_in_transit} icon="🚚" color="indigo" />
            <KpiCard title="Pending Payments" value={formatCurrency(data.pending_payments_total)} subtitle={`${data.pending_payments_count} parcels`} icon="💰" color="amber" />
          </div>
        ) : null}
      </div>
    </RoleGuard>
  );
}

function KpiCard({ title, value, subtitle, icon, color }: any) {
  const colorMap: any = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    indigo: 'bg-indigo-100 text-indigo-600',
    amber: 'bg-amber-100 text-amber-600',
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 flex items-center">
      <div className={`p-4 rounded-full ${colorMap[color]} mr-4 text-2xl`}>{icon}</div>
      <div>
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}