'use client';
import { useTranslation } from '@/lib/i18n';
import { useState, useMemo } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { formatCurrency } from '@/lib/utils';

const fetcher = (url: string) => api.get(url).then(res => res.data);

function defaultRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

export default function CashReconciliation() {
  const { t } = useTranslation();
  const defaults = useMemo(() => defaultRange(), []);
  const [startDate, setStartDate] = useState(defaults.start);
  const [endDate, setEndDate] = useState(defaults.end);

  const { data, isLoading, error } = useSWR(
    `/reports/cash-reconciliation?start_date=${startDate}&end_date=${endDate}`,
    fetcher
  );

  return (
    <RoleGuard allowedRoles={['admin', 'manager']}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('cash')}</h1>
            <p className="text-sm text-gray-500 mt-1">{t('cash_subtitle')}</p>
          </div>
          <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-gray-200 shadow-sm text-sm">
            <input 
              type="date" 
              value={startDate} 
              onChange={e => setStartDate(e.target.value)} 
              className="border-none bg-gray-50 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 outline-none" 
            />
            <span className="text-gray-400 text-xs">{t('date_to')}</span>
            <input 
              type="date" 
              value={endDate} 
              onChange={e => setEndDate(e.target.value)} 
              className="border-none bg-gray-50 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 outline-none" 
            />
          </div>
        </div>

        {error ? (
          <div className="py-12 text-center text-rose-500 text-sm">{t('cash_load_error')}</div>
        ) : isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-pulse">
            <div className="bg-white h-32 rounded-2xl shadow-sm"></div>
            <div className="bg-white h-32 rounded-2xl shadow-sm"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-2xl p-6 shadow-lg shadow-emerald-600/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-100">{t('total_collected')}</span>
                <span className="text-2xl">💰</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold mt-3 tracking-tight">
                {formatCurrency(data?.total_cash_collected || 0)}
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t('transactions')}</span>
                <span className="text-2xl">🧾</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-3 tracking-tight">
                {data?.transaction_count || 0}
              </p>
            </div>
          </div>
        )}

        {data?.daily_breakdown?.length > 0 && (
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <h2 className="text-base font-bold text-gray-900 mb-4 pb-2 border-b border-gray-100">
              {t('cash_daily_breakdown')}
            </h2>
            <div className="divide-y divide-gray-100">
              {data.daily_breakdown.map((row: { date: string; collected_total: number }) => (
                <div key={row.date} className="flex justify-between py-2 text-sm">
                  <span className="text-gray-600 font-mono">{row.date}</span>
                  <span className="font-semibold text-emerald-600">{formatCurrency(row.collected_total)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {!isLoading && !error && (
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex justify-between items-center py-2 text-sm text-gray-700">
              <span>{t('drawer_status')}</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">{t('balanced')}</span>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}
