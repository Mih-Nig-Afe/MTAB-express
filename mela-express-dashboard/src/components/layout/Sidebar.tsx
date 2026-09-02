'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { useTranslation } from '@/lib/i18n';
import { useBrand } from '@/components/BrandProvider';
import { displayName } from '@brand';

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const { t } = useTranslation();
  const brand = useBrand();
  const [isOpen, setIsOpen] = useState(false);

  const links = [
    { href: '/dashboard', label: t('dashboard'), icon: '📊' },
    { href: '/scan', label: t('scan_nav'), icon: '📷' },
    { href: '/parcels', label: t('parcels'), icon: '📦' },
    { href: '/manifests', label: t('manifests'), icon: '📋' },
    { href: '/cash', label: t('cash_short'), icon: '💰' },
    { href: '/reports', label: t('reports'), icon: '📈' },
  ];

  const adminLinks = [
    { href: '/admin/operations', label: t('ops_nav'), icon: '⏱' },
    { href: '/admin/branches', label: t('branches'), icon: '🏢' },
    { href: '/admin/staff', label: t('staff'), icon: '👥' },
    { href: '/admin/overrides', label: t('overrides'), icon: '⚙️' },
  ];

  const isAdmin = user?.role === 'admin' || user?.role === 'manager';

  return (
    <>
      <button className="md:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-md shadow" onClick={() => setIsOpen(!isOpen)}>
        ☰
      </button>
      <div className={cn("fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out md:translate-x-0", isOpen ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex items-center justify-center h-16 border-b border-gray-200">
          <span className="text-xl font-bold text-blue-600">{displayName(brand)}</span>
        </div>
        <nav className="p-4 space-y-1 overflow-y-auto h-[calc(100vh-4rem)]">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className={cn("flex items-center px-4 py-2 text-sm font-medium rounded-md", pathname.startsWith(link.href) ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50")}>
              <span className="mr-3">{link.icon}</span> {link.label}
            </Link>
          ))}
          
          {isAdmin && (
            <>
              <div className="pt-4 pb-2">
                <p className="px-4 text-xs font-semibold tracking-wider text-gray-500 uppercase">{t('admin_section')}</p>
              </div>
              {adminLinks.map((link) => (
                <Link key={link.href} href={link.href} className={cn("flex items-center px-4 py-2 text-sm font-medium rounded-md", pathname.startsWith(link.href) ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50")}>
                  <span className="mr-3">{link.icon}</span> {link.label}
                </Link>
              ))}
            </>
          )}
        </nav>
      </div>
    </>
  );
}