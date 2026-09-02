'use client';
// Shared language switcher — EN / አማርኛ pill toggle.
import { useTranslation } from '@/lib/i18n';

export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { language, setLanguage } = useTranslation();
  return (
    <div className="flex rounded-full bg-gray-100 overflow-hidden text-xs font-bold">
      <button
        onClick={() => setLanguage('en')}
        className={`px-2.5 py-1 transition ${language === 'en' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
        aria-label="English"
      >
        EN
      </button>
      <button
        onClick={() => setLanguage('am')}
        className={`px-2.5 py-1 transition ${language === 'am' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
        aria-label="አማርኛ"
      >
        {compact ? 'አማ' : 'አማርኛ'}
      </button>
    </div>
  );
}
