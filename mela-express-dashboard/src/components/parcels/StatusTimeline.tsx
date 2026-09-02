'use client';
import { ParcelStatusHistory, ParcelStatus } from '@/types';
import { formatDate, formatStatus, statusColor } from '@/lib/utils';
import { useTranslation } from '@/lib/i18n';

export default function StatusTimeline({ history }: { history: ParcelStatusHistory[] }) {
  const { t } = useTranslation();
  if (!history || history.length === 0) return <div className="text-sm text-gray-500">{t('no_status_history')}</div>;

  const statusLabel = (status: ParcelStatus) => {
    const key = `status_${status}`;
    const label = t(key);
    return label === key ? formatStatus(status) : label;
  };

  return (
    <div className="flow-root">
      <ul role="list" className="-mb-8">
        {history.map((event, eventIdx) => {
          const currentStatus = (event.to_status || event.status || 'created') as ParcelStatus;
          const time = event.timestamp || event.created_at || '';
          return (
            <li key={event.id || eventIdx}>
              <div className="relative pb-8">
                {eventIdx !== history.length - 1 ? (
                  <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                ) : null}
                <div className="relative flex space-x-3">
                  <div>
                    <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${statusColor(currentStatus).split(' ')[0]}`}>
                      <span className="w-2.5 h-2.5 rounded-full bg-current" />
                    </span>
                  </div>
                  <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                    <div>
                      <p className="text-sm text-gray-900 font-medium">{statusLabel(currentStatus)}</p>
                      {event.note && <p className="mt-1 text-sm text-gray-500">{event.note}</p>}
                    </div>
                    <div className="text-right text-sm whitespace-nowrap text-gray-500">
                      {time && <time dateTime={time}>{formatDate(time)}</time>}
                      {event.operator_name && <p className="mt-1 text-xs">{event.operator_name}</p>}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
