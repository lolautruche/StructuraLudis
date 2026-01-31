'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

export function Header() {
  const t = useTranslations('Common');
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header
      className="sticky top-0 z-50 backdrop-blur border-b transition-colors"
      style={{
        backgroundColor: 'var(--color-bg-header)',
        borderColor: 'var(--color-border)'
      }}
    >
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
              href="/exhibitions"
              className="transition-colors"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              {t('exhibitions')}
            </Link>
            {isAuthenticated && (
              <Link
                href="/my/agenda"
                className="transition-colors"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('myAgenda')}
              </Link>
            )}
          </nav>

          {/* Right side */}
          <div className="flex items-center space-x-3">
            <ThemeToggle />
            <LanguageSwitcher />

            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <span
                  className="text-sm hidden sm:block"
                  style={{ color: 'var(--color-text-muted)' }}
                >
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
