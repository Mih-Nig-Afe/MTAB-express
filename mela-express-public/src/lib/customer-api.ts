const API_ROOT =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/?$/, "") ||
  "http://localhost:8001";

const CUSTOMER_API = `${API_ROOT}/api/customer`;

const TOKEN_KEY = "mela_customer_token";

export function getCustomerToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setCustomerToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearCustomerToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): HeadersInit {
  const token = getCustomerToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function authWithTelegram(initData: string, phone?: string) {
  const res = await fetch(`${CUSTOMER_API}/auth/telegram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData, phone }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Telegram auth failed");
  }
  const data = await res.json();
  setCustomerToken(data.access_token);
  return data;
}

export async function fetchCustomerMe() {
  const res = await fetch(`${CUSTOMER_API}/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function fetchMyParcels() {
  const res = await fetch(`${CUSTOMER_API}/parcels`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load parcels");
  return res.json();
}

export async function fetchParcelTrack(code: string) {
  const res = await fetch(`${CUSTOMER_API}/parcels/${encodeURIComponent(code)}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Parcel not found");
  return res.json();
}

export async function fetchPublicTrack(code: string) {
  const res = await fetch(`${API_ROOT}/api/parcels/track/${encodeURIComponent(code)}`);
  if (!res.ok) throw new Error("Parcel not found");
  return res.json();
}

export async function fetchBranches() {
  const res = await fetch(`${CUSTOMER_API}/branches`);
  if (!res.ok) throw new Error("Failed to load branches");
  return res.json();
}

export async function fetchQuote(body: {
  weight_kg: number;
  length_cm?: number;
  width_cm?: number;
  height_cm?: number;
}) {
  const res = await fetch(`${CUSTOMER_API}/quote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, content_category: "general" }),
  });
  if (!res.ok) throw new Error("Quote failed");
  return res.json();
}

export async function initiatePayment(trackingCode: string) {
  const res = await fetch(`${API_ROOT}/api/payments/chapa/initiate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tracking_code: trackingCode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Payment failed");
  }
  return res.json();
}

export async function fetchPickupCode(trackingCode: string) {
  const res = await fetch(`${CUSTOMER_API}/pickup-code/${encodeURIComponent(trackingCode)}`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Pickup code unavailable");
  }
  return res.json();
}

export async function confirmReceipt(trackingCode: string) {
  const res = await fetch(
    `${CUSTOMER_API}/parcels/${encodeURIComponent(trackingCode)}/confirm-receipt`,
    { method: "POST", headers: authHeaders() }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Could not confirm receipt");
  }
  return res.json();
}
