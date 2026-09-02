'use client';
import { useTranslation } from '@/lib/i18n';
import useSWR from 'swr';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';

export default function ManifestDetail() {
  const { t } = useTranslation();
  const { id } = useParams();
  const { data, isLoading } = useSWR(`/manifests/${id}`, url => api.get(url).then(res => res.data));

  if (isLoading) return <RoleGuard>Loading...</RoleGuard>;

  return (
    <RoleGuard>
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-sm space-y-6">
        <h1 className="text-2xl font-bold">Manifest {id?.toString().substring(0,8)}</h1>
        <div className="grid grid-cols-2 gap-4">
          <div><span className="font-semibold">Status:</span> {data?.status}</div>
          <div><span className="font-semibold">Driver:</span> {data?.driver_name} ({data?.vehicle_plate})</div>
        </div>
        <h2 className="text-xl font-bold mt-6">Parcels</h2>
        <ul className="list-disc pl-5">
          {data?.parcels?.map((p: any) => (
            <li key={p.id}>{p.tracking_code} - {p.status}</li>
          ))}
        </ul>
      </div>
    </RoleGuard>
  );
}