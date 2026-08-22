'use client';
import useSWR from 'swr';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import ParcelTable from '@/components/parcels/ParcelTable';
import { Parcel } from '@/types';
import { useTranslation } from '@/lib/i18n';
import { useBarcodeScanner } from '@/lib/useBarcodeScanner';
import { useToast } from '@/components/ui/Toast';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function Dashboard() {
  const router = useRouter();
  const toast = useToast();
  const { t } = useTranslation();
  const { data: parcels, error, isLoading } = useSWR<Parcel[]>('/parcels', fetcher);

  // Barcode scanner listener
  useBarcodeScanner((code) => {
    toast.info(`Scanned Barcode: ${code}`, 'Barcode Gun Detected');
    const matched = parcels?.find(p => p.tracking_code.toLowerCase() === code.toLowerCase());
    if (matched) {
      router.push(`/parcels/${matched.id}`);
    } else {
      router.push(`/parcels?search=${encodeURIComponent(code)}`);
    }
  });

  const totalParcels = parcels?.length || 0;
  const inTransit = parcels?.filter(p => p.status === 'in_transit').length || 0;
  const delivered = parcels?.filter(p => p.status === 'delivered').length || 0;
  const pendingPayment = parcels?.filter(p => p.payment_status === 'pending').length || 0;

  return (
    <RoleGuard>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-gray-900">{t('dashboard')}</h1>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">Real-time overview of branch operations & inter-city freight</p>
          </div>
          <div className="flex gap-2">
            <Link
              href="/parcels/new"
              className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold py-2.5 px-4 rounded-2xl text-xs sm:text-sm shadow-md shadow-blue-500/20 transition flex items-center gap-1.5"
            >
              {t('new_parcel')}
            </Link>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Total Parcels</span>
              <span className="text-xl">📦</span>
            </div>
            <div className="text-2xl font-black text-gray-900 mt-2">{isLoading ? '...' : totalParcels}</div>
            <p className="text-xs text-gray-500 mt-1">All time registered shipments</p>
          </div>

          <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-500 uppercase tracking-wider">In Transit</span>
              <span className="text-xl">🚚</span>
            </div>
            <div className="text-2xl font-black text-blue-600 mt-2">{isLoading ? '...' : inTransit}</div>
            <p className="text-xs text-gray-500 mt-1">Currently on highway routes</p>
          </div>

          <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-500 uppercase tracking-wider">Delivered</span>
              <span className="text-xl">✅</span>
            </div>
            <div className="text-2xl font-black text-emerald-600 mt-2">{isLoading ? '...' : delivered}</div>
            <p className="text-xs text-gray-500 mt-1">Successfully handed over</p>
          </div>

          <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-500 uppercase tracking-wider">Pending Payment</span>
              <span className="text-xl">⏳</span>
            </div>
            <div className="text-2xl font-black text-amber-600 mt-2">{isLoading ? '...' : pendingPayment}</div>
            <p className="text-xs text-gray-500 mt-1">Awaiting cash or digital settle</p>
          </div>
        </div>

        {/* Recent Parcels Section */}
        <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-base font-extrabold text-gray-900 flex items-center gap-2">
              <span>📋 Recent Parcels</span>
            </h2>
            <Link href="/parcels" className="text-xs font-bold text-blue-600 hover:text-blue-800 transition">
              View All ➔
            </Link>
          </div>
          {isLoading ? (
            <div className="py-12 text-center text-gray-400 text-sm">Loading shipments...</div>
          ) : error ? (
            <div className="py-12 text-center text-rose-500 text-sm">Failed to load shipments.</div>
          ) : (
            <ParcelTable parcels={(parcels || []).slice(0, 10)} />
          )}
        </div>
      </div>
    </RoleGuard>
  );
}