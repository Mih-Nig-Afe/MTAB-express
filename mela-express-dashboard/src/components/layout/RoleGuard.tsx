'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, useAuth } from '@/lib/auth';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function RoleGuard({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: string[] }) {
  const router = useRouter();
  const { user } = useAuth();
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
          <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
          <p className="mt-2 text-gray-600">You don't have permission to view this page.</p>
          <button onClick={() => router.push('/dashboard')} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md">Go to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div suppressHydrationWarning className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div suppressHydrationWarning className="flex flex-col flex-1 md:ml-64 w-full">
        <TopBar />
        <main suppressHydrationWarning className="flex-1 overflow-y-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}