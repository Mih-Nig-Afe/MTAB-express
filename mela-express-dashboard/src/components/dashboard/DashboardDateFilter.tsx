'use client';

import { useTranslation } from '@/lib/i18n';

export type DateFilterMode = 'single' | 'range';

export interface DateFilterValue {
  mode: DateFilterMode;
  startDate: string; // YYYY-MM-DD
  endDate: string;
}

export function todayIso(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function localDateIso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function defaultDateFilter(): DateFilterValue {
  const d = todayIso();
  return { mode: 'single', startDate: d, endDate: d };
}

interface Props {
  value: DateFilterValue;
  onChange: (value: DateFilterValue) => void;
}

export default function DashboardDateFilter({ value, onChange }: Props) {
  const { t } = useTranslation();

  const setPreset = (preset: 'today' | 'yesterday' | 'week' | 'month') => {
    const now = new Date();
    const fmt = localDateIso;
    if (preset === 'today') {
      const d = fmt(now);
      onChange({ mode: 'single', startDate: d, endDate: d });
      return;
    }
    if (preset === 'yesterday') {
      const y = new Date(now);
      y.setDate(y.getDate() - 1);
      const d = fmt(y);
      onChange({ mode: 'single', startDate: d, endDate: d });
      return;
    }
    if (preset === 'week') {
      const start = new Date(now);
      start.setDate(start.getDate() - 6);
      onChange({ mode: 'range', startDate: fmt(start), endDate: fmt(now) });
      return;
    }
    const start = new Date(now);
    start.setDate(start.getDate() - 29);
    onChange({ mode: 'range', startDate: fmt(start), endDate: fmt(now) });
  };

  const label =
    value.mode === 'single' || value.startDate === value.endDate
      ? value.startDate
      : `${value.startDate} → ${value.endDate}`;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-4 sm:p-5 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-end gap-4 justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-gray-500">{t('date_filter_title')}</p>
          <p className="text-sm font-semibold text-gray-900 mt-1">{label}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {(['today', 'yesterday', 'week', 'month'] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPreset(p)}
              className="px-3 py-1.5 rounded-xl text-xs font-bold bg-gray-100 hover:bg-blue-50 hover:text-blue-700 text-gray-700 transition"
            >
              {t(`date_preset_${p}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 flex flex-col sm:flex-row gap-4 items-start sm:items-end">
        <div className="flex rounded-xl border border-gray-200 p-1 bg-gray-50">
          <button
            type="button"
            onClick={() => onChange({ ...value, mode: 'single', endDate: value.startDate })}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              value.mode === 'single' ? 'bg-white shadow text-blue-700' : 'text-gray-600'
            }`}
          >
            {t('date_mode_single')}
          </button>
          <button
            type="button"
            onClick={() => onChange({ ...value, mode: 'range' })}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              value.mode === 'range' ? 'bg-white shadow text-blue-700' : 'text-gray-600'
            }`}
          >
            {t('date_mode_range')}
          </button>
        </div>

        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-[10px] font-bold uppercase text-gray-500 mb-1">
              {value.mode === 'single' ? t('date_pick_day') : t('date_from')}
            </label>
            <input
              type="date"
              value={value.startDate}
              max={value.endDate}
              onChange={(e) => {
                const startDate = e.target.value;
                onChange({
                  ...value,
                  startDate,
                  endDate: value.mode === 'single' ? startDate : value.endDate < startDate ? startDate : value.endDate,
                });
              }}
              className="border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          {value.mode === 'range' && (
            <div>
              <label className="block text-[10px] font-bold uppercase text-gray-500 mb-1">{t('date_to')}</label>
              <input
                type="date"
                value={value.endDate}
                min={value.startDate}
                onChange={(e) => onChange({ ...value, endDate: e.target.value })}
                className="border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function dateFilterQuery(value: DateFilterValue): string {
  const params = new URLSearchParams();
  params.set('start_date', value.startDate);
  params.set('end_date', value.mode === 'single' ? value.startDate : value.endDate);
  return params.toString();
}

export function parcelDateQuery(value: DateFilterValue): string {
  const end = value.mode === 'single' ? value.startDate : value.endDate;
  const params = new URLSearchParams();
  params.set('created_from', value.startDate);
  params.set('created_to', end);
  return params.toString();
}
