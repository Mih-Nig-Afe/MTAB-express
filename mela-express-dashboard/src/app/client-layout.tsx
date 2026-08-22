'use client';
import { useState, useEffect } from 'react';
import { AuthContext, getUser } from '@/lib/auth';
import { User } from '@/types';
import { ToastProvider } from '@/components/ui/Toast';
import { I18nProvider } from '@/lib/i18n';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      <I18nProvider>
        <ToastProvider>
          {children}
        </ToastProvider>
      </I18nProvider>
    </AuthContext.Provider>
  );
}