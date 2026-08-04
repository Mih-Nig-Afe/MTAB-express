export type StaffRole = 'operator' | 'manager' | 'driver' | 'admin';
export type ParcelStatus = 'created' | 'received_at_origin' | 'in_transit' | 'arrived_at_destination' | 'ready_for_pickup' | 'delivered' | 'returned' | 'cancelled' | 'lost' | 'on_hold';
export type PaymentMode = 'before' | 'after';
export type PaymentMethod = 'cash' | 'chapa';
export type PaymentStatus = 'pending' | 'paid' | 'failed';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  name: string;
  phone: string;
  email?: string;
  role: StaffRole;
  branch_id?: string;
  is_active: boolean;
}

export interface Branch {
  id: string;
  name: string;
  code: string;
  city: string;
  address?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
}

export interface Staff {
  id: string;
  name: string;
  phone: string;
  email?: string;
  role: StaffRole;
  branch_id?: string;
  is_active: boolean;
}

export interface Parcel {
  id: string;
  tracking_code: string;
  origin_branch_id: string;
  destination_branch_id: string;
  sender_phone: string;
  receiver_name: string;
  receiver_phone: string;
  description?: string;
  weight_kg?: number;
  declared_value?: number;
  price: number;
  payment_mode: PaymentMode;
  payment_method?: PaymentMethod;
  payment_status: PaymentStatus;
  status: ParcelStatus;
  waybill_url?: string;
  created_at: string;
  updated_at?: string;
  status_history?: ParcelStatusHistory[];
}

export interface ParcelStatusHistory {
  id: string;
  parcel_id?: string;
  to_status?: ParcelStatus;
  status?: ParcelStatus;
  from_status?: ParcelStatus;
  note?: string;
  timestamp?: string;
  created_at?: string;
  operator_name?: string;
  changed_by?: string;
  branch_id?: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DashboardKPIs {
  parcels_created_today: number;
  parcels_delivered_today: number;
  parcels_in_transit: number;
  pending_payments_count: number;
  pending_payments_total: number;
}

export interface Manifest {
  id: string;
  origin_branch_id: string;
  destination_branch_id: string;
  driver_name?: string;
  vehicle_plate?: string;
  notes?: string;
  status: 'draft' | 'in_transit' | 'received' | 'cancelled';
  created_at: string;
  parcel_count?: number;
  parcels?: Parcel[];
  parcel_ids?: string[];
}