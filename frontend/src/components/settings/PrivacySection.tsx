'use client';

import { useTranslations, useLocale } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui';

export function PrivacySection() {
  const t = useTranslations('Settings');
  const locale = useLocale();
  const { user } = useAuth();

  const formatDate = (dateString: string | null) => {
    if (!dateString) return t('notAccepted');
    const date = new Date(dateString);
    return date.toLocaleDateString(locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Privacy consent info */}
      <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--color-border)' }}>
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          {t('privacyAcceptedOn')}:{' '}
          <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
            {formatDate(user?.privacy_accepted_at ?? null)}
          </span>
        </p>
      </div>

      {/* Data export */}
      <div className="space-y-2">
        <Button
          variant="secondary"
          disabled
          className="w-full justify-center"
        >
          {t('downloadData')}
          <span className="ml-2 text-xs opacity-60">({t('comingSoon')})</span>
        </Button>
      </div>

      {/* Account deletion */}
      <div className="space-y-2">
        <Button
          variant="danger"
          disabled
          className="w-full justify-center"
        >
          {t('deleteAccount')}
          <span className="ml-2 text-xs opacity-60">({t('comingSoon')})</span>
        </Button>
      </div>
    </div>
  );
}
