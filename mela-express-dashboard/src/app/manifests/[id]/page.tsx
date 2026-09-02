'use client';
import { useTranslation, labelFor } from '@/lib/i18n';
import useSWR from 'swr';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';

export default function ManifestDetail() {
  const { t } = useTranslation();
  const { id } = useParams();
  const { data, isLoading } = useSWR(`/manifests/${id}`, url => api.get(url).then(res => res.data));

  if (isLoading) return <RoleGuard>{t('loading')}</RoleGuard>;

  return (
    <RoleGuard>
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-sm space-y-6">
        <h1 className="text-2xl font-bold">{t('manifest_heading', { id: id?.toString().substring(0, 8) || '' })}</h1>
        <div className="grid grid-cols-2 gap-4">
          <div><span className="font-semibold">{t('status')}:</span> {labelFor(t, 'manifest_status_', data?.status)}</div>
          <div><span className="font-semibold">{t('driver')}:</span> {data?.driver_name} ({data?.vehicle_plate})</div>
        </div>
        <h2 className="text-xl font-bold mt-6">{t('parcels')}</h2>
        <ul className="list-disc pl-5">
          {data?.parcels?.map((p: any) => (
            <li key={p.id}>{p.tracking_code} - {labelFor(t, 'status_', p.status)}</li>
          ))}
        </ul>
      </div>
    </RoleGuard>
  );
}
