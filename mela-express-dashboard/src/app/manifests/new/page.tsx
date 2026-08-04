'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { Branch, Parcel } from '@/types';
import { useToast } from '@/components/ui/Toast';

export default function NewManifestPage() {
  const router = useRouter();
  const toast = useToast();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [availableParcels, setAvailableParcels] = useState<Parcel[]>([]);
  const [selectedParcels, setSelectedParcels] = useState<Set<string>>(new Set());
  const [loadingParcels, setLoadingParcels] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    origin_branch_id: '',
    destination_branch_id: '',
    driver_name: '',
    vehicle_plate: '',
    notes: ''
  });

  useEffect(() => {
    api.get('/branches').then(res => {
      setBranches(res.data);
      if (res.data.length >= 2) {
        setFormData(prev => ({
          ...prev,
          origin_branch_id: res.data[0].id,
          destination_branch_id: res.data[1].id
        }));
      }
    });
  }, []);

  useEffect(() => {
    if (!formData.origin_branch_id) return;
    setLoadingParcels(true);
    api.get(`/parcels?size=50`)
      .then(res => {
        const parcels = res.data.items || [];
        const filtered = parcels.filter((p: Parcel) => 
          p.origin_branch_id === formData.origin_branch_id &&
          ['created', 'received_at_origin'].includes(p.status)
        );
        setAvailableParcels(filtered);
        setSelectedParcels(new Set(filtered.map((p: Parcel) => p.id)));
      })
      .catch(() => setAvailableParcels([]))
      .finally(() => setLoadingParcels(false));
  }, [formData.origin_branch_id, formData.destination_branch_id]);

  const toggleParcel = (id: string) => {
    const next = new Set(selectedParcels);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedParcels(next);
  };

  const toggleAll = () => {
    if (selectedParcels.size === availableParcels.length) {
      setSelectedParcels(new Set());
    } else {
      setSelectedParcels(new Set(availableParcels.map(p => p.id)));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.origin_branch_id === formData.destination_branch_id) {
      toast.warning('Origin and destination branches must be different.', 'Validation Error');
      return;
    }

    if (selectedParcels.size === 0) {
      toast.warning('Please select at least one parcel to include in this manifest.', 'No Parcels Selected');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        parcel_ids: Array.from(selectedParcels)
      };
      const res = await api.post('/manifests', payload);
      toast.success(`Manifest created with ${selectedParcels.size} parcels!`, 'Manifest Dispatched');
      router.push(`/manifests/${res.data.id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to create manifest.';
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail), 'Creation Failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <RoleGuard allowedRoles={['admin', 'manager', 'operator']}>
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create Transfer Manifest</h1>
          <p className="text-sm text-gray-500 mt-1">Batch parcels for inter-city transit and assign driver/vehicle.</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-200 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Origin Branch</label>
              <select 
                value={formData.origin_branch_id} 
                onChange={e => setFormData({...formData, origin_branch_id: e.target.value})} 
                className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                {branches.map(b => <option key={b.id} value={b.id}>{b.name} ({b.code})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Destination Branch</label>
              <select 
                value={formData.destination_branch_id} 
                onChange={e => setFormData({...formData, destination_branch_id: e.target.value})} 
                className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                {branches.map(b => <option key={b.id} value={b.id}>{b.name} ({b.code})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Driver Name</label>
              <input 
                required 
                type="text" 
                placeholder="e.g. Dawit Bekele"
                value={formData.driver_name} 
                onChange={e => setFormData({...formData, driver_name: e.target.value})} 
                className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Vehicle Plate Number</label>
              <input 
                required 
                type="text" 
                placeholder="e.g. 3-AA-12345"
                value={formData.vehicle_plate} 
                onChange={e => setFormData({...formData, vehicle_plate: e.target.value})} 
                className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-3">
              <label className="block text-sm font-semibold text-gray-700">
                Select Parcels to Dispatch ({selectedParcels.size} selected)
              </label>
              {availableParcels.length > 0 && (
                <button
                  type="button"
                  onClick={toggleAll}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                >
                  {selectedParcels.size === availableParcels.length ? 'Deselect All' : 'Select All'}
                </button>
              )}
            </div>

            {loadingParcels ? (
              <div className="text-center py-6 text-gray-400 text-sm">Loading available parcels at origin...</div>
            ) : availableParcels.length === 0 ? (
              <div className="p-4 bg-gray-50 rounded-xl border border-dashed border-gray-300 text-center text-sm text-gray-500">
                No ready parcels found at this origin branch.
              </div>
            ) : (
              <div className="border border-gray-200 rounded-xl max-h-64 overflow-y-auto divide-y divide-gray-100">
                {availableParcels.map(p => (
                  <label key={p.id} className="flex items-center gap-3 p-3 hover:bg-blue-50/50 cursor-pointer transition">
                    <input 
                      type="checkbox" 
                      checked={selectedParcels.has(p.id)} 
                      onChange={() => toggleParcel(p.id)} 
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1 flex justify-between items-center text-sm">
                      <span className="font-mono font-medium text-gray-900">{p.tracking_code}</span>
                      <span className="text-gray-500 text-xs">{p.receiver_name} ({p.receiver_phone})</span>
                      <span className="font-semibold text-gray-700 text-xs">{p.weight_kg} kg</span>
                    </div>
                  </label>
                ))}
              </div>
            )}
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
              type="submit" 
              disabled={submitting || selectedParcels.size === 0} 
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-blue-500/20 disabled:opacity-50 transition"
            >
              {submitting ? 'Creating Manifest...' : `Dispatch Manifest (${selectedParcels.size} Parcels)`}
            </button>
          </div>
        </form>
      </div>
    </RoleGuard>
  );
}