'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { userApi } from '@/lib/api';
import { Button, Input } from '@/components/ui';

const passwordSchema = z
  .object({
    current_password: z.string().min(1),
    new_password: z.string().min(8),
    confirm_password: z.string().min(8),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    path: ['confirm_password'],
  });

type PasswordFormData = z.infer<typeof passwordSchema>;

interface PasswordFormProps {
  onSuccess?: () => void;
}

export function PasswordForm({ onSuccess }: PasswordFormProps) {
  const t = useTranslations('Settings');
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  const newPassword = watch('new_password');

  // Password strength calculation (reused from RegisterForm)
  const getPasswordStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (!pwd) return { score: 0, label: '', color: 'bg-slate-600' };

    let score = 0;
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;
    if (/\d/.test(pwd)) score++;
    if (/[^a-zA-Z0-9]/.test(pwd)) score++;

    if (score <= 2) return { score, label: 'Weak', color: 'bg-red-500' };
    if (score <= 3) return { score, label: 'Medium', color: 'bg-amber-500' };
    return { score, label: 'Strong', color: 'bg-emerald-500' };
  };

  const passwordStrength = getPasswordStrength(newPassword);

  const onSubmit = async (data: PasswordFormData) => {
    setServerError(null);
    setSuccess(false);

    const response = await userApi.changePassword({
      current_password: data.current_password,
      new_password: data.new_password,
    });

    if (response.error) {
      if (response.error.message?.includes('incorrect')) {
        setServerError(t('wrongPassword'));
      } else {
        setServerError(response.error.message || t('passwordChangeError'));
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
          {t('passwordChanged')}
        </div>
      )}

      <Input
        {...register('current_password')}
        type="password"
        label={t('currentPassword')}
        error={errors.current_password?.message}
        autoComplete="current-password"
      />

      <div className="space-y-2">
        <Input
          {...register('new_password')}
          type="password"
          label={t('newPassword')}
          error={errors.new_password ? t('passwordTooShort') : undefined}
          autoComplete="new-password"
        />
        {newPassword && (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${passwordStrength.color}`}
                style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
              />
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {passwordStrength.label}
            </span>
          </div>
        )}
      </div>

      <Input
        {...register('confirm_password')}
        type="password"
        label={t('confirmNewPassword')}
        error={errors.confirm_password ? t('passwordMismatch') : undefined}
        autoComplete="new-password"
      />

      <div className="pt-2">
        <Button
          type="submit"
          variant="primary"
          disabled={isSubmitting}
        >
          {isSubmitting ? t('changingPassword') : t('changePassword')}
        </Button>
      </div>
    </form>
  );
}
