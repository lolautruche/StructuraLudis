'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Button, Input } from '@/components/ui';
import { authApi } from '@/lib/api';

const forgotPasswordSchema = z.object({
  email: z.string().email(),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const t = useTranslations('Auth');
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setServerError(null);

    const response = await authApi.forgotPassword({ email: data.email });

    if (response.error) {
      setServerError(response.error.message || t('forgotPasswordError'));
    } else {
      setSuccess(true);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8">
      <Card>
        <Card.Header>
          <Card.Title>{t('forgotPasswordTitle')}</Card.Title>
          <Card.Description>{t('forgotPasswordSubtitle')}</Card.Description>
        </Card.Header>
        <Card.Content>
          {success ? (
            <div className="text-center py-4">
              <div className="text-4xl mb-4 text-emerald-500">&#10003;</div>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {t('forgotPasswordSuccess')}
              </p>
              <Link href="/auth/login">
                <Button variant="primary">{t('backToLogin')}</Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {serverError && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  {serverError}
                </div>
              )}

              <Input
                {...register('email')}
                type="email"
                label={t('email')}
                placeholder="nom@exemple.com"
                error={errors.email?.message}
                autoComplete="email"
                autoFocus
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={isSubmitting}
              >
                {isSubmitting ? '...' : t('sendResetLink')}
              </Button>
            </form>
          )}
        </Card.Content>
        <Card.Footer className="text-center">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            <Link
              href="/auth/login"
              className="text-ludis-primary hover:underline"
            >
              {t('backToLogin')}
            </Link>
          </p>
        </Card.Footer>
      </Card>
    </div>
  );
}
