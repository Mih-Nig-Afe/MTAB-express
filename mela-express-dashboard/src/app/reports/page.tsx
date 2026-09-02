'use client';
import { useTranslation } from '@/lib/i18n';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { formatCurrency } from '@/lib/utils';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function Reports() {
  const { t } = useTranslation();
  const { data, isLoading } = useSWR<any>('/reports/branch-performance', fetcher);

  const summary = data?.summary || (data && !data.branch_breakdown ? data : null);
  const branches = Array.isArray(data?.branch_breakdown) 
    ? data.branch_breakdown 
    : (Array.isArray(data) ? data : []);

  const totalVolume = summary?.total_parcels ?? branches.reduce((sum: number, b: any) => sum + (b.total_parcels || 0), 0);
  const totalRevenue = summary?.total_revenue ?? branches.reduce((sum: number, b: any) => sum + (b.total_revenue || 0), 0);
  const delivered = summary?.delivered_parcels ?? 0;
  const inTransit = summary?.in_transit_parcels ?? 0;

  return (
    <RoleGuard allowedRoles={['admin', 'manager']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('reports')}</h1>
          <p className="text-sm text-gray-500 mt-1">{t('reports_subtitle')}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t('total_network_volume')}</span>
            <p className="text-3xl font-extrabold text-blue-600 mt-2">{t('n_parcels', { count: totalVolume })}</p>
            <p className="text-xs text-gray-400 mt-1">{t('registered_all_hubs')}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t('gross_revenue')}</span>
            <p className="text-3xl font-extrabold text-emerald-600 mt-2">{formatCurrency(totalRevenue)}</p>
            <p className="text-xs text-gray-400 mt-1">{t('total_paid_fees')}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t('kpi_delivered')}</span>
            <p className="text-3xl font-extrabold text-teal-600 mt-2">{t('n_parcels', { count: delivered })}</p>
            <p className="text-xs text-gray-400 mt-1">{t('handed_over')}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t('kpi_in_transit')}</span>
            <p className="text-3xl font-extrabold text-indigo-600 mt-2">{t('n_parcels', { count: inTransit })}</p>
            <p className="text-xs text-gray-400 mt-1">{t('active_on_highways')}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-base font-bold text-gray-900">{t('branch_breakdown')}</h2>
          </div>
          <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('branch_hub_col')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('city')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('total_parcels')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('revenue_col')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('share_of_network')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {isLoading ? (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-400 text-sm">{t('loading_metrics')}</td></tr>
              ) : branches && branches.length > 0 ? (
                branches.map((b: any, idx: number) => {
                  const share = totalVolume > 0 ? Math.round(((b.total_parcels || 0) / totalVolume) * 100) : 0;
                  return (
                    <tr key={b.branch_id || idx} className="hover:bg-gray-50/50 transition">
                      <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                        {b.branch_name} <span className="text-xs text-blue-600 font-mono">({b.branch_code})</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{b.city || '-'}</td>
                      <td className="px-6 py-4 text-sm font-mono font-medium text-gray-700">{t('n_parcels', { count: b.total_parcels || 0 })}</td>
                      <td className="px-6 py-4 text-sm font-semibold text-emerald-600">{formatCurrency(b.total_revenue || 0)}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        <div className="flex items-center gap-3">
                          <div className="w-24 bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${share}%` }}></div>
                          </div>
                          <span className="text-xs font-semibold">{share}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-400 text-sm">{t('no_branch_performance')}</td></tr>
              )}
            </tbody>
          </table>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}