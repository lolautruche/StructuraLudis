'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { authApi } from '@/lib/api/endpoints/auth';
import { Button } from '@/components/ui';

export function EmailVerificationBanner() {
  const t = useTranslations('Auth');
  const { user } = useAuth();
  const [isResending, setIsResending] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Cooldown timer
  useEffect(() => {
    if (cooldown <= 0) return;

    const timer = setInterval(() => {
      setCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown]);

  const handleResend = useCallback(async () => {
    if (isResending || cooldown > 0) return;

    setIsResending(true);
    setMessage(null);

    try {
      const response = await authApi.resendVerification();

      if (response.data?.success) {
        setMessage({ type: 'success', text: t('verificationEmailSent') });
        setCooldown(60); // 60 second cooldown
      } else if (response.error) {
        // Check if rate limited
        if (response.error.status === 429) {
          const match = response.error.detail?.match(/(\d+)/);
          const seconds = match ? parseInt(match[1], 10) : 60;
          setCooldown(seconds);
        }
        setMessage({ type: 'error', text: response.error.detail || response.error.message });
      }
    } catch {
      setMessage({ type: 'error', text: t('verificationFailed') });
    } finally {
      setIsResending(false);
    }
  }, [isResending, cooldown, t]);

  // Don't render if user is not logged in or email is verified
  if (!user || user.email_verified) {
    return null;
  }

  return (
    <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex-1">
          <p className="text-amber-700 dark:text-amber-400 text-sm font-medium">
            {t('emailNotVerified')}
          </p>
          {message && (
            <p
              className={`text-sm mt-1 ${
                message.type === 'success'
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {message.text}
            </p>
          )}
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleResend}
          disabled={isResending || cooldown > 0}
        >
          {isResending
            ? t('resendingVerification')
            : cooldown > 0
              ? t('resendCooldown', { seconds: cooldown })
              : t('resendVerification')}
        </Button>
      </div>
    </div>
  );
}
