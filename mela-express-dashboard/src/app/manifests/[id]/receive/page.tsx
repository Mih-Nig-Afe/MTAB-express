'use client';
import { useTranslation } from '@/lib/i18n';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { Manifest, Parcel } from '@/types';
import { useToast } from '@/components/ui/Toast';

export default function ReceiveManifest() {
  const { t } = useTranslation();
  const { id } = useParams();
  const router = useRouter();
  const toast = useToast();
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [scanCode, setScanCode] = useState('');
  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    if (!scanCode.trim()) return;
    setScanning(true);
    try {
      const res = await api.post(`/manifests/${id}/scan`, { code: scanCode.trim() });
      const parcel = manifest?.parcels?.find(p => p.tracking_code === res.data.tracking_code);
      if (parcel) {
        setSelected(prev => new Set([...prev, parcel.id]));
      }
      toast.success(res.data.message, t('scan_success_title'));
      setScanCode('');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || t('scan_failed'));
    } finally {
      setScanning(false);
    }
  };

  useEffect(() => {
    api.get(`/manifests/${id}`)
      .then(res => {
        setManifest(res.data);
        if (res.data.parcels) {
          setSelected(new Set(res.data.parcels.map((p: Parcel) => p.id)));
        }
      })
      .catch(() => toast.error(t('failed_load_manifest')));
  }, [id, toast, t]);

  const handleToggle = (parcelId: string) => {
    const next = new Set(selected);
    if (next.has(parcelId)) next.delete(parcelId);
    else next.add(parcelId);
    setSelected(next);
  };

  const handleSelectAll = () => {
    if (!manifest?.parcels) return;
    if (selected.size === manifest.parcels.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(manifest.parcels.map(p => p.id)));
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await api.post(`/manifests/${id}/receive`, { received_parcel_ids: Array.from(selected) });
      const total = manifest?.parcels?.length || 0;
      const received = selected.size;
      const missing = total - received;

      if (missing > 0) {
        toast.warning(t('received_with_hold', { received, missing }), t('bulk_received_exceptions'));
      } else {
        toast.success(t('all_parcels_received', { count: received }), t('manifest_received'));
      }
      router.push(`/manifests/${id}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || t('failed_process_arrival'));
    } finally {
      setSubmitting(false);
    }
  };

  if (!manifest) {
    return <RoleGuard><div className="p-8 text-center text-gray-500">{t('loading')}</div></RoleGuard>;
  }

  const parcels = manifest.parcels || [];

  return (
    <RoleGuard allowedRoles={['admin', 'manager', 'operator']}>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('receive')} — {t('destination')}</h1>
            <p className="text-sm text-gray-500 mt-1">
              {t('receive_incoming_hint', { plate: manifest.vehicle_plate || '', driver: manifest.driver_name || '' })}
            </p>
          </div>
          <button 
            type="button" 
            onClick={handleSelectAll}
            className="text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition"
          >
            {selected.size === parcels.length ? t('deselect_all') : t('select_all')}
          </button>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-4">
          <div className="flex gap-2">
            <input
              value={scanCode}
              onChange={e => setScanCode(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), handleScan())}
              placeholder={t('scan_or_type_code')}
              className="flex-1 font-mono border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
            <button
              type="button"
              onClick={handleScan}
              disabled={scanning || !scanCode.trim()}
              className="px-5 py-3 bg-blue-600 text-white font-semibold rounded-xl text-sm disabled:opacity-50"
            >
              {scanning ? t('scanning') : t('confirm_scan')}
            </button>
          </div>

          <h2 className="text-sm font-semibold text-gray-700 uppercase">
            {t('parcels_in_manifest', { selected: selected.size, total: parcels.length })}
          </h2>
          
          <div className="divide-y divide-gray-100 border border-gray-200 rounded-xl overflow-hidden">
            {parcels.map((p) => {
              const isChecked = selected.has(p.id);
              return (
                <label 
                  key={p.id} 
                  className={`flex items-center gap-4 p-4 cursor-pointer transition ${
                    isChecked ? 'bg-blue-50/40' : 'bg-rose-50/20 opacity-75'
                  }`}
                >
                  <input 
                    type="checkbox" 
                    checked={isChecked} 
                    onChange={() => handleToggle(p.id)} 
                    className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1 flex justify-between items-center text-sm">
                    <div>
                      <span className="font-mono font-bold text-gray-900">{p.tracking_code}</span>
                      <p className="text-xs text-gray-500 mt-0.5">{t('receiver_label')}: {p.receiver_name} ({p.receiver_phone})</p>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold text-gray-800 text-xs block">{p.weight_kg} {t('kg_short')}</span>
                      <span className={`text-xs font-medium ${isChecked ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {isChecked ? t('verified_present') : t('missing_unchecked')}
                      </span>
                    </div>
                  </div>
                </label>
              );
            })}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button 
              type="button" 
              onClick={() => router.back()} 
              className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl text-sm transition"
            >
              {t('cancel')}
            </button>
            <button 
              onClick={handleSubmit} 
              disabled={submitting} 
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-emerald-500/20 disabled:opacity-50 transition"
            >
              {submitting ? t('confirming') : t('confirm_bulk_arrival', { count: selected.size })}
            </button>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}
