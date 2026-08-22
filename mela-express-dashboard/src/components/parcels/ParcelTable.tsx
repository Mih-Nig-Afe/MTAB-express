'use client';
import { Parcel } from '@/types';
import StatusBadge from './StatusBadge';
import { formatCurrency, formatDate } from '@/lib/utils';
import Link from 'next/link';

export default function ParcelTable({ parcels }: { parcels: Parcel[] }) {
  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow-sm border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tracking</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sender / Receiver</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
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
                <div><span className="text-gray-500">S:</span> {parcel.sender_phone}</div>
                <div><span className="text-gray-500">R:</span> {parcel.receiver_name} ({parcel.receiver_phone})</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {parcel.origin_branch_id?.substring(0,8)} → {parcel.destination_branch_id?.substring(0,8)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <StatusBadge status={parcel.status} />
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <div className="font-medium">{formatCurrency(parcel.price)}</div>
                <div className={`text-xs ${parcel.payment_status === 'paid' ? 'text-green-600' : 'text-amber-600'}`}>
                  {parcel.payment_status.toUpperCase()} ({parcel.payment_mode})
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(parcel.created_at)}
              </td>
            </tr>
          ))}
          {parcels.length === 0 && (
            <tr>
              <td colSpan={6} className="px-6 py-8 text-center text-gray-500">No parcels found</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}