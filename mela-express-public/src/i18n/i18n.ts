// i18n initialisation — static locale JSON imports, flat key lookup.
import i18next from "i18next";

import { brandFromEnv, toI18nVars } from "@brand";

import enCommon from "@/locales/en/common.json";
import enTracking from "@/locales/en/tracking.json";
import enStatuses from "@/locales/en/statuses.json";
import enErrors from "@/locales/en/errors.json";

import amCommon from "@/locales/am/common.json";
import amTracking from "@/locales/am/tracking.json";
import amStatuses from "@/locales/am/statuses.json";
import amErrors from "@/locales/am/errors.json";

export const LANG_STORAGE_KEY = "mela_public_lang";
export const supportedLanguages = ["en", "am"] as const;
export type SupportedLanguage = (typeof supportedLanguages)[number];
export const defaultLanguage: SupportedLanguage = "en";

const en = { ...enCommon, ...enTracking, ...enStatuses, ...enErrors };
const am = { ...amCommon, ...amTracking, ...amStatuses, ...amErrors };

void i18next.init({
  lng: defaultLanguage,
  fallbackLng: "en",
  resources: { en: { translation: en }, am: { translation: am } },
  keySeparator: false,
  nsSeparator: false,
  interpolation: { escapeValue: false, defaultVariables: toI18nVars(brandFromEnv(process.env, "NEXT_PUBLIC_")) },
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
