'use client';

import { useTranslations } from 'next-intl';
import { Card } from '@/components/ui';

export default function LoginPage() {
  const t = useTranslations('Auth');

  return (
    <div className="max-w-md mx-auto mt-8">
      <Card>
        <Card.Header>
          <Card.Title>{t('loginTitle')}</Card.Title>
          <Card.Description>{t('loginSubtitle')}</Card.Description>
        </Card.Header>
        <Card.Content>
          <p className="text-slate-400 text-center py-8">
            Login form coming soon (Issue #59)
          </p>
        </Card.Content>
      </Card>
    </div>
  );
}
