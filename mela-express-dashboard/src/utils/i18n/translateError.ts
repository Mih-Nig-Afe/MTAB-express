/**
 * translateError — single source of truth for turning backend error payloads
 * into user-facing localized strings (mirrors backend terr()).
 *
 * The backend already localizes `detail` server-side based on ?lang= /
 * Accept-Language. This util is the client-side fallback: known English
 * details are translated via errors.json `error_backend.*` keys; unknown
 * strings pass through untouched; network failures map to a generic message.
 */

type HttpErrorLike = {
  response?: { status?: number; data?: { detail?: unknown } };
  message?: string;
};

const KNOWN_DETAILS = new Set([
  'Parcel not found',
  'Branch not found',
  'Staff not found',
  'Manifest not found',
  'Customer not found',
  'Invalid credentials',
  'Not enough permissions',
  'Payment for this parcel was already collected.',
]);

export function translateError(err: HttpErrorLike | string | undefined | null, t: (k: string) => string): string {
  if (!err) return t('error_generic');

  if (typeof err === 'string') {
    return KNOWN_DETAILS.has(err) ? t(`error_backend.${err}`) : err;
  }

  const detail = err.response?.data?.detail;
  const status = err.response?.status;

  if (status && status >= 500) return t('error_generic');
  if (typeof detail === 'string' && detail) {
    return KNOWN_DETAILS.has(detail) ? t(`error_backend.${detail}`) : detail;
  }
  if (!err.response) return t('error_generic');
  return t('error_generic');
}
