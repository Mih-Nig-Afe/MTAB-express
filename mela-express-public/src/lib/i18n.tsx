'use client';
// Compatibility shim — real i18n lives in src/i18n/ (reference layout).
import React, { createContext, useContext, useEffect, useState } from 'react';
import i18next, { LANG_STORAGE_KEY, resolveSupportedLanguage } from '@/i18n/i18n';
import type { SupportedLanguage } from '@/i18n/i18n';

export type Language = SupportedLanguage;

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  language: 'en',
  setLanguage: () => {},
  t: (key: string) => key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    let saved: Language | null = null;
    try {
      const raw = localStorage.getItem(LANG_STORAGE_KEY);
      saved = resolveSupportedLanguage(raw) === raw ? (raw as Language) : null;
    } catch {}
    if (saved && saved !== i18next.language) void i18next.changeLanguage(saved);
    const apply = () => setLanguageState(resolveSupportedLanguage(i18next.language));
    apply();
    i18next.on('languageChanged', apply);
    return () => i18next.off('languageChanged', apply);
  }, []);

  const setLanguage = (lang: Language) => {
    void i18next.changeLanguage(lang);
    try {
      localStorage.setItem(LANG_STORAGE_KEY, lang);
      document.documentElement.lang = lang;
    } catch {}
  };

  const t = (key: string): string => i18next.t(key);

  return <I18nContext.Provider value={{ language, setLanguage, t }}>{children}</I18nContext.Provider>;
}

export const useTranslation = () => useContext(I18nContext);

export { default as LanguageToggle } from '@/components/common/LanguageToggle';
