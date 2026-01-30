'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card } from '@/components/ui';
import { RegisterForm } from '@/components/auth';

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
          <RegisterForm />
        </Card.Content>
        <Card.Footer className="text-center">
          <p className="text-sm text-slate-400">
            {t('hasAccount')}{' '}
            <Link
              href="/auth/login"
              className="text-ludis-primary hover:underline"
            >
              {t('loginButton')}
            </Link>
          </p>
        </Card.Footer>
      </Card>
    </div>
  );
}
