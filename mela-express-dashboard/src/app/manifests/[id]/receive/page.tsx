'use client';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { Manifest, Parcel } from '@/types';
import { useToast } from '@/components/ui/Toast';

export default function ReceiveManifest() {
  const { id } = useParams();
  const router = useRouter();
  const toast = useToast();
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get(`/manifests/${id}`)
      .then(res => {
        setManifest(res.data);
        if (res.data.parcels) {
          setSelected(new Set(res.data.parcels.map((p: Parcel) => p.id)));
        }
      })
      .catch(() => toast.error('Failed to load manifest details'));
  }, [id, toast]);

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
        toast.warning(`Received ${received} parcels. ${missing} unverified parcels marked ON HOLD.`, 'Bulk Received with Exceptions');
      } else {
        toast.success(`All ${received} parcels verified and received at destination!`, 'Manifest Received');
      }
      router.push(`/manifests/${id}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to process manifest arrival');
    } finally {
      setSubmitting(false);
    }
  };

  if (!manifest) {
    return <RoleGuard><div className="p-8 text-center text-gray-500">Loading manifest...</div></RoleGuard>;
  }

  const parcels = manifest.parcels || [];

  return (
    <RoleGuard allowedRoles={['admin', 'manager', 'operator']}>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Destination Bulk Check-In</h1>
            <p className="text-sm text-gray-500 mt-1">
              Verify incoming packages for vehicle <span className="font-semibold text-gray-800">{manifest.vehicle_plate}</span> (Driver: {manifest.driver_name})
            </p>
          </div>
          <button 
            type="button" 
            onClick={handleSelectAll}
            className="text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition"
          >
            {selected.size === parcels.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-4">
          <h2 className="text-sm font-semibold text-gray-700 uppercase">
            Parcels in Manifest ({selected.size}/{parcels.length} Verified)
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
                      <p className="text-xs text-gray-500 mt-0.5">Receiver: {p.receiver_name} ({p.receiver_phone})</p>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold text-gray-800 text-xs block">{p.weight_kg} kg</span>
                      <span className={`text-xs font-medium ${isChecked ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {isChecked ? '✓ Verified Present' : '⚠ Missing / Unchecked'}
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
              Cancel
            </button>
            <button 
              onClick={handleSubmit} 
              disabled={submitting} 
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-emerald-500/20 disabled:opacity-50 transition"
            >
              {submitting ? 'Confirming...' : `Confirm Bulk Arrival (${selected.size} Received)`}
            </button>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}