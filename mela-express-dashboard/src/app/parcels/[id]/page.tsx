'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import StatusBadge from '@/components/parcels/StatusBadge';
import StatusTimeline from '@/components/parcels/StatusTimeline';
import WaybillLabel from '@/components/parcels/WaybillLabel';
import ProofOfDeliveryModal from '@/components/parcels/ProofOfDeliveryModal';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Parcel, Branch } from '@/types';
import { useToast } from '@/components/ui/Toast';
import { useTranslation } from '@/lib/i18n';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function ParcelDetail() {
  const { id } = useParams();
  const toast = useToast();
  const { t } = useTranslation();
  const { data: parcel, error, isLoading, mutate } = useSWR<Parcel>(`/parcels/${id}`, fetcher);
  const { data: branches } = useSWR<Branch[]>('/branches', fetcher);
  
  const [newStatus, setNewStatus] = useState('');
  const [note, setNote] = useState('');
  const [updating, setUpdating] = useState(false);
  const [showWaybill, setShowWaybill] = useState(false);
  const [showPoDModal, setShowPoDModal] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);

  const originName = branches?.find(b => b.id === parcel?.origin_branch_id)?.name || parcel?.origin_branch_id || 'Origin';
  const destName = branches?.find(b => b.id === parcel?.destination_branch_id)?.name || parcel?.destination_branch_id || 'Destination';

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

  const handleCollectCash = async () => {
    try {
      await api.post(`/payments/cash/${id}/collect`, { override_reason: '' });
      toast.success(`Collected ${formatCurrency(parcel?.price || 0)} ETB in cash!`, 'Payment Received');
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
        {/* Top Header Card */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-3xl shadow-sm border border-gray-200">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl sm:text-3xl font-extrabold text-gray-900 font-mono tracking-wide">
                {parcel.tracking_code}
              </span>
              <StatusBadge status={parcel.status} />
            </div>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">Registered on {formatDate(parcel.created_at)}</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setShowWaybill(true)}
              className="bg-gray-100 hover:bg-gray-200 text-gray-800 font-bold px-4 py-2.5 rounded-2xl text-xs sm:text-sm transition flex items-center gap-1.5 shadow-sm"
            >
              🖨️ {t('print_waybill')}
            </button>

            {parcel.status !== 'delivered' && (
              <button
                onClick={() => setShowPoDModal(true)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2.5 rounded-2xl text-xs sm:text-sm shadow-md shadow-emerald-500/20 transition flex items-center gap-1.5"
              >
                🔐 {t('handover_pod')}
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            {/* Details Section */}
            <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 sm:p-7">
              <h2 className="text-base font-extrabold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
                📦 Shipment Details
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-5 gap-x-6 text-sm">
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">Sender</dt>
                  <dd className="font-semibold text-gray-900 mt-1 text-sm">{parcel.sender_phone}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">Receiver</dt>
                  <dd className="font-bold text-gray-900 mt-1 text-sm">{parcel.receiver_name}</dd>
                  <dd className="font-mono text-xs text-gray-500">{parcel.receiver_phone}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">Route</dt>
                  <dd className="font-bold text-blue-600 mt-1 text-sm">{originName} ➔ {destName}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">Weight & Price</dt>
                  <dd className="font-bold text-gray-900 mt-1 text-sm">{parcel.weight_kg || 1} kg — {formatCurrency(parcel.price)}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">Contents</dt>
                  <dd className="text-gray-700 mt-1 text-sm">{parcel.description || 'General Cargo'}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">Payment Status</dt>
                  <dd className="mt-1">
                    <span className={`px-2.5 py-1 text-xs font-extrabold rounded-full ${parcel.payment_status === 'paid' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                      {parcel.payment_status.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 ml-2 capitalize">({parcel.payment_mode})</span>
                  </dd>
                </div>
              </div>
              
              {parcel.payment_status === 'pending' && (
                <div className="mt-6 pt-6 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs text-amber-800 font-bold block">⚠️ Payment is pending for this parcel</span>
                    <span className="text-xs text-gray-500">Amount due: {formatCurrency(parcel.price)}</span>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => setShowQrModal(true)} 
                      className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1"
                    >
                      📱 Telebirr / CBE QR
                    </button>
                    <button 
                      onClick={handleCollectCash} 
                      className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
                    >
                      💵 {t('collect_cash')}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Status Update Card */}
            <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 sm:p-7">
              <h2 className="text-base font-extrabold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
                🔄 Update Lifecycle Status
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Next Lifecycle Stage</label>
                  <select 
                    value={newStatus} 
                    onChange={e => setNewStatus(e.target.value)} 
                    className="w-full border border-gray-300 rounded-2xl px-4 py-3 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition"
                  >
                    <option value="">Select status to transition...</option>
                    {statuses.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ').toUpperCase()}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Status Note (Optional)</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Scanned at warehouse sorting area..." 
                    value={note} 
                    onChange={e => setNote(e.target.value)} 
                    className="w-full border border-gray-300 rounded-2xl px-4 py-3 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" 
                  />
                </div>
                <button 
                  onClick={handleStatusUpdate} 
                  disabled={!newStatus || updating} 
                  className="w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white py-3 px-4 rounded-2xl text-sm font-bold shadow-md shadow-blue-500/20 disabled:opacity-50 transition"
                >
                  {updating ? 'Updating Status...' : 'Apply Status Update'}
                </button>
              </div>
            </div>
          </div>

          {/* Timeline Audit History */}
          <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 sm:p-7">
            <h2 className="text-base font-extrabold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
              📜 Audit History
            </h2>
            <StatusTimeline history={parcel.status_history || []} />
          </div>
        </div>

        {/* Thermal Sticker Modal */}
        {showWaybill && (
          <WaybillLabel 
            parcel={parcel} 
            originName={originName} 
            destName={destName} 
            onClose={() => setShowWaybill(false)} 
          />
        )}

        {/* Proof of Delivery OTP & Touch Signature Modal */}
        {showPoDModal && (
          <ProofOfDeliveryModal
            parcel={parcel}
            onClose={() => setShowPoDModal(false)}
            onSuccess={() => {
              setShowPoDModal(false);
              mutate();
            }}
          />
        )}

        {/* Telebirr / CBE QR Modal */}
        {showQrModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-sm w-full shadow-2xl text-center">
              <h3 className="font-extrabold text-gray-900 text-lg mb-1">📱 Scan & Pay</h3>
              <p className="text-xs text-gray-500 mb-4">Amount: <span className="font-bold text-gray-900">{formatCurrency(parcel.price)}</span></p>
              
              <div className="bg-gray-100 p-6 rounded-2xl inline-block mb-4 border border-gray-200">
                {/* Visual QR Code Display */}
                <div className="w-44 h-44 bg-white p-3 rounded-xl shadow-sm flex flex-col items-center justify-center border">
                  <div className="w-36 h-36 bg-[radial-gradient(#000_2px,transparent_2px)] [background-size:8px_8px] border-2 border-black p-2 flex items-center justify-center font-mono font-bold text-xs">
                    [CBE / Telebirr QR]
                  </div>
                </div>
              </div>
              
              <p className="text-xs text-gray-600 mb-6">Customer can scan with Telebirr or CBE Birr app.</p>
              
              <button
                onClick={() => setShowQrModal(false)}
                className="w-full py-3 bg-gray-100 hover:bg-gray-200 font-bold rounded-2xl text-sm transition"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}