'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card } from '@/components/ui';
import { LoginForm } from '@/components/auth';

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
          <LoginForm />
        </Card.Content>
        <Card.Footer className="text-center">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {t('noAccount')}{' '}
            <Link
              href="/auth/register"
              className="text-ludis-primary hover:underline"
            >
              {t('registerButton')}
            </Link>
          </p>
        </Card.Footer>
      </Card>
    </div>
  );
}
