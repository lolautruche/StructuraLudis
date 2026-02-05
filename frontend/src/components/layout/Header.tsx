'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

export function Header() {
  const t = useTranslations('Common');
  const { user, isAuthenticated, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const closeMobileMenu = () => setMobileMenuOpen(false);

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

          {/* Desktop Navigation */}
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
            {isAuthenticated && (
              <Link
                href="/my/events"
                className="transition-colors"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('myEvents')}
              </Link>
            )}
            {(user?.global_role === 'SUPER_ADMIN' || user?.global_role === 'ADMIN') && (
              <Link
                href="/admin"
                className="transition-colors font-medium"
                style={{ color: 'var(--color-primary)' }}
              >
                Admin
              </Link>
            )}
          </nav>

          {/* Desktop Right side */}
          <div className="hidden md:flex items-center space-x-3">
            <ThemeToggle />
            <LanguageSwitcher />

            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <span
                  className="text-sm hidden lg:block"
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

          {/* Mobile hamburger button */}
          <button
            className="md:hidden p-2 rounded-lg transition-colors"
            style={{ color: 'var(--color-text-primary)' }}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div
            className="md:hidden py-4 border-t"
            style={{ borderColor: 'var(--color-border)' }}
          >
            <nav className="flex flex-col space-y-3">
              <Link
                href="/exhibitions"
                className="px-2 py-2 rounded-lg transition-colors"
                style={{ color: 'var(--color-text-primary)' }}
                onClick={closeMobileMenu}
              >
                {t('exhibitions')}
              </Link>
              {isAuthenticated && (
                <>
                  <Link
                    href="/my/agenda"
                    className="px-2 py-2 rounded-lg transition-colors"
                    style={{ color: 'var(--color-text-primary)' }}
                    onClick={closeMobileMenu}
                  >
                    {t('myAgenda')}
                  </Link>
                  <Link
                    href="/my/events"
                    className="px-2 py-2 rounded-lg transition-colors"
                    style={{ color: 'var(--color-text-primary)' }}
                    onClick={closeMobileMenu}
                  >
                    {t('myEvents')}
                  </Link>
                </>
              )}
              {(user?.global_role === 'SUPER_ADMIN' || user?.global_role === 'ADMIN') && (
                <Link
                  href="/admin"
                  className="px-2 py-2 rounded-lg transition-colors font-medium"
                  style={{ color: 'var(--color-primary)' }}
                  onClick={closeMobileMenu}
                >
                  Admin
                </Link>
              )}

              {/* Divider */}
              <div className="border-t my-2" style={{ borderColor: 'var(--color-border)' }} />

              {/* Theme & Language */}
              <div className="flex items-center justify-between px-2 py-2">
                <span style={{ color: 'var(--color-text-secondary)' }}>{t('theme')}</span>
                <ThemeToggle />
              </div>
              <div className="flex items-center justify-between px-2 py-2">
                <span style={{ color: 'var(--color-text-secondary)' }}>{t('language')}</span>
                <LanguageSwitcher />
              </div>

              {/* Divider */}
              <div className="border-t my-2" style={{ borderColor: 'var(--color-border)' }} />

              {/* Auth actions */}
              {isAuthenticated ? (
                <>
                  <Link
                    href="/my/settings"
                    className="px-2 py-2 rounded-lg transition-colors"
                    style={{ color: 'var(--color-text-primary)' }}
                    onClick={closeMobileMenu}
                  >
                    {t('settings')}
                  </Link>
                  <button
                    className="px-2 py-2 rounded-lg transition-colors text-left"
                    style={{ color: 'var(--color-text-danger)' }}
                    onClick={() => { logout(); closeMobileMenu(); }}
                  >
                    {t('logout')}
                  </button>
                </>
              ) : (
                <div className="flex flex-col space-y-2 px-2">
                  <Link href="/auth/login" onClick={closeMobileMenu}>
                    <Button variant="ghost" size="sm" className="w-full">
                      {t('login')}
                    </Button>
                  </Link>
                  <Link href="/auth/register" onClick={closeMobileMenu}>
                    <Button variant="primary" size="sm" className="w-full">
                      {t('register')}
                    </Button>
                  </Link>
                </div>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
