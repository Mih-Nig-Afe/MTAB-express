'use client';
import RoleGuard from '@/components/layout/RoleGuard';
import ParcelForm from '@/components/parcels/ParcelForm';
import { useTranslation } from '@/lib/i18n';

export default function NewParcelPage() {
  const { t } = useTranslation();
  return (
    <RoleGuard allowedRoles={['admin', 'manager', 'operator']}>
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('create_new_parcel')}</h1>
        <ParcelForm />
      </div>
    </RoleGuard>
  );
}
