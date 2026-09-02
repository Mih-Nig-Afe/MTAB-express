// Runtime language management for the public portal (per-browser preference).
import { useCallback, useEffect } from "react";
import i18next, { LANG_STORAGE_KEY, resolveSupportedLanguage, type SupportedLanguage } from "./i18n";

export function useLanguage() {
  const applyLanguage = useCallback((lang: SupportedLanguage) => {
    void i18next.changeLanguage(lang);
    document.documentElement.lang = lang;
    try { localStorage.setItem(LANG_STORAGE_KEY, lang); } catch {}
  }, []);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(LANG_STORAGE_KEY);
      const saved = resolveSupportedLanguage(raw) === raw ? (raw as SupportedLanguage) : null;
      if (saved && saved !== i18next.language) void i18next.changeLanguage(saved);
    } catch {}
    document.documentElement.lang = i18next.language;
  }, []);

  const changeLanguage = useCallback((lang: SupportedLanguage) => applyLanguage(lang), [applyLanguage]);
  return { language: resolveSupportedLanguage(i18next.language), changeLanguage };
}
