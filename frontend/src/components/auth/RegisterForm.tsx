'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { Link, useRouter } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { Button, Input, Checkbox } from '@/components/ui';

const registerSchema = z
  .object({
    email: z.string().email(),
    fullName: z.string().optional(),
    password: z.string().min(8),
    confirmPassword: z.string().min(8),
    acceptPrivacy: z.boolean(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
  })
  .refine((data) => data.acceptPrivacy === true, {
    path: ['acceptPrivacy'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const t = useTranslations('Auth');
  const tErrors = useTranslations('Errors');
  const router = useRouter();
  const { register: registerUser } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      fullName: '',
      password: '',
      confirmPassword: '',
      acceptPrivacy: false,
    },
  });

  const password = watch('password');

  // Password strength calculation
  const getPasswordStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (!pwd) return { score: 0, label: '', color: 'bg-slate-600' };

    let score = 0;
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;
    if (/\d/.test(pwd)) score++;
    if (/[^a-zA-Z0-9]/.test(pwd)) score++;

    if (score <= 2) return { score, label: 'Faible', color: 'bg-red-500' };
    if (score <= 3) return { score, label: 'Moyen', color: 'bg-amber-500' };
    return { score, label: 'Fort', color: 'bg-emerald-500' };
  };

  const passwordStrength = getPasswordStrength(password);

  const onSubmit = async (data: RegisterFormData) => {
    setServerError(null);

    const result = await registerUser({
      email: data.email,
      password: data.password,
      full_name: data.fullName || undefined,
      accept_privacy_policy: data.acceptPrivacy,
    });

    if (result.success) {
      setSuccess(true);
      // Redirect to login after short delay
      setTimeout(() => {
        router.push('/auth/login');
      }, 2000);
    } else {
      // Map API errors to translated messages
      if (result.error?.includes('email') && result.error?.includes('exists')) {
        setServerError(t('emailExists'));
      } else {
        setServerError(result.error || tErrors('generic'));
      }
    }
  };

  if (success) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-4">✓</div>
        <h3 className="text-lg font-semibold text-emerald-400 mb-2">
          Compte créé avec succès !
        </h3>
        <p className="text-slate-400">
          Redirection vers la page de connexion...
        </p>
      </div>
    );
  }

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
        {...register('fullName')}
        type="text"
        label={t('fullName')}
        placeholder="Jean Dupont"
        error={errors.fullName?.message}
        autoComplete="name"
      />

      <div className="space-y-2">
        <Input
          {...register('password')}
          type="password"
          label={t('password')}
          error={errors.password ? t('passwordTooShort') : undefined}
          autoComplete="new-password"
        />
        {password && (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${passwordStrength.color}`}
                style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
              />
            </div>
            <span className="text-xs text-slate-400">{passwordStrength.label}</span>
          </div>
        )}
      </div>

      <Input
        {...register('confirmPassword')}
        type="password"
        label={t('confirmPassword')}
        error={errors.confirmPassword ? t('passwordMismatch') : undefined}
        autoComplete="new-password"
      />

      <div className="pt-2">
        <Checkbox
          {...register('acceptPrivacy')}
          error={errors.acceptPrivacy ? t('privacyRequired') : undefined}
          label={
            <span>
              J&apos;accepte la{' '}
              <Link
                href="/privacy"
                className="text-ludis-primary hover:underline"
                target="_blank"
              >
                politique de confidentialité
              </Link>
            </span>
          }
        />
      </div>

      <Button
        type="submit"
        variant="primary"
        className="w-full"
        disabled={isSubmitting}
      >
        {isSubmitting ? '...' : t('registerButton')}
      </Button>
    </form>
  );
}
