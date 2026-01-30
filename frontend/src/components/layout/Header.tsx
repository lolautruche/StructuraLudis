'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui';
import { LanguageSwitcher } from './LanguageSwitcher';

export function Header() {
  const t = useTranslations('Common');
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-ludis-dark/95 backdrop-blur border-b border-slate-800">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold text-ludis-primary">
              Structura Ludis
            </span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link
              href="/sessions"
              className="text-slate-300 hover:text-white transition-colors"
            >
              {t('sessions')}
            </Link>
            {isAuthenticated && (
              <Link
                href="/my/dashboard"
                className="text-slate-300 hover:text-white transition-colors"
              >
                {t('dashboard')}
              </Link>
            )}
          </nav>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            <LanguageSwitcher />

            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-slate-400 hidden sm:block">
                  {user?.full_name || user?.email}
                </span>
                <Button variant="ghost" size="sm" onClick={logout}>
                  {t('logout')}
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link href="/auth/login">
                  <Button variant="ghost" size="sm">
                    {t('login')}
                  </Button>
                </Link>
                <Link href="/auth/register">
                  <Button variant="primary" size="sm">
                    {t('register')}
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
