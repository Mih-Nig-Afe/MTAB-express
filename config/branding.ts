/**
 * Single source of truth for white-label branding.
 * Values come ONLY from environment variables — never hardcode a brand name in app code.
 * Example values live in the repo root `.env.example` only.
 */
export type BrandConfig = {
  brandName: string;
  brandShort: string;
  trackingPrefix: string;
  trackingExample: string;
  trackingPlaceholder: string;
  smsSenderId: string;
};

function envGet(env: Record<string, string | undefined>, key: string): string {
  return (env[key] ?? "").trim();
}

/** Build brand config from env keys (optionally prefixed, e.g. NEXT_PUBLIC_). */
export function brandFromEnv(
  env: Record<string, string | undefined>,
  prefix = "",
): BrandConfig {
  const brandName = envGet(env, `${prefix}BRAND_NAME`);
  const brandShort = envGet(env, `${prefix}BRAND_SHORT`);
  const trackingPrefix = (
    envGet(env, `${prefix}TRACKING_PREFIX`) || brandShort
  ).toUpperCase();
  const smsSenderId =
    envGet(env, `${prefix}SMS_SENDER_ID`) ||
    envGet(env, "SMS_SENDER_ID") ||
    (brandShort ? `${brandShort}Express` : "");

  return {
    brandName,
    brandShort,
    trackingPrefix,
    trackingExample: trackingPrefix ? `${trackingPrefix}-HW-000482` : "",
    trackingPlaceholder: trackingPrefix ? `${trackingPrefix}-HW-000000` : "",
    smsSenderId,
  };
}

/** Map API /public/brand JSON to BrandConfig. */
export function brandFromApi(data: Record<string, string>): BrandConfig {
  const brandName = (data.brand_name ?? "").trim();
  const brandShort = (data.brand_short ?? "").trim();
  const trackingPrefix = ((data.tracking_prefix ?? brandShort) || "").toUpperCase();
  const smsSenderId = (data.sms_sender_id ?? "").trim();

  return {
    brandName,
    brandShort,
    trackingPrefix,
    trackingExample: (data.tracking_example ?? "").trim() || `${trackingPrefix}-HW-000482`,
    trackingPlaceholder:
      (data.tracking_placeholder ?? "").trim() || `${trackingPrefix}-HW-000000`,
    smsSenderId,
  };
}

export function toI18nVars(brand: BrandConfig): Record<string, string> {
  return {
    brandName: brand.brandName,
    brandShort: brand.brandShort,
    trackingPrefix: brand.trackingPrefix,
    trackingExample: brand.trackingExample,
    trackingPlaceholder: brand.trackingPlaceholder,
  };
}

export function displayName(brand: BrandConfig): string {
  return brand.brandName || brand.brandShort || "";
}
