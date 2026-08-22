'use client';
import { useAuth, logout } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export default function TopBar() {
  const { user, setUser } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    setUser(null);
    router.push('/login');
  };

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
      <div className="flex items-center ml-12 md:ml-0">
        <h2 className="text-xl font-semibold text-gray-800">Branch: {user?.branch_id || 'All'}</h2>
      </div>
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">{user?.name}</p>
          <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
        </div>
        <button onClick={handleLogout} className="px-3 py-1 text-sm font-medium text-red-600 border border-red-200 rounded-md hover:bg-red-50">
          Logout
        </button>
      </div>
    </header>
  );
}