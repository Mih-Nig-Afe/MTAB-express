'use client';
import RoleGuard from '@/components/layout/RoleGuard';
import ParcelForm from '@/components/parcels/ParcelForm';

export default function NewParcelPage() {
  return (
    <RoleGuard>
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Create New Parcel</h1>
        <ParcelForm />
      </div>
    </RoleGuard>
  );
}