'use client';
import { useState, useEffect } from 'react';
import { AuthContext, getUser } from '@/lib/auth';
import { User } from '@/types';
import { ToastProvider } from '@/components/ui/Toast';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      <ToastProvider>
        {children}
      </ToastProvider>
    </AuthContext.Provider>
  );
}