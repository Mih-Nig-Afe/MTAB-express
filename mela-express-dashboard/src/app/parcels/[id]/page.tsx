'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import StatusBadge from '@/components/parcels/StatusBadge';
import StatusTimeline from '@/components/parcels/StatusTimeline';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Parcel, Branch } from '@/types';
import { useToast } from '@/components/ui/Toast';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function ParcelDetail() {
  const { id } = useParams();
  const toast = useToast();
  const { data: parcel, error, isLoading, mutate } = useSWR<Parcel>(`/parcels/${id}`, fetcher);
  const { data: branches } = useSWR<Branch[]>('/branches', fetcher);
  
  const [newStatus, setNewStatus] = useState('');
  const [note, setNote] = useState('');
  const [updating, setUpdating] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [showOverrideModal, setShowOverrideModal] = useState(false);

  const originName = branches?.find(b => b.id === parcel?.origin_branch_id)?.name || parcel?.origin_branch_id;
  const destName = branches?.find(b => b.id === parcel?.destination_branch_id)?.name || parcel?.destination_branch_id;

  const handleStatusUpdate = async () => {
    if (!newStatus) return;
    setUpdating(true);
    try {
      await api.patch(`/parcels/${id}/status`, { to_status: newStatus, note });
      toast.success(`Parcel status updated to ${newStatus.replace(/_/g, ' ').toUpperCase()}`, 'Status Updated');
      setNewStatus('');
      setNote('');
      mutate();
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to update status.';
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail), 'Transition Error');
    } finally {
      setUpdating(false);
    }
  };

  const handleCollectCash = async (reason = '') => {
    try {
      await api.post(`/payments/cash/${id}/collect`, { override_reason: reason });
      toast.success(`Collected ${formatCurrency(parcel?.price || 0)} ETB in cash!`, 'Payment Received');
      setShowOverrideModal(false);
      mutate();
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to record cash payment.';
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail), 'Payment Failed');
    }
  };

  if (isLoading) return <RoleGuard><div className="p-8 text-center text-gray-500">Loading parcel details...</div></RoleGuard>;
  if (error || !parcel) return <RoleGuard><div className="p-8 text-center text-rose-500">Error loading parcel details.</div></RoleGuard>;

  const statuses = ['received_at_origin', 'in_transit', 'arrived_at_destination', 'ready_for_pickup', 'delivered', 'returned', 'cancelled', 'on_hold'];

  return (
    <RoleGuard>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl sm:text-3xl font-extrabold text-gray-900 font-mono tracking-wide">
                {parcel.tracking_code}
              </span>
              <StatusBadge status={parcel.status} />
            </div>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">Registered on {formatDate(parcel.created_at)}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 text-xs font-semibold rounded-full ${parcel.payment_status === 'paid' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
              Payment: {parcel.payment_status.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-base font-bold text-gray-900 mb-4 pb-2 border-b border-gray-100 flex items-center gap-2">
                📦 Shipment Details
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6 text-sm">
                <div>
                  <dt className="text-gray-500 text-xs uppercase font-medium">Sender</dt>
                  <dd className="font-semibold text-gray-900 mt-0.5">{parcel.sender_phone}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase font-medium">Receiver</dt>
                  <dd className="font-semibold text-gray-900 mt-0.5">{parcel.receiver_name} ({parcel.receiver_phone})</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase font-medium">Route</dt>
                  <dd className="font-semibold text-blue-600 mt-0.5">{originName} ➔ {destName}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase font-medium">Weight & Fee</dt>
                  <dd className="font-semibold text-gray-900 mt-0.5">{parcel.weight_kg} kg — {formatCurrency(parcel.price)}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-gray-500 text-xs uppercase font-medium">Description</dt>
                  <dd className="text-gray-700 mt-0.5">{parcel.description || 'No package description'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase font-medium">Payment Mode</dt>
                  <dd className="font-semibold text-gray-800 mt-0.5 capitalize">{parcel.payment_mode} (Method: {parcel.payment_method})</dd>
                </div>
              </div>
              
              {parcel.payment_status === 'pending' && (
                <div className="mt-6 pt-6 border-t border-gray-100 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-amber-700 font-semibold block">⚠️ Payment is pending for this parcel</span>
                    <span className="text-xs text-gray-500">Amount due: {formatCurrency(parcel.price)}</span>
                  </div>
                  <button 
                    onClick={() => handleCollectCash('')} 
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold shadow-sm transition flex items-center gap-1.5"
                  >
                    💵 Collect Cash Payment
                  </button>
                </div>
              )}
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-base font-bold text-gray-900 mb-4 pb-2 border-b border-gray-100 flex items-center gap-2">
                🔄 Update Lifecycle Status
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Select Next Status</label>
                  <select 
                    value={newStatus} 
                    onChange={e => setNewStatus(e.target.value)} 
                    className="w-full border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                  >
                    <option value="">Select status to transition...</option>
                    {statuses.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ').toUpperCase()}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Status Note (Optional)</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Scanned at warehouse gate 2..." 
                    value={note} 
                    onChange={e => setNote(e.target.value)} 
                    className="w-full border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
                  />
                </div>
                <button 
                  onClick={handleStatusUpdate} 
                  disabled={!newStatus || updating} 
                  className="w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white py-2.5 px-4 rounded-xl text-sm font-semibold shadow-md shadow-blue-500/20 disabled:opacity-50 transition"
                >
                  {updating ? 'Updating Status...' : 'Apply Status Update'}
                </button>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-base font-bold text-gray-900 mb-4 pb-2 border-b border-gray-100 flex items-center gap-2">
              📜 Audit History
            </h2>
            <StatusTimeline history={parcel.status_history || []} />
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}