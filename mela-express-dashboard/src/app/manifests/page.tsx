'use client';
import { useTranslation, labelFor } from '@/lib/i18n';
import { useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';
import { Manifest } from '@/types';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function ManifestsPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useSWR(`/manifests?page=${page}&size=20`, fetcher);

  return (
    <RoleGuard>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">{t('manifests')}</h1>
          <Link href="/manifests/new" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium text-sm">
            + {t('new_manifest')}
          </Link>
        </div>

        {isLoading ? (
          <div>{t('loading')}</div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('manifest_no')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('route')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('driver_name')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('status')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('date')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data?.items?.map((manifest: Manifest) => (
                  <tr key={manifest.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-blue-600"><Link href={`/manifests/${manifest.id}`}>{manifest.id.substring(0,8)}</Link></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{manifest.origin_branch_id?.substring(0,8)} → {manifest.destination_branch_id?.substring(0,8)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{manifest.driver_name} <br/><span className="text-xs text-gray-500">{manifest.vehicle_plate}</span></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm"><span className="px-2 py-1 bg-gray-100 rounded-full">{labelFor(t, 'manifest_status_', manifest.status)}</span></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(manifest.created_at)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {manifest.status === 'in_transit' && (
                        <Link href={`/manifests/${manifest.id}/receive`} className="text-blue-600 hover:text-blue-900">{t('receive')}</Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <span className="text-sm text-gray-700">{t('page_word')} {page} {t('of_word')} {data.pages}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 text-sm">{t('previous')}</button>
              <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page === data.pages} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 text-sm">{t('next')}</button>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}