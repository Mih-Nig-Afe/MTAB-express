'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, useAuth } from '@/lib/auth';
import { useTranslation } from '@/lib/i18n';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function RoleGuard({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: string[] }) {
  const router = useRouter();
  const { user } = useAuth();
  const { t } = useTranslation();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    if (!isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  if (!isClient) {
    return (
      <div suppressHydrationWarning className="flex h-screen items-center justify-center bg-gray-50">
        <div suppressHydrationWarning className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated()) return null;

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div suppressHydrationWarning className="flex h-screen items-center justify-center bg-gray-50">
        <div suppressHydrationWarning className="text-center">
          <h1 className="text-2xl font-bold text-red-600">{t('access_denied_title')}</h1>
          <p className="mt-2 text-gray-600">{t('access_denied_msg')}</p>
          <button onClick={() => router.push('/dashboard')} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md">{t('go_to_dashboard')}</button>
        </div>
      </div>
    );
  }

  return (
    <div suppressHydrationWarning className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      {/* flex-1 + ml-64 (no w-full): margin is subtracted from the flex item's
          width so content never exceeds the viewport. min-w-0 lets tables and
          grids shrink instead of forcing horizontal overflow. */}
      <div suppressHydrationWarning className="flex flex-col flex-1 min-w-0 md:ml-64">
        <TopBar />
        <main suppressHydrationWarning className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}