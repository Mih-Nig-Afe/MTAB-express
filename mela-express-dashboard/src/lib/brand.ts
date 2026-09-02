/**
 * Branding for the dashboard — env at build time, API at runtime (see BrandProvider).
 * Do not hardcode brand names here; set BRAND_* / NEXT_PUBLIC_BRAND_* in .env.
 */
import {
  brandFromApi,
  brandFromEnv,
  displayName,
  toI18nVars,
  apiOrigin,
  type BrandConfig,
} from "@brand";

import i18next from "@/i18n/i18n";

const EMPTY: BrandConfig = brandFromEnv({});

/** Brand from NEXT_PUBLIC_* (build-time / Vercel env). */
export const envBrand: BrandConfig = brandFromEnv(process.env, "NEXT_PUBLIC_");

let runtimeBrand: BrandConfig | null = null;

export function getBrand(): BrandConfig {
  return runtimeBrand ?? (displayName(envBrand) ? envBrand : EMPTY);
}

export function applyBrandToI18n(brand: BrandConfig): void {
  const vars = toI18nVars(brand);
  const interpolation = i18next.options.interpolation;
  if (interpolation) {
    interpolation.defaultVariables = { ...interpolation.defaultVariables, ...vars };
  }
}

export async function loadBrandFromApi(apiUrl: string): Promise<BrandConfig> {
  const base = apiOrigin(apiUrl);
  const res = await fetch(`${base}/public/brand`, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`Brand config fetch failed: ${res.status}`);
  const brand = brandFromApi(await res.json());
  runtimeBrand = brand;
  applyBrandToI18n(brand);
  return brand;
}

/** @deprecated Prefer useBrand() — kept for static metadata fallbacks */
export const BRAND_NAME = displayName(envBrand);

export const brandInterpolation = toI18nVars(getBrand());

export type { BrandConfig };
