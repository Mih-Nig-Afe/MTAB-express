'use client';
import { Parcel } from '@/types';
import StatusBadge from './StatusBadge';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useTranslation } from '@/lib/i18n';
import Link from 'next/link';

export default function ParcelTable({ parcels }: { parcels: Parcel[] }) {
  const { t } = useTranslation();
  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow-sm border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('tracking')}</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('sender_receiver')}</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('route')}</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('status')}</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('payment')}</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('date')}</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {parcels.map((parcel) => (
            <tr key={parcel.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <Link href={`/parcels/${parcel.id}`} className="text-blue-600 hover:text-blue-900 font-medium font-mono text-sm">
                  {parcel.tracking_code}
                </Link>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <div><span className="text-gray-500">{t('s_prefix')}</span> {parcel.sender_phone}</div>
                <div><span className="text-gray-500">{t('r_prefix')}</span> {parcel.receiver_name} ({parcel.receiver_phone})</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {parcel.origin_branch_code || parcel.origin_branch_id?.substring(0, 8)} → {parcel.destination_branch_code || parcel.destination_branch_id?.substring(0, 8)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <StatusBadge status={parcel.status} />
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <div className="font-medium">{formatCurrency(parcel.price)}</div>
                <div className={`text-xs ${parcel.payment_status === 'paid' ? 'text-green-600' : 'text-amber-600'}`}>
                  {t(`payment_${parcel.payment_status}`)} ({parcel.payment_mode === 'before' ? t('mode_before') : t('mode_after')})
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(parcel.created_at)}
              </td>
            </tr>
          ))}
          {parcels.length === 0 && (
            <tr>
              <td colSpan={6} className="px-6 py-8 text-center text-gray-500">{t('no_parcels_found')}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
