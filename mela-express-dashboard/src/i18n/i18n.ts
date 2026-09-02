// i18n initialisation — statically imports all locale JSON files.
// No runtime fetches, no lazy loading, no URL-based language routing.
// Language is set at runtime from localStorage via useLanguage.
//
// Flat key lookup (keySeparator/nsSeparator disabled) so existing
// t('some_key') call sites work unchanged while locale data stays
// organised in per-domain JSON files under src/locales/.

import i18next from "i18next";

import enNav from "@/locales/en/nav.json";
import enAuth from "@/locales/en/auth.json";
import enDashboard from "@/locales/en/dashboard.json";
import enParcels from "@/locales/en/parcels.json";
import enManifests from "@/locales/en/manifests.json";
import enAdmin from "@/locales/en/admin.json";
import enFinance from "@/locales/en/finance.json";
import enStatuses from "@/locales/en/statuses.json";
import enErrors from "@/locales/en/errors.json";

import amNav from "@/locales/am/nav.json";
import amAuth from "@/locales/am/auth.json";
import amDashboard from "@/locales/am/dashboard.json";
import amParcels from "@/locales/am/parcels.json";
import amManifests from "@/locales/am/manifests.json";
import amAdmin from "@/locales/am/admin.json";
import amFinance from "@/locales/am/finance.json";
import amStatuses from "@/locales/am/statuses.json";
import amErrors from "@/locales/am/errors.json";

export const LANG_STORAGE_KEY = "mela_lang";
export const supportedLanguages = ["en", "am"] as const;
export type SupportedLanguage = (typeof supportedLanguages)[number];
export const defaultLanguage: SupportedLanguage = "en";

const en = { ...enNav, ...enAuth, ...enDashboard, ...enParcels, ...enManifests, ...enAdmin, ...enFinance, ...enStatuses, ...enErrors };
const am = { ...amNav, ...amAuth, ...amDashboard, ...amParcels, ...amManifests, ...amAdmin, ...amFinance, ...amStatuses, ...amErrors };

void i18next.init({
  lng: defaultLanguage,
  fallbackLng: "en",
  resources: { en: { translation: en }, am: { translation: am } },
  // Flat keys only — dots in keys are literal, matching legacy usage.
  keySeparator: false,
  nsSeparator: false,
  interpolation: { escapeValue: false },
  saveMissing: process.env.NODE_ENV === "development",
  missingKeyHandler: (_lngs, _ns, key) => {
    // eslint-disable-next-line no-console
    console.warn(`[i18n] missing key: "${key}"`);
  },
});

export function resolveSupportedLanguage(lang: string | null | undefined): SupportedLanguage {
  return (supportedLanguages as readonly string[]).includes(lang ?? "") ? (lang as SupportedLanguage) : defaultLanguage;
}

export default i18next;
