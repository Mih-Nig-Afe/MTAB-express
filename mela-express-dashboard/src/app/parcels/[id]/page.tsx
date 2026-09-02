'use client';
import { Suspense, useState, useEffect } from 'react';
import useSWR from 'swr';
import { useParams, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import StatusBadge from '@/components/parcels/StatusBadge';
import StatusTimeline from '@/components/parcels/StatusTimeline';
import WaybillLabel from '@/components/parcels/WaybillLabel';
import ProofOfDeliveryModal from '@/components/parcels/ProofOfDeliveryModal';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Parcel, Branch } from '@/types';
import { useToast } from '@/components/ui/Toast';
import { useTranslation, labelFor } from '@/lib/i18n';
import { useAuth } from '@/lib/auth';
import Link from 'next/link';

const fetcher = (url: string) => api.get(url).then(res => res.data);

function LoadingFallback() {
  const { t } = useTranslation();
  return <div className="text-center py-10 text-gray-500">{t('loading')}</div>;
}

export default function ParcelDetailPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <ParcelDetail />
    </Suspense>
  );
}

function ParcelDetail() {
  const { id } = useParams();
  const searchParams = useSearchParams();
  const toast = useToast();
  const { t } = useTranslation();
  const { user } = useAuth();
  const canOverrideStatus = user?.role === 'admin' || user?.role === 'manager';
  const { data: parcel, error, isLoading, mutate } = useSWR<Parcel>(`/parcels/${id}`, fetcher);
  const { data: branches } = useSWR<Branch[]>('/branches', fetcher);
  
  const [newStatus, setNewStatus] = useState('');
  const [note, setNote] = useState('');
  const [flightNumber, setFlightNumber] = useState('');
  const [originAirport, setOriginAirport] = useState('');
  const [destAirport, setDestAirport] = useState('');
  const [updating, setUpdating] = useState(false);
  const [showWaybill, setShowWaybill] = useState(false);
  const [showPoDModal, setShowPoDModal] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);

  useEffect(() => {
    if (searchParams.get('sticker') === '1' && parcel) {
      setShowWaybill(true);
    }
  }, [searchParams, parcel]);

  const originName = branches?.find(b => b.id === parcel?.origin_branch_id)?.name || parcel?.origin_branch_id || t('origin_fallback');
  const destName = branches?.find(b => b.id === parcel?.destination_branch_id)?.name || parcel?.destination_branch_id || t('destination_fallback');

  const handleStatusUpdate = async () => {
    if (!newStatus) return;
    setUpdating(true);
    try {
      await api.patch(`/parcels/${id}/status`, {
        to_status: newStatus,
        note,
        flight_number: flightNumber || undefined,
        origin_airport_iata: originAirport || undefined,
        destination_airport_iata: destAirport || undefined,
      });
      toast.success(t('status_updated_msg').replace('{status}', t(`status_${newStatus}`)), t('status_updated_title'));
      setNewStatus('');
      setNote('');
      mutate();
    } catch (err: any) {
      const detail = err.response?.data?.detail || t('failed_update_status');
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail), t('transition_error_title'));
    } finally {
      setUpdating(false);
    }
  };

  const handleCollectCash = async () => {
    if (typeof window !== 'undefined' && !window.confirm(t('confirm_collect_cash').replace('{amount}', formatCurrency(parcel?.price || 0)))) {
      return;
    }
    try {
      await api.post(`/payments/cash/${id}/collect`, { override_reason: '' });
      toast.success(t('collected_cash_msg').replace('{amount}', formatCurrency(parcel?.price || 0)), t('collected_cash_title'));
      mutate();
    } catch (err: any) {
      const detail = err.response?.data?.detail || t('failed_record_cash');
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail), t('payment_failed_title'));
    }
  };

  if (isLoading) return <RoleGuard><div className="p-8 text-center text-gray-500">{t('loading_parcel_details')}</div></RoleGuard>;
  if (error || !parcel) return <RoleGuard><div className="p-8 text-center text-rose-500">{t('error_loading_parcel_details')}</div></RoleGuard>;

  const statuses = parcel?.allowed_next?.length
    ? parcel.allowed_next
    : ['received_at_origin', 'processed_at_origin', 'dispatched_from_origin', 'in_transit', 'arrived_origin_airport', 'checked_in_flight', 'departed', 'arrived_destination_airport', 'released_from_airport', 'arrived_at_destination', 'distributed_to_branch', 'ready_for_pickup', 'delivered', 'returned', 'cancelled', 'on_hold'];
  const needsFlight = newStatus === 'checked_in_flight' || newStatus === 'departed';

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
            <p className="text-xs sm:text-sm text-gray-500 mt-1">{t('registered_on')} {formatDate(parcel.created_at)}</p>
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
                {t('shipment_details')}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-5 gap-x-6 text-sm">
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">{t('sender_label')}</dt>
                  <dd className="font-semibold text-gray-900 mt-1 text-sm">{parcel.sender_phone}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">{t('receiver_label')}</dt>
                  <dd className="font-bold text-gray-900 mt-1 text-sm">{parcel.receiver_name}</dd>
                  <dd className="font-mono text-xs text-gray-500">{parcel.receiver_phone}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">{t('route')}</dt>
                  <dd className="font-bold text-blue-600 mt-1 text-sm">{originName} ➔ {destName}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">{t('weight_price')}</dt>
                  <dd className="font-bold text-gray-900 mt-1 text-sm">{parcel.weight_kg || 1} {t('kg_short')} — {formatCurrency(parcel.price)}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">{t('contents')}</dt>
                  <dd className="text-gray-700 mt-1 text-sm">{parcel.description || t('general_cargo')}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-xs uppercase font-bold tracking-wider">{t('payment_status_label')}</dt>
                  <dd className="mt-1">
                    <span className={`px-2.5 py-1 text-xs font-extrabold rounded-full ${parcel.payment_status === 'paid' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                      {t(`payment_${parcel.payment_status}`)}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">({parcel.payment_mode === 'before' ? t('mode_before') : t('mode_after')})</span>
                  </dd>
                </div>
              </div>
              
              {parcel.payment_status === 'pending' && (
                <div className="mt-6 pt-6 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs text-amber-800 font-bold block">{t('payment_pending_note')}</span>
                    <span className="text-xs text-gray-500">{t('amount_due')} {formatCurrency(parcel.price)}</span>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => setShowQrModal(true)} 
                      className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1"
                    >
                      {t('qr_button')}
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

            {/* Status — scan-first for operators; manual override for admin/manager */}
            {canOverrideStatus ? (
            <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 sm:p-7">
              <h2 className="text-base font-extrabold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
                {t('update_lifecycle')}
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">{t('next_stage_label')}</label>
                  <select 
                    value={newStatus} 
                    onChange={e => setNewStatus(e.target.value)} 
                    className="w-full border border-gray-300 rounded-2xl px-4 py-3 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition"
                  >
                    <option value="">{t('select_status_placeholder')}</option>
                    {statuses.map(s => <option key={s} value={s}>{t(`status_${s}`)}</option>)}
                  </select>
                </div>
                {needsFlight && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="sm:col-span-1">
                      <label className="block text-xs font-bold text-gray-700 uppercase mb-1">{t('flight_number')}</label>
                      <input
                        value={flightNumber}
                        onChange={e => setFlightNumber(e.target.value.toUpperCase())}
                        placeholder={t('flight_number_placeholder')}
                        className="w-full border border-gray-300 rounded-2xl px-4 py-3 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-700 uppercase mb-1">{t('origin_airport')}</label>
                      <input
                        value={originAirport}
                        onChange={e => setOriginAirport(e.target.value.toUpperCase())}
                        placeholder="ADD"
                        className="w-full border border-gray-300 rounded-2xl px-4 py-3 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-700 uppercase mb-1">{t('dest_airport')}</label>
                      <input
                        value={destAirport}
                        onChange={e => setDestAirport(e.target.value.toUpperCase())}
                        placeholder="DIR"
                        className="w-full border border-gray-300 rounded-2xl px-4 py-3 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                  </div>
                )}
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">{t('status_note_optional')}</label>
                  <input 
                    type="text" 
                    placeholder={t('status_note_placeholder')} 
                    value={note} 
                    onChange={e => setNote(e.target.value)} 
                    className="w-full border border-gray-300 rounded-2xl px-4 py-3 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" 
                  />
                </div>
                <button 
                  onClick={handleStatusUpdate} 
                  disabled={!newStatus || updating || (needsFlight && !flightNumber)} 
                  className="w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white py-3 px-4 rounded-2xl text-sm font-bold shadow-md shadow-blue-500/20 disabled:opacity-50 transition"
                >
                  {updating ? t('updating_status') : t('apply_status_update')}
                </button>
              </div>
            </div>
            ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-3xl p-6 text-center">
              <p className="text-sm text-blue-900 font-semibold mb-3">{t('scan_station_hint')}</p>
              <Link href="/scan" className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl text-sm font-bold transition">
                📷 {t('scan_nav')}
              </Link>
            </div>
            )}
          </div>

          {/* Timeline Audit History */}
          <div className="space-y-6">
            {(parcel.eta || parcel.flight) && (
              <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 sm:p-7">
                <h2 className="text-base font-extrabold text-gray-900 mb-4">{t('flight_section')}</h2>
                {parcel.eta && (
                  <div className="mb-4 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <dt className="text-gray-400 text-xs uppercase font-bold">{t('eta_label')}</dt>
                      <dd className="font-semibold mt-1">{parcel.eta.current_eta_at ? formatDate(parcel.eta.current_eta_at) : '—'}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-400 text-xs uppercase font-bold">{t('promised_label')}</dt>
                      <dd className="font-semibold mt-1">{parcel.eta.promised_delivery_at ? formatDate(parcel.eta.promised_delivery_at) : '—'}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-400 text-xs uppercase font-bold">{t('remaining_label')}</dt>
                      <dd className="font-semibold mt-1">{parcel.eta.remaining_minutes} {t('minutes_short')}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-400 text-xs uppercase font-bold">{parcel.eta.on_time === false ? t('delayed') : t('on_time')}</dt>
                      <dd className="font-semibold mt-1">{parcel.eta.delay_minutes} {t('minutes_short')}</dd>
                    </div>
                  </div>
                )}
                {parcel.flight && (
                  <div className="text-sm border-t border-gray-100 pt-4 space-y-1">
                    <p className="font-bold text-gray-900">{parcel.flight.flight_number} · {parcel.flight.origin_iata || '—'} → {parcel.flight.dest_iata || '—'}</p>
                    <p className="text-gray-500 capitalize">{labelFor(t, 'status_', parcel.flight.status)}{parcel.flight.airline_name ? ` · ${parcel.flight.airline_name}` : ''}</p>
                    {parcel.flight.latitude != null && parcel.flight.longitude != null && (
                      <p className="text-gray-500">{t('live_position')}: {Number(parcel.flight.latitude).toFixed(3)}, {Number(parcel.flight.longitude).toFixed(3)}</p>
                    )}
                  </div>
                )}
              </div>
            )}
            <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 sm:p-7">
            <h2 className="text-base font-extrabold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
              {t('audit_history')}
            </h2>
            <StatusTimeline history={parcel.status_history || []} />
            </div>
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
              <h3 className="font-extrabold text-gray-900 text-lg mb-1">{t('scan_pay_title')}</h3>
              <p className="text-xs text-gray-500 mb-4">{t('amount_label')} <span className="font-bold text-gray-900">{formatCurrency(parcel.price)}</span></p>
              
              <div className="bg-gray-100 p-6 rounded-2xl inline-block mb-4 border border-gray-200">
                {/* Visual QR Code Display */}
                <div className="w-44 h-44 bg-white p-3 rounded-xl shadow-sm flex flex-col items-center justify-center border">
                  <div className="w-36 h-36 bg-[radial-gradient(#000_2px,transparent_2px)] [background-size:8px_8px] border-2 border-black p-2 flex items-center justify-center font-mono font-bold text-xs">
                    [CBE / Telebirr QR]
                  </div>
                </div>
              </div>
              
              <p className="text-xs text-gray-600 mb-6">{t('scan_pay_hint')}</p>
              
              <button
                onClick={() => setShowQrModal(false)}
                className="w-full py-3 bg-gray-100 hover:bg-gray-200 font-bold rounded-2xl text-sm transition"
              >
                {t('close')}
              </button>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}
