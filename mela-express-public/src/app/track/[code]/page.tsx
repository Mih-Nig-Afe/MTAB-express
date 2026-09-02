"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { use } from "react";
import { API_BASE_URL } from "@/lib/api";
import { useTranslation, LanguageToggle, labelFor } from '@/lib/i18n';

interface StatusEntry {
  to_status: string;
  timestamp: string;
  note?: string;
}

interface JourneyEvent {
  event_type: string;
  to_status?: string;
  location_name?: string;
  facility_type?: string;
  flight_number?: string;
  note?: string;
  source: string;
  created_at: string;
}

interface Checkpoint {
  location_name: string;
  latitude?: number;
  longitude?: number;
  note?: string;
  created_at: string;
}

interface FlightLeg {
  flight_number: string;
  origin_iata?: string;
  dest_iata?: string;
  status: string;
  delay_minutes?: number;
  latitude?: number;
  longitude?: number;
  scheduled_arrival?: string;
  airline_name?: string;
}

interface Eta {
  promised_delivery_at?: string;
  current_eta_at?: string;
  remaining_minutes: number;
  delay_minutes: number;
  on_time?: boolean | null;
}

interface ParcelData {
  tracking_code: string;
  status: string;
  status_label?: string;
  carrier_status_label?: string;
  payment_status: string;
  origin_branch_name: string;
  destination_branch_name: string;
  status_history: StatusEntry[];
  journey_events?: JourneyEvent[];
  checkpoints?: Checkpoint[];
  flight?: FlightLeg | null;
  eta?: Eta | null;
  created_at: string;
}

type TimelineItem = {
  key: string;
  label: string;
  detail?: string;
  at: string;
  kind: 'scan' | 'checkpoint' | 'history';
};

export default function TrackingPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { t } = useTranslation();
  const router = useRouter();
  const { code: rawCode } = use(params);
  const code = decodeURIComponent(rawCode);

  const [parcel, setParcel] = useState<ParcelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [searchCode, setSearchCode] = useState("");
  const [actionMsg, setActionMsg] = useState("");
  const [payLoading, setPayLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function fetchTracking(initial: boolean) {
      try {
        if (initial) setLoading(true);
        const res = await fetch(`${API_BASE_URL}/parcels/track/${encodeURIComponent(code)}`);
        if (!res.ok) {
          if (res.status === 404) {
            if (!cancelled) setError(true);
          } else {
            throw new Error(t('failed_to_fetch'));
          }
        } else {
          const data = await res.json();
          if (!cancelled) {
            setParcel(data);
            setError(false);
          }
        }
      } catch (err) {
        console.error(err);
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled && initial) setLoading(false);
      }
    }
    fetchTracking(true);
    const timer = setInterval(() => fetchTracking(false), 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [code]);

  const timeline = useMemo((): TimelineItem[] => {
    if (!parcel) return [];
    const items: TimelineItem[] = [];

    for (const e of parcel.journey_events || []) {
      const status = e.to_status || e.event_type;
      items.push({
        key: `j-${e.created_at}-${status}`,
        label: t('status_' + status) !== 'status_' + status
          ? t('status_' + status)
          : status.replace(/_/g, ' '),
        detail: [e.location_name, e.flight_number, e.note].filter(Boolean).join(' · '),
        at: e.created_at,
        kind: 'scan',
      });
    }
    for (const h of parcel.status_history || []) {
      items.push({
        key: `h-${h.timestamp}-${h.to_status}`,
        label: t('status_' + h.to_status) !== 'status_' + h.to_status
          ? t('status_' + h.to_status)
          : h.to_status.replace(/_/g, ' '),
        detail: h.note,
        at: h.timestamp,
        kind: 'history',
      });
    }
    for (const c of parcel.checkpoints || []) {
      items.push({
        key: `c-${c.created_at}`,
        label: t('checkpoint'),
        detail: c.location_name + (c.note ? ` — ${c.note}` : ''),
        at: c.created_at,
        kind: 'checkpoint',
      });
    }
    items.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
    const seen = new Set<string>();
    return items.filter((item) => {
      const sig = `${item.label}-${item.at.slice(0, 16)}`;
      if (seen.has(sig)) return false;
      seen.add(sig);
      return true;
    });
  }, [parcel, t]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchCode.trim()) {
      router.push(`/track/${encodeURIComponent(searchCode.trim())}`);
    }
  };

  const handlePay = async () => {
    if (!parcel) return;
    setPayLoading(true);
    setActionMsg("");
    try {
      const res = await fetch(`${API_BASE_URL}/payments/chapa/initiate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tracking_code: parcel.tracking_code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t('payment_failed'));
      if (data.checkout_url) window.location.href = data.checkout_url;
      else setActionMsg(t('payment_confirmed'));
    } catch (e: any) {
      setActionMsg(e.message);
    } finally {
      setPayLoading(false);
    }
  };

  const handleConfirmReceipt = async () => {
    if (!parcel) return;
    setActionMsg("");
    try {
      const res = await fetch(`${API_BASE_URL}/parcels/track/${parcel.tracking_code}/confirm_receipt`, {
        method: "POST",
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || t('could_not_confirm'));
      }
      setActionMsg(t('receipt_confirmed'));
    } catch (e: any) {
      setActionMsg(e.message);
    }
  };

  const getStatusBg = (status: string) => {
    const s = status.toLowerCase();
    if (s.includes("delivered")) return "bg-green-100 text-green-800";
    if (s.includes("transit") || s.includes("departed") || s.includes("flight")) return "bg-blue-100 text-blue-800";
    if (s.includes("pickup") || s.includes("ready")) return "bg-amber-100 text-amber-800";
    if (s.includes("hold") || s.includes("lost")) return "bg-red-100 text-red-800";
    return "bg-gray-100 text-gray-800";
  };

  const formatDate = (isoStr: string) => {
    try {
      return new Intl.DateTimeFormat(undefined, {
        month: "short", day: "numeric", year: "numeric",
        hour: "numeric", minute: "numeric",
      }).format(new Date(isoStr));
    } catch {
      return isoStr;
    }
  };

  const statusDisplay = parcel
    ? (labelFor(t, 'status_', parcel.status) || parcel.carrier_status_label || parcel.status_label)
    : '';

  const mapUrl = parcel?.flight?.latitude != null && parcel?.flight?.longitude != null
    ? `https://www.openstreetmap.org/?mlat=${parcel.flight.latitude}&mlon=${parcel.flight.longitude}#map=8/${parcel.flight.latitude}/${parcel.flight.longitude}`
    : null;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center cursor-pointer" onClick={() => router.push("/")}>
            <span className="text-2xl mr-2">📦</span>
            <h1 className="text-xl font-bold">{t('brand')}</h1>
          </div>
          <LanguageToggle />
        </div>
      </header>

      <main className="flex-grow max-w-3xl w-full mx-auto p-4 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : error || !parcel ? (
          <div className="bg-white rounded-xl shadow p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">{t('not_found_title')}</h2>
            <p className="text-gray-600 mb-6">{t('not_found_body').replace('{code}', code)}</p>
            <form onSubmit={handleSearch} className="max-w-md mx-auto flex gap-2">
              <input
                type="text"
                placeholder={t('search_placeholder')}
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                className="flex-grow px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                required
              />
              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition">
                {t('search')}
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                  <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">{t('tracking_code')}</p>
                  <h2 className="text-2xl md:text-3xl font-bold text-gray-900 font-mono">{parcel.tracking_code}</h2>
                </div>
                <div className={`px-4 py-2 rounded-full font-semibold text-sm ${getStatusBg(parcel.status)}`}>
                  {statusDisplay}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{t('route')}</p>
                  <p className="font-medium text-gray-800">{parcel.origin_branch_name} → {parcel.destination_branch_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">{t('payment_status')}</p>
                  <p className="font-medium text-gray-800 capitalize">
                    {t('payment_' + parcel.payment_status) !== 'payment_' + parcel.payment_status
                      ? t('payment_' + parcel.payment_status) : parcel.payment_status}
                  </p>
                </div>
              </div>
              {(parcel.payment_status === 'pending' || parcel.status === 'delivered') && (
                <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-100 mt-4">
                  {parcel.payment_status === 'pending' && (
                    <button type="button" onClick={handlePay} disabled={payLoading}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-lg text-sm disabled:opacity-50">
                      {payLoading ? '...' : t('pay_now')}
                    </button>
                  )}
                  {parcel.status === 'delivered' && (
                    <button type="button" onClick={handleConfirmReceipt}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg text-sm">
                      {t('confirm_receipt')}
                    </button>
                  )}
                </div>
              )}
              {actionMsg && <p className="text-sm text-emerald-700 mt-3">{actionMsg}</p>}
            </div>

            {(parcel.eta || parcel.flight) && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">{t('eta_title')}</h3>
                {parcel.eta && (
                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <p className="text-gray-500">{t('eta_current')}</p>
                      <p className="font-medium">{parcel.eta.current_eta_at ? formatDate(parcel.eta.current_eta_at) : '—'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">{t('eta_promised')}</p>
                      <p className="font-medium">{parcel.eta.promised_delivery_at ? formatDate(parcel.eta.promised_delivery_at) : '—'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">{t('eta_remaining')}</p>
                      <p className="font-medium">{parcel.eta.remaining_minutes} {t('minutes_short')}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">{parcel.eta.on_time === false ? t('eta_delayed') : t('eta_on_time')}</p>
                      <p className="font-medium">{parcel.eta.delay_minutes} {t('minutes_short')}</p>
                    </div>
                  </div>
                )}
                {parcel.flight && (
                  <div className="pt-4 border-t border-gray-100 text-sm space-y-2">
                    <p className="font-semibold">{parcel.flight.flight_number} · {parcel.flight.origin_iata || '—'} → {parcel.flight.dest_iata || '—'}</p>
                    <p className="text-gray-500 capitalize">{labelFor(t, 'status_', parcel.flight.status)}{parcel.flight.airline_name ? ` · ${parcel.flight.airline_name}` : ''}</p>
                    {mapUrl && (
                      <a href={mapUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-blue-600 font-semibold hover:underline">
                        {t('live_map')} ↗
                      </a>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-6">{t('tracking_history')}</h3>
              <div className="relative border-l-2 border-gray-200 ml-3">
                {timeline.length === 0 ? (
                  <p className="pl-8 text-gray-500 text-sm">{t('no_events_yet')}</p>
                ) : timeline.map((entry) => (
                  <div key={entry.key} className="mb-8 pl-8 relative">
                    <div className={`absolute w-4 h-4 rounded-full -left-[9px] top-1 ring-4 ring-white ${
                      entry.kind === 'checkpoint' ? 'bg-purple-500' : entry.kind === 'scan' ? 'bg-blue-600' : 'bg-gray-400'
                    }`} />
                    <p className="font-semibold text-gray-900 text-sm">{entry.label}</p>
                    {entry.detail && <p className="text-gray-600 text-sm mt-1">{entry.detail}</p>}
                    <p className="text-xs text-gray-400 mt-1">{formatDate(entry.at)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="py-6 text-center text-sm text-gray-500">
        <p>{t('powered_by')}</p>
      </footer>
    </div>
  );
}
