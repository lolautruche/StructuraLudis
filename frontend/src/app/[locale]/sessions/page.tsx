'use client';

import { useTranslations } from 'next-intl';
import { Card } from '@/components/ui';

export default function SessionsPage() {
  const t = useTranslations('Discovery');

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('title')}</h1>

      <Card>
        <Card.Content>
          <p className="text-slate-400 text-center py-12">
            Session discovery coming soon (Issue #9)
          </p>
        </Card.Content>
      </Card>
    </div>
  );
}
