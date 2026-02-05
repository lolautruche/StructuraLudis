'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Button } from '@/components/ui';
import { authApi } from '@/lib/api/endpoints/auth';
import { useAuth } from '@/contexts/AuthContext';

type VerificationState = 'loading' | 'success' | 'error';

export default function VerifyEmailPage() {
  const t = useTranslations('Auth');
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

    async function verifyEmail() {
      if (!token) {
        setState('error');
        setErrorMessage(t('verificationFailedMessage'));
        return;
      }

      verificationAttempted.current = true;

      try {
        const response = await authApi.verifyEmail(token);

        if (response.data?.success) {
          setState('success');
          // Refresh user data to update email_verified status
          doRefreshUser();
        } else {
          setState('error');
          // Always use translated message (backend returns English)
          setErrorMessage(t('verificationFailedMessage'));
        }
      } catch {
        setState('error');
        setErrorMessage(t('verificationFailedMessage'));
      }
    }

    verifyEmail();
  }, [token, t, doRefreshUser]);

  return (
    <div className="max-w-md mx-auto mt-8">
      <Card>
        <Card.Header>
          <Card.Title>
            {state === 'loading' && t('verifying')}
            {state === 'success' && t('verificationSuccess')}
            {state === 'error' && t('verificationFailed')}
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
                {t('verificationSuccessMessage')}
              </p>
              <Link href="/auth/login">
                <Button variant="primary">{t('goToLogin')}</Button>
              </Link>
            </div>
          )}

          {state === 'error' && (
            <div className="text-center py-4">
              <div className="text-4xl mb-4 text-red-500">&#10007;</div>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {errorMessage}
              </p>
              <Link href="/auth/login">
                <Button variant="primary">{t('goToLogin')}</Button>
              </Link>
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
