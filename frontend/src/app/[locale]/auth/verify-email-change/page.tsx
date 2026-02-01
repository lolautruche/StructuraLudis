'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Button } from '@/components/ui';
import { userApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

type VerificationState = 'loading' | 'success' | 'error';

export default function VerifyEmailChangePage() {
  const t = useTranslations('Settings');
  const tAuth = useTranslations('Auth');
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();
  const [state, setState] = useState<VerificationState>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const verificationAttempted = useRef(false);

  const token = searchParams.get('token');

  const doRefreshUser = useCallback(() => {
    refreshUser();
  }, [refreshUser]);

  useEffect(() => {
    // Prevent double verification attempts
    if (verificationAttempted.current) {
      return;
    }

    async function verifyEmailChange() {
      if (!token) {
        setState('error');
        setErrorMessage(t('emailChangeFailedMessage'));
        return;
      }

      verificationAttempted.current = true;

      try {
        const response = await userApi.verifyEmailChange(token);

        if (response.data?.success) {
          setState('success');
          // Refresh user data to update email
          doRefreshUser();
        } else {
          setState('error');
          if (response.error?.detail?.includes('expired')) {
            setErrorMessage(t('emailChangeExpired'));
          } else {
            setErrorMessage(response.error?.detail || t('emailChangeFailedMessage'));
          }
        }
      } catch {
        setState('error');
        setErrorMessage(t('emailChangeFailedMessage'));
      }
    }

    verifyEmailChange();
  }, [token, t, doRefreshUser]);

  return (
    <div className="max-w-md mx-auto mt-8">
      <Card>
        <Card.Header>
          <Card.Title>
            {state === 'loading' && t('verifyingEmailChange')}
            {state === 'success' && t('emailChangeSuccess')}
            {state === 'error' && t('emailChangeFailed')}
          </Card.Title>
        </Card.Header>
        <Card.Content>
          {state === 'loading' && (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ludis-primary" />
            </div>
          )}

          {state === 'success' && (
            <div className="text-center py-4">
              <div className="text-4xl mb-4 text-emerald-500">&#10003;</div>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {t('emailChangeSuccessMessage')}
              </p>
              <Link href="/auth/login">
                <Button variant="primary">
                  {tAuth('goToLogin')}
                </Button>
              </Link>
            </div>
          )}

          {state === 'error' && (
            <div className="text-center py-4">
              <div className="text-4xl mb-4 text-red-500">&#10007;</div>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {errorMessage}
              </p>
              <Link href="/my/settings">
                <Button variant="primary">{t('title')}</Button>
              </Link>
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
