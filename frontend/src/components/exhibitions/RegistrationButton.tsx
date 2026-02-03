'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Button, ConfirmDialog } from '@/components/ui';
import { Link } from '@/i18n/routing';
import { exhibitionsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import type { Exhibition } from '@/lib/api/types';

interface RegistrationButtonProps {
  exhibition: Exhibition;
  onRegistrationChange?: () => void;
}

export function RegistrationButton({
  exhibition,
  onRegistrationChange,
}: RegistrationButtonProps) {
  const t = useTranslations('Exhibition');
  const { isAuthenticated, user } = useAuth();
  const { showSuccess } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [showUnregisterDialog, setShowUnregisterDialog] = useState(false);
  const [showForceUnregisterDialog, setShowForceUnregisterDialog] = useState(false);
  const [activeBookingCount, setActiveBookingCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Don't show the button if registration is not required
  if (!exhibition.requires_registration) {
    return null;
  }

  // Check if registration is within the window
  const now = new Date();
  const registrationOpensAt = exhibition.registration_opens_at
    ? new Date(exhibition.registration_opens_at)
    : null;
  const registrationClosesAt = exhibition.registration_closes_at
    ? new Date(exhibition.registration_closes_at)
    : null;

  const isBeforeWindow = registrationOpensAt && now < registrationOpensAt;
  const isAfterWindow = registrationClosesAt && now > registrationClosesAt;

  const handleRegister = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await exhibitionsApi.register(exhibition.id);
      if (response.error) {
        setError(response.error.detail || response.error.message);
      } else {
        setShowRegisterDialog(false);
        showSuccess(t('registrationSuccess', { title: exhibition.title }));
        onRegistrationChange?.();
      }
    } catch {
      setError(t('registrationError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnregister = async (force: boolean = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await exhibitionsApi.unregister(exhibition.id, force);
      if (response.error) {
        // Check if it's a 409 with active bookings
        const detail = response.error.detail as { code?: string; booking_count?: number; message?: string } | string;
        if (
          response.error.status === 409 &&
          typeof detail === 'object' &&
          detail?.code === 'has_active_bookings'
        ) {
          // Show the force confirmation dialog
          setActiveBookingCount(detail.booking_count || 0);
          setShowUnregisterDialog(false);
          setShowForceUnregisterDialog(true);
        } else {
          const message = typeof detail === 'object' ? detail?.message : detail;
          setError(message || response.error.message);
        }
      } else {
        setShowUnregisterDialog(false);
        setShowForceUnregisterDialog(false);
        showSuccess(t('unregistrationSuccess'));
        onRegistrationChange?.();
      }
    } catch {
      setError(t('unregistrationError'));
    } finally {
      setIsLoading(false);
    }
  };

  // Not authenticated - show login prompt
  if (!isAuthenticated) {
    return (
      <Link href="/auth/login">
        <Button variant="primary">
          {t('loginToRegister')}
        </Button>
      </Link>
    );
  }

  // User is already registered
  if (exhibition.is_user_registered) {
    return (
      <>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2 py-1 text-sm font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 rounded">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            {t('registered')}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowUnregisterDialog(true)}
            className="text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400"
          >
            {t('unregister')}
          </Button>
        </div>

        <ConfirmDialog
          isOpen={showUnregisterDialog}
          onClose={() => setShowUnregisterDialog(false)}
          onConfirm={() => handleUnregister(false)}
          title={t('confirmUnregisterTitle')}
          message={error || t('confirmUnregisterMessage')}
          confirmLabel={t('confirmUnregister')}
          cancelLabel={t('keepRegistration')}
          variant="danger"
          isLoading={isLoading}
        />

        <ConfirmDialog
          isOpen={showForceUnregisterDialog}
          onClose={() => setShowForceUnregisterDialog(false)}
          onConfirm={() => handleUnregister(true)}
          title={t('confirmForceUnregisterTitle')}
          message={t('confirmForceUnregisterMessage', { count: activeBookingCount })}
          confirmLabel={t('confirmForceUnregister')}
          cancelLabel={t('cancel')}
          variant="danger"
          isLoading={isLoading}
        />
      </>
    );
  }

  // Registration not open
  if (!exhibition.is_registration_open) {
    return (
      <Button variant="secondary" disabled>
        {t('registrationClosed')}
      </Button>
    );
  }

  // Before registration window
  if (isBeforeWindow && registrationOpensAt) {
    const formattedDate = registrationOpensAt.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
    return (
      <Button variant="secondary" disabled>
        {t('registrationOpensAt', { date: formattedDate })}
      </Button>
    );
  }

  // After registration window
  if (isAfterWindow) {
    return (
      <Button variant="secondary" disabled>
        {t('registrationClosed')}
      </Button>
    );
  }

  // Email not verified
  if (user && !user.email_verified) {
    return (
      <div className="flex flex-col gap-1">
        <Button variant="secondary" disabled>
          {t('register')}
        </Button>
        <span className="text-xs text-amber-600 dark:text-amber-400">
          {t('emailVerificationRequired')}
        </span>
      </div>
    );
  }

  // Can register
  return (
    <>
      <div className="flex flex-col gap-1">
        <Button
          variant="success"
          onClick={() => setShowRegisterDialog(true)}
        >
          {t('register')}
        </Button>
        {error && (
          <span className="text-xs text-red-600 dark:text-red-400">{error}</span>
        )}
      </div>

      <ConfirmDialog
        isOpen={showRegisterDialog}
        onClose={() => setShowRegisterDialog(false)}
        onConfirm={handleRegister}
        title={t('confirmRegisterTitle', { title: exhibition.title })}
        message={t('confirmRegisterMessage')}
        confirmLabel={t('register')}
        cancelLabel={t('cancel')}
        variant="default"
        isLoading={isLoading}
      />
    </>
  );
}
