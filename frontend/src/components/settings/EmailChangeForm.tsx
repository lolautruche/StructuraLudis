'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { userApi } from '@/lib/api';
import { Button, Input } from '@/components/ui';

const emailChangeSchema = z.object({
  new_email: z.string().email(),
  password: z.string().min(1),
});

type EmailChangeFormData = z.infer<typeof emailChangeSchema>;

interface EmailChangeFormProps {
  onSuccess?: () => void;
}

export function EmailChangeForm({ onSuccess }: EmailChangeFormProps) {
  const t = useTranslations('Settings');
  const { user } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<EmailChangeFormData>({
    resolver: zodResolver(emailChangeSchema),
    defaultValues: {
      new_email: '',
      password: '',
    },
  });

  const onSubmit = async (data: EmailChangeFormData) => {
    setServerError(null);
    setSuccess(false);

    const response = await userApi.requestEmailChange({
      new_email: data.new_email,
      password: data.password,
    });

    if (response.error) {
      // Map specific errors
      if (response.error.message?.includes('already in use')) {
        setServerError(t('emailInUse'));
      } else if (response.error.message?.includes('different')) {
        setServerError(t('emailSameAsCurrent'));
      } else if (response.error.message?.includes('incorrect')) {
        setServerError(t('wrongPassword'));
      } else {
        setServerError(response.error.message || t('emailChangeError'));
      }
    } else {
      setSuccess(true);
      reset();
      onSuccess?.();
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {serverError && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-600 dark:text-red-400 text-sm">
          {serverError}
        </div>
      )}

      {success && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-600 dark:text-emerald-400 text-sm">
          {t('emailChangeRequested')}
        </div>
      )}

      <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          {t('currentEmail')}:{' '}
          <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
            {user?.email}
          </span>
        </p>
      </div>

      <Input
        {...register('new_email')}
        type="email"
        label={t('newEmail')}
        placeholder={t('newEmailPlaceholder')}
        error={errors.new_email?.message}
        autoComplete="email"
      />

      <Input
        {...register('password')}
        type="password"
        label={t('passwordForEmail')}
        helperText={t('passwordForEmailHelper')}
        error={errors.password?.message}
        autoComplete="current-password"
      />

      <div className="pt-2">
        <Button
          type="submit"
          variant="primary"
          disabled={isSubmitting}
        >
          {isSubmitting ? t('changingEmail') : t('changeEmail')}
        </Button>
      </div>
    </form>
  );
}
