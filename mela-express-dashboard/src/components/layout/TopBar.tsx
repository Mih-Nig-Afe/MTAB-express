'use client';
import { useAuth, logout } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useTranslation } from '@/lib/i18n';

export default function TopBar() {
  const { user, setUser } = useAuth();
  const router = useRouter();
  const { language, setLanguage, t } = useTranslation();

  const handleLogout = () => {
    logout();
    setUser(null);
    router.push('/login');
  };

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
      <div className="flex items-center gap-4 ml-12 md:ml-0">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <span className="text-xl">🏢</span>
          <span>{user?.branch_id ? `Branch Hub` : 'Headquarters (Admin)'}</span>
        </h2>
      </div>

      <div className="flex items-center space-x-4">
        {/* Language Switcher */}
        <div className="flex items-center bg-gray-100 p-1 rounded-xl text-xs font-bold">
          <button
            onClick={() => setLanguage('en')}
            className={`px-2.5 py-1 rounded-lg transition ${language === 'en' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-800'}`}
          >
            EN
          </button>
          <button
            onClick={() => setLanguage('am')}
            className={`px-2.5 py-1 rounded-lg transition ${language === 'am' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-800'}`}
          >
            አማርኛ
          </button>
        </div>

        <div className="text-right hidden sm:block">
          <p className="text-sm font-bold text-gray-900">{user?.name || 'Staff'}</p>
          <p className="text-xs text-blue-600 font-semibold uppercase">{user?.role}</p>
        </div>

        <button 
          onClick={handleLogout} 
          className="px-3.5 py-1.5 text-xs font-bold text-rose-600 border border-rose-200 rounded-xl hover:bg-rose-50 transition"
        >
          {t('logout')}
        </button>
      </div>
    </header>
  );
}