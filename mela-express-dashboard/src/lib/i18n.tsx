'use client';
// Compatibility shim — the real i18n lives in src/i18n/ (reference layout).
// Keeps the legacy context API ({ language, setLanguage, t }) so existing
// imports across the app continue to work unchanged.
import React, { createContext, useContext, useEffect, useState } from 'react';
import i18next, { LANG_STORAGE_KEY, resolveSupportedLanguage } from '@/i18n/i18n';
import type { SupportedLanguage } from '@/i18n/i18n';

export type Language = SupportedLanguage;

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextType>({
  language: 'en',
  setLanguage: () => {},
  t: (key: string) => key,
});

function readStored(): Language | null {
  try {
    const raw = localStorage.getItem(LANG_STORAGE_KEY);
    return resolveSupportedLanguage(raw) === raw ? (raw as Language) : null;
  } catch {
    return null;
  }
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    const saved = readStored();
    if (saved && saved !== i18next.language) void i18next.changeLanguage(saved);
    // Track whatever i18next resolves to (covers external changeLanguage too).
    const apply = () => setLanguageState(resolveSupportedLanguage(i18next.language));
    apply();
    i18next.on('languageChanged', apply);
    return () => i18next.off('languageChanged', apply);
  }, []);

  const setLanguage = (lang: Language) => {
    void i18next.changeLanguage(lang); // fires languageChanged → state sync above
    try {
      localStorage.setItem(LANG_STORAGE_KEY, lang);
      document.documentElement.lang = lang;
    } catch {
      /* storage unavailable */
    }
  };

  const t = (key: string, vars?: Record<string, string | number>): string =>
    (vars ? i18next.t(key, vars) : i18next.t(key)) as string;

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useTranslation = () => useContext(I18nContext);

/** Translate `prefix + value` (e.g. status_in_transit); fall back to a readable raw value. */
export function labelFor(
  t: (key: string, vars?: Record<string, string | number>) => string,
  prefix: string,
  value?: string | null,
): string {
  if (!value) return '';
  const key = `${prefix}${value}`;
  const translated = t(key);
  return translated === key ? value.replace(/_/g, ' ') : translated;
}

// Named aliases for consumers migrating toward the reference layout.
export { default as LanguageSwitcher } from "@/components/common/LanguageSwitcher";
