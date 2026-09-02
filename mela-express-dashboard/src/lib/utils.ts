export function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

export function formatDate(dateStr: string) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function formatCurrency(amount: number) {
  return `ETB ${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatStatus(status: string) {
  if (!status) return '';
  return status.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

export function statusColor(status: string) {
  switch (status) {
    case 'created': return 'bg-gray-100 text-gray-800';
    case 'received_at_origin':
    case 'processed_at_origin': return 'bg-blue-100 text-blue-800';
    case 'dispatched_from_origin':
    case 'in_transit': return 'bg-indigo-100 text-indigo-800';
    case 'arrived_origin_airport':
    case 'checked_in_flight':
    case 'departed': return 'bg-sky-100 text-sky-800';
    case 'arrived_destination_airport':
    case 'released_from_airport': return 'bg-cyan-100 text-cyan-800';
    case 'arrived_at_destination':
    case 'distributed_to_branch': return 'bg-purple-100 text-purple-800';
    case 'ready_for_pickup': return 'bg-amber-100 text-amber-800';
    case 'delivered': return 'bg-green-100 text-green-800';
    case 'returned': return 'bg-orange-100 text-orange-800';
    case 'cancelled':
    case 'lost': return 'bg-red-100 text-red-800';
    case 'on_hold': return 'bg-yellow-100 text-yellow-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}