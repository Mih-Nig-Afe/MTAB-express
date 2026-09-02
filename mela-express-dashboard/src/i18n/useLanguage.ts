// useLanguage — runtime language management for the staff dashboard.
//
// Staff pick their own UI language; it is stored per-browser
// (localStorage `mela_lang`) and applied to <html lang> for a11y/fonts.

import { useCallback, useEffect } from "react";
import i18next, {
  LANG_STORAGE_KEY,
  resolveSupportedLanguage,
  type SupportedLanguage,
} from "./i18n";

function readFromStorage(): SupportedLanguage | null {
  try {
    const raw = localStorage.getItem(LANG_STORAGE_KEY);
    return resolveSupportedLanguage(raw) === raw ? (raw as SupportedLanguage) : null;
  } catch {
    return null;
  }
}

function applyDocumentLang(lang: string) {
  document.documentElement.lang = lang;
}

export function useLanguage() {
  const applyLanguage = useCallback((lang: SupportedLanguage) => {
    void i18next.changeLanguage(lang);
    applyDocumentLang(lang);
    try {
      localStorage.setItem(LANG_STORAGE_KEY, lang);
    } catch {
      /* storage unavailable — language still applies for this session */
    }
  }, []);

  // Restore persisted choice on first mount (i18next already booted at default).
  useEffect(() => {
    const saved = readFromStorage();
    if (saved && saved !== i18next.language) applyLanguage(saved);
    applyDocumentLang(i18next.language);
  }, [applyLanguage]);

  const changeLanguage = useCallback(
    (lang: SupportedLanguage) => applyLanguage(lang),
    [applyLanguage],
  );

  return { language: resolveSupportedLanguage(i18next.language), changeLanguage };
}
