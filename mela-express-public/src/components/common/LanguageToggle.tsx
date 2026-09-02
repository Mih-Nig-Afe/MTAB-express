'use client';
// Shared language switcher for the public portal — EN / አማርኛ pill toggle.
import { useTranslation } from '@/lib/i18n';

export default function LanguageToggle() {
  const { language, setLanguage } = useTranslation();
  return (
    <div className="fixed top-3 right-3 z-50 flex rounded-full bg-white shadow-md border border-slate-200 overflow-hidden text-xs font-bold">
      <button
        onClick={() => setLanguage('en')}
        className={`px-3 py-1.5 transition ${language === 'en' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:text-slate-900'}`}
        aria-label="English"
      >
        EN
      </button>
      <button
        onClick={() => setLanguage('am')}
        className={`px-3 py-1.5 transition ${language === 'am' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:text-slate-900'}`}
        aria-label="አማርኛ"
      >
        አማ
      </button>
    </div>
  );
}
