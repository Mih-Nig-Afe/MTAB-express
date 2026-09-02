'use client';
import { useCallback, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import RoleGuard from '@/components/layout/RoleGuard';
import { useBarcodeScanner } from '@/hooks/useBarcodeScanner';
import { useToast } from '@/components/ui/Toast';
import { useTranslation } from '@/lib/i18n';
import { ParcelScanResult } from '@/types';

export default function ScanStationPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [code, setCode] = useState('');
  const [flightNumber, setFlightNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<ParcelScanResult | null>(null);

  const submitScan = useCallback(async (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setCode(trimmed);
    try {
      const res = await api.post<ParcelScanResult>('/parcels/scan', {
        code: trimmed,
        flight_number: flightNumber.trim() || undefined,
      });
      setLastResult(res.data);
      setCode('');
      setFlightNumber('');
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        navigator.vibrate(80);
      }
      toast.success(res.data.message, t('scan_success_title'));
    } catch (err: any) {
      const detail = err.response?.data?.detail || t('scan_failed');
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail), t('scan_error_title'));
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        navigator.vibrate([60, 40, 60]);
      }
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [flightNumber, loading, t, toast]);

  useBarcodeScanner(submitScan);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitScan(code);
  };

  const needsBranch = !user?.branch_id && user?.role !== 'driver';

  return (
    <RoleGuard allowedRoles={['operator', 'manager', 'driver', 'admin']}>
      <div className="max-w-lg mx-auto p-4 sm:p-8">
        {needsBranch && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-2xl text-sm text-amber-900">
            <p className="font-bold">{t('scan_no_branch_title')}</p>
            <p className="mt-1 text-amber-800">{t('scan_no_branch_hint')}</p>
          </div>
        )}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 text-white text-3xl mb-4 shadow-lg shadow-blue-500/30">
            📷
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{t('scan_station_title')}</h1>
          <p className="text-gray-500 mt-2 text-sm">{t('scan_station_hint')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">{t('tracking_code')}</label>
            <input
              ref={inputRef}
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder={t('scan_or_type_code')}
              className="w-full text-lg font-mono tracking-wider bg-gray-50 border-2 border-gray-300 rounded-xl py-4 px-4 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">{t('flight_number_optional')}</label>
            <input
              value={flightNumber}
              onChange={(e) => setFlightNumber(e.target.value.toUpperCase())}
              placeholder="ET302"
              className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm font-mono focus:border-blue-500 outline-none"
            />
            <p className="text-xs text-gray-400 mt-1">{t('flight_scan_hint')}</p>
          </div>
          <button
            type="submit"
            disabled={loading || !code.trim() || needsBranch}
            className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold rounded-xl text-lg shadow-md transition"
          >
            {loading ? t('scanning') : t('confirm_scan')}
          </button>
        </form>

        {lastResult && (
          <div className="mt-8 p-5 bg-emerald-50 border border-emerald-200 rounded-2xl">
            <p className="text-xs font-bold uppercase text-emerald-700 tracking-wide">{t('last_scan')}</p>
            <p className="font-mono font-black text-xl mt-1">{lastResult.tracking_code}</p>
            <p className="text-emerald-800 font-semibold mt-2">{lastResult.status_label}</p>
            <p className="text-sm text-emerald-700 mt-1">{lastResult.station}</p>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}
