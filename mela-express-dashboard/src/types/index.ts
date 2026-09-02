export type StaffRole = 'operator' | 'manager' | 'driver' | 'admin';
export type ParcelStatus =
  | 'created'
  | 'received_at_origin'
  | 'processed_at_origin'
  | 'dispatched_from_origin'
  | 'in_transit'
  | 'arrived_origin_airport'
  | 'checked_in_flight'
  | 'departed'
  | 'arrived_destination_airport'
  | 'released_from_airport'
  | 'arrived_at_destination'
  | 'distributed_to_branch'
  | 'ready_for_pickup'
  | 'delivered'
  | 'returned'
  | 'cancelled'
  | 'lost'
  | 'on_hold';
export type PaymentMode = 'before' | 'after';
export type PaymentMethod = 'cash' | 'chapa';
export type PaymentStatus = 'pending' | 'paid' | 'failed';
export type SizeCategory = 'small' | 'medium' | 'large' | 'oversized';
export type ContentCategory = 'documents' | 'electronics' | 'clothing' | 'food' | 'fragile' | 'general';
export type FacilityType = 'branch' | 'airport' | 'sorting_hub';

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
  facility_type?: FacilityType;
  airport_iata?: string;
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
  origin_branch_code?: string;
  destination_branch_code?: string;
  sender_phone: string;
  receiver_name: string;
  receiver_phone: string;
  description?: string;
  weight_kg?: number;
  length_cm?: number;
  width_cm?: number;
  height_cm?: number;
  size_category?: SizeCategory;
  content_category?: ContentCategory;
  volumetric_weight_kg?: number;
  chargeable_weight_kg?: number;
  declared_value?: number;
  price: number;
  payment_mode: PaymentMode;
  payment_method?: PaymentMethod;
  payment_status: PaymentStatus;
  status: ParcelStatus;
  waybill_url?: string;
  track_url?: string;
  origin_airport_iata?: string;
  dest_airport_iata?: string;
  promised_delivery_at?: string;
  current_eta_at?: string;
  created_at: string;
  updated_at?: string;
  status_history?: ParcelStatusHistory[];
  journey_events?: JourneyEvent[];
  flight?: FlightLeg | null;
  eta?: ParcelEta | null;
  allowed_next?: ParcelStatus[];
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

export interface JourneyEvent {
  id: string;
  event_type: string;
  to_status?: ParcelStatus;
  location_name?: string;
  facility_type?: string;
  latitude?: number;
  longitude?: number;
  flight_number?: string;
  note?: string;
  source: string;
  created_at: string;
}

export interface FlightLeg {
  id: string;
  flight_number: string;
  airline_iata?: string;
  airline_name?: string;
  origin_iata?: string;
  dest_iata?: string;
  airway_bill?: string;
  status: string;
  scheduled_departure?: string;
  scheduled_arrival?: string;
  actual_departure?: string;
  actual_arrival?: string;
  delay_minutes: number;
  latitude?: number;
  longitude?: number;
  altitude_m?: number;
  heading?: number;
  velocity_ms?: number;
  on_ground?: boolean;
  last_position_at?: string;
  provider?: string;
}

export interface ParcelEta {
  promised_delivery_at?: string;
  current_eta_at?: string;
  remaining_minutes: number;
  delay_minutes: number;
  on_time?: boolean | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DashboardKPIs {
  start_date?: string;
  end_date?: string;
  total_parcels: number;
  status_counts: Record<string, number>;
  parcels_created_today: number;
  parcels_delivered_today: number;
  parcels_in_transit: number;
  pending_payments_count: number;
  pending_payments_total: number;
  ready_for_pickup?: number;
  delayed_vs_promised?: number;
}

export interface OperationsKPIs {
  volume: {
    total: number;
    linehaul: number;
    ready_for_pickup: number;
    delivered: number;
    exceptions: number;
  };
  on_time_delivery_pct: number | null;
  exception_rate_pct: number;
  funnel: Record<string, number>;
  dwell_hours: Record<string, number>;
  pickup_aging: {
    ready_now: number;
    over_24h: number;
    over_72h: number;
    over_7d: number;
    avg_hours_waiting: number;
    reminders_sent: number;
  };
  eta: { late_vs_promised: number; tracked_with_eta: number };
  flights: { active: number; delayed: number };
  generated_at: string;
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

export interface ClassificationPreview {
  size_category: SizeCategory;
  volumetric_weight_kg: number;
  chargeable_weight_kg: number;
  suggested_price: number;
}

export interface ParcelScanResult {
  ok: boolean;
  tracking_code: string;
  from_status: ParcelStatus;
  to_status: ParcelStatus;
  status_label: string;
  station: string;
  message: string;
  track_url: string;
}