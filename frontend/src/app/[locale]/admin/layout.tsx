'use client';

import { useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from '@/i18n/routing';
import { Link, usePathname } from '@/i18n/routing';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const t = useTranslations('SuperAdmin');
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // SUPER_ADMIN and ADMIN can access admin portal
  const isAdmin = user?.global_role === 'SUPER_ADMIN' || user?.global_role === 'ADMIN';

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Redirect if not SUPER_ADMIN or ADMIN
  useEffect(() => {
    if (!authLoading && isAuthenticated && !isAdmin) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, isAdmin, router]);

  // Loading state
  if (authLoading || !isAuthenticated || !isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse">
          <div className="h-8 w-48 rounded" style={{ backgroundColor: 'var(--color-bg-secondary)' }} />
        </div>
      </div>
    );
  }

  const navItems = [
    { href: '/admin', label: t('dashboard'), exact: true },
    { href: '/admin/users', label: t('users') },
    { href: '/admin/exhibitions', label: t('exhibitions') },
    { href: '/admin/event-requests', label: t('eventRequests') },
  ];

  const isActive = (href: string, exact?: boolean) => {
    if (exact) {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1
        className="text-2xl font-bold mb-6"
        style={{ color: 'var(--color-text-primary)' }}
      >
        {t('title')}
      </h1>

      {/* Navigation tabs */}
      <div
        className="flex border-b mb-6"
        style={{ borderColor: 'var(--color-border)' }}
      >
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              isActive(item.href, item.exact)
                ? 'border-ludis-primary'
                : 'border-transparent hover:border-slate-300 dark:hover:border-slate-600'
            }`}
            style={{
              color: isActive(item.href, item.exact)
                ? 'var(--color-primary)'
                : 'var(--color-text-secondary)',
            }}
          >
            {item.label}
          </Link>
        ))}
      </div>

      {children}
    </div>
  );
}
