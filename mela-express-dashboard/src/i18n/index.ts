// i18n module public surface.
import i18next from "./i18n";

export { default as i18n, LANG_STORAGE_KEY, supportedLanguages, defaultLanguage, resolveSupportedLanguage } from "./i18n";
export type { SupportedLanguage } from "./i18n";
export { useLanguage } from "./useLanguage";

/** Localize a backend error detail string (mirrors backend terr()). */
export function translateError(detail: string | undefined | null): string {
  if (!detail) return i18next.t("error_generic");
  const key = `error_backend.${detail}`;
  const localized = i18next.t(key);
  return localized === key ? detail : localized;
}

export default i18next;
