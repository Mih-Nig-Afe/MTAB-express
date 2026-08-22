'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';
import { Manifest } from '@/types';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function ManifestsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useSWR(`/manifests?page=${page}&size=20`, fetcher);

  return (
    <RoleGuard>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Manifests</h1>
          <Link href="/manifests/new" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium text-sm">
            + New Manifest
          </Link>
        </div>

        {isLoading ? (
          <div>Loading...</div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Route</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Driver</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data?.items?.map((manifest: Manifest) => (
                  <tr key={manifest.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-blue-600"><Link href={`/manifests/${manifest.id}`}>{manifest.id.substring(0,8)}</Link></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{manifest.origin_branch_id?.substring(0,8)} → {manifest.destination_branch_id?.substring(0,8)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{manifest.driver_name} <br/><span className="text-xs text-gray-500">{manifest.vehicle_plate}</span></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm"><span className="px-2 py-1 bg-gray-100 rounded-full">{manifest.status}</span></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(manifest.created_at)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {manifest.status === 'in_transit' && (
                        <Link href={`/manifests/${manifest.id}/receive`} className="text-blue-600 hover:text-blue-900">Receive</Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}