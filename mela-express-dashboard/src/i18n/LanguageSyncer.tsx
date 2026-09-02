'use client';
// Side-effect-only: keeps <html lang> and document.title in sync with UI language.
import { useEffect } from 'react';
import { useLanguage } from './useLanguage';
import i18next from './i18n';

export default function LanguageSyncer({ titleKey = 'meta_dashboard_title' }: { titleKey?: string }) {
  useLanguage();
  useEffect(() => {
    const apply = () => {
      const title = i18next.t(titleKey) as string;
      if (title && title !== titleKey) document.title = title;
    };
    apply();
    i18next.on('languageChanged', apply);
    return () => { i18next.off('languageChanged', apply); };
  }, [titleKey]);
  return null;
}
