'use client';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { useTranslation } from '@/lib/i18n';
import { OperationsKPIs } from '@/types';
import { formatStatus } from '@/lib/utils';

const fetcher = (url: string) => api.get(url).then(res => res.data);

function Card({ label, value, hint, tone = 'gray' }: { label: string; value: string | number; hint?: string; tone?: string }) {
  const tones: Record<string, string> = {
    gray: 'text-gray-900',
    blue: 'text-blue-600',
    green: 'text-emerald-600',
    amber: 'text-amber-600',
    red: 'text-rose-600',
    indigo: 'text-indigo-600',
  };
  return (
    <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-200">
      <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{label}</span>
      <div className={`text-2xl font-black mt-2 ${tones[tone] || tones.gray}`}>{value}</div>
      {hint && <p className="text-xs text-gray-500 mt-1">{hint}</p>}
    </div>
  );
}

export default function OperationsBoard() {
  const { t } = useTranslation();
  const { data, error, isLoading } = useSWR<OperationsKPIs>('/reports/operations-kpis', fetcher, {
    refreshInterval: 30000,
  });

  const label = (status: string) => {
    const key = `status_${status}`;
    const translated = t(key);
    return translated === key ? formatStatus(status) : translated;
  };

  const funnel = data?.funnel ? Object.entries(data.funnel).filter(([, n]) => n > 0) : [];
  const maxFunnel = funnel.reduce((m, [, n]) => Math.max(m, n), 1);

  return (
    <RoleGuard allowedRoles={['admin', 'manager']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">{t('ops_title')}</h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">{t('ops_subtitle')}</p>
        </div>

        {isLoading && <div className="text-sm text-gray-400">{t('ops_loading')}</div>}
        {error && <div className="text-sm text-rose-500">{t('ops_error')}</div>}

        {data && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card label={t('ops_otd')} value={data.on_time_delivery_pct == null ? '—' : `${data.on_time_delivery_pct}%`} hint={t('ops_otd_hint')} tone="green" />
              <Card label={t('ops_linehaul')} value={data.volume.linehaul} hint={t('ops_linehaul_hint')} tone="blue" />
              <Card label={t('ops_ready')} value={data.volume.ready_for_pickup} hint={t('ops_ready_hint')} tone="amber" />
              <Card label={t('ops_exceptions')} value={`${data.exception_rate_pct}%`} hint={`${data.volume.exceptions} ${t('ops_exception_count')}`} tone="red" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card label={t('ops_aging_24')} value={data.pickup_aging.over_24h} hint={t('ops_aging_24_hint')} tone="amber" />
              <Card label={t('ops_aging_7d')} value={data.pickup_aging.over_7d} hint={t('ops_aging_7d_hint')} tone="red" />
              <Card label={t('ops_reminders')} value={data.pickup_aging.reminders_sent} hint={t('ops_reminders_hint')} />
              <Card label={t('ops_flights')} value={data.flights.active} hint={`${data.flights.delayed} ${t('ops_flights_delayed')}`} tone="indigo" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-base font-extrabold text-gray-900 mb-4">{t('ops_funnel')}</h2>
                {funnel.length === 0 ? (
                  <p className="text-sm text-gray-400">{t('ops_empty')}</p>
                ) : (
                  <ul className="space-y-2">
                    {funnel.map(([status, count]) => (
                      <li key={status}>
                        <div className="flex justify-between text-xs font-semibold text-gray-600 mb-1">
                          <span>{label(status)}</span>
                          <span>{count}</span>
                        </div>
                        <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-blue-500"
                            style={{ width: `${Math.max(6, (count / maxFunnel) * 100)}%` }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-base font-extrabold text-gray-900 mb-4">{t('ops_dwell')}</h2>
                {Object.keys(data.dwell_hours).length === 0 ? (
                  <p className="text-sm text-gray-400">{t('ops_empty')}</p>
                ) : (
                  <ul className="divide-y divide-gray-100">
                    {Object.entries(data.dwell_hours)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 10)
                      .map(([status, hours]) => (
                        <li key={status} className="py-2 flex justify-between text-sm">
                          <span className="text-gray-700">{label(status)}</span>
                          <span className="font-bold text-gray-900">{hours}h</span>
                        </li>
                      ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-base font-extrabold text-gray-900 mb-2">{t('ops_eta_title')}</h2>
              <p className="text-sm text-gray-600">
                {t('ops_eta_body')
                  .replace('{late}', String(data.eta.late_vs_promised))
                  .replace('{tracked}', String(data.eta.tracked_with_eta))}
              </p>
              <p className="text-xs text-gray-400 mt-3">
                {t('ops_wait_avg')}: {data.pickup_aging.avg_hours_waiting}h · {t('ops_total')}: {data.volume.total}
              </p>
            </div>
          </>
        )}
      </div>
    </RoleGuard>
  );
}
