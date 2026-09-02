'use client';
import { useTranslation } from '@/lib/i18n';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { formatCurrency } from '@/lib/utils';
import Link from 'next/link';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function Overrides() {
  const { t } = useTranslation();
  const { data: logs, isLoading } = useSWR<any[]>('/reports/operator-overrides', fetcher);

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('overrides')}</h1>
          <p className="text-sm text-gray-500 mt-1">{t('overrides_subtitle')}</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('parcel_code')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('operator_name')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('amount')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('reason')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {isLoading ? (
                <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-400 text-sm">{t('loading_audit')}</td></tr>
              ) : logs && logs.length > 0 ? (
                logs.map((log: any, idx: number) => (
                  <tr key={log.payment_id || idx} className="hover:bg-gray-50/50 transition">
                    <td className="px-6 py-4 text-sm font-mono font-bold text-blue-600">
                      {log.parcel_tracking_code}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">{log.operator_name}</td>
                    <td className="px-6 py-4 text-sm font-semibold text-emerald-600">
                      {formatCurrency(log.amount)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      <span className="bg-amber-50 text-amber-900 border border-amber-200 px-2.5 py-1 rounded-lg text-xs font-medium inline-block">
                        {log.override_reason}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-400 text-sm">{t('no_override_logs')}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </RoleGuard>
  );
}