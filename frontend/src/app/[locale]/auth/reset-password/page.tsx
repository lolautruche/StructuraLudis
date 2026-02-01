'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { Link } from '@/i18n/routing';
import { Card, Button, Input } from '@/components/ui';
import { authApi } from '@/lib/api';
import { PasswordStrength } from '@/components/auth';

const resetPasswordSchema = z
  .object({
    new_password: z.string().min(8),
    confirm_password: z.string().min(1),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'passwordsDoNotMatch',
    path: ['confirm_password'],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const t = useTranslations('Auth');
  const tSettings = useTranslations('Settings');
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      new_password: '',
      confirm_password: '',
    },
  });

  const newPassword = watch('new_password');

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      setServerError(t('invalidResetToken'));
      return;
    }

    setServerError(null);

    const response = await authApi.resetPassword({
      token,
      new_password: data.new_password,
    });

    if (response.error) {
      if (response.error.message?.includes('expired')) {
        setServerError(t('resetTokenExpired'));
      } else if (response.error.message?.includes('Invalid')) {
        setServerError(t('invalidResetToken'));
      } else {
        setServerError(response.error.message || t('resetPasswordError'));
      }
    } else {
      setSuccess(true);
    }
  };

  // No token provided
  if (!token) {
    return (
      <div className="max-w-md mx-auto mt-8">
        <Card>
          <Card.Header>
            <Card.Title>{t('resetPasswordTitle')}</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="text-center py-4">
              <div className="text-4xl mb-4 text-red-500">&#10007;</div>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {t('invalidResetToken')}
              </p>
              <Link href="/auth/forgot-password">
                <Button variant="primary">{t('requestNewLink')}</Button>
              </Link>
            </div>
          </Card.Content>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-8">
      <Card>
        <Card.Header>
          <Card.Title>{t('resetPasswordTitle')}</Card.Title>
          <Card.Description>{t('resetPasswordSubtitle')}</Card.Description>
        </Card.Header>
        <Card.Content>
          {success ? (
            <div className="text-center py-4">
              <div className="text-4xl mb-4 text-emerald-500">&#10003;</div>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {t('resetPasswordSuccess')}
              </p>
              <Link href="/auth/login">
                <Button variant="primary">{t('goToLogin')}</Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {serverError && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  {serverError}
                </div>
              )}

              <div>
                <Input
                  {...register('new_password')}
                  type="password"
                  label={tSettings('newPassword')}
                  error={errors.new_password?.message}
                  autoComplete="new-password"
                  autoFocus
                />
                <PasswordStrength password={newPassword} />
              </div>

              <Input
                {...register('confirm_password')}
                type="password"
                label={tSettings('confirmNewPassword')}
                error={
                  errors.confirm_password?.message === 'passwordsDoNotMatch'
                    ? tSettings('passwordsMismatch')
                    : errors.confirm_password?.message
                }
                autoComplete="new-password"
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={isSubmitting}
              >
                {isSubmitting ? '...' : t('resetPasswordButton')}
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
