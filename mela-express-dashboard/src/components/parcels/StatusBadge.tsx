'use client';
import { useTranslation } from '@/lib/i18n';
import { formatStatus, statusColor } from '@/lib/utils';

export default function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  const key = `status_${status}`;
  const label = t(key) === key ? formatStatus(status) : t(key);
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor(status)}`}>
      {label}
    </span>
  );
}
