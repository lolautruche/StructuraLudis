'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { Button, Input, Checkbox } from '@/components/ui';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
  rememberMe: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  redirectTo?: string;
}

export function LoginForm({ redirectTo = '/my/dashboard' }: LoginFormProps) {
  const t = useTranslations('Auth');
  const tErrors = useTranslations('Errors');
  const router = useRouter();
  const { login } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);

    const result = await login({
      email: data.email,
      password: data.password,
    });

    if (result.success) {
      router.push(redirectTo);
    } else {
      // Map API errors to translated messages
      if (result.error?.includes('Invalid') || result.error?.includes('credentials')) {
        setServerError(t('invalidCredentials'));
      } else {
        setServerError(result.error || tErrors('generic'));
      }
    }
  };

  return (
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

      <Input
        {...register('password')}
        type="password"
        label={t('password')}
        error={errors.password?.message}
        autoComplete="current-password"
      />

      <div className="flex items-center justify-between">
        <Checkbox {...register('rememberMe')} label={t('rememberMe')} />
        <a
          href="#"
          className="text-sm text-ludis-primary hover:text-ludis-primary/80"
        >
          {t('forgotPassword')}
        </a>
      </div>

      <Button
        type="submit"
        variant="primary"
        className="w-full"
        disabled={isSubmitting}
      >
        {isSubmitting ? '...' : t('loginButton')}
      </Button>
    </form>
  );
}
