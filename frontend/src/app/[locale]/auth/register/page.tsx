'use client';

import { useTranslations } from 'next-intl';
import { Card } from '@/components/ui';

export default function RegisterPage() {
  const t = useTranslations('Auth');

  return (
    <div className="max-w-md mx-auto mt-8">
      <Card>
        <Card.Header>
          <Card.Title>{t('registerTitle')}</Card.Title>
          <Card.Description>{t('registerSubtitle')}</Card.Description>
        </Card.Header>
        <Card.Content>
          <p className="text-slate-400 text-center py-8">
            Register form coming soon (Issue #59)
          </p>
        </Card.Content>
      </Card>
    </div>
  );
}
