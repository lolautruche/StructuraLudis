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
                <Link href="/my/settings">
                  <Button variant="ghost" size="sm" aria-label={t('settings')}>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </Button>
                </Link>
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
