'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { userApi } from '@/lib/api';
import { Button, Input, Select } from '@/components/ui';

const TIMEZONES = [
  { value: 'Europe/Paris', label: 'Europe/Paris (CET)' },
  { value: 'Europe/London', label: 'Europe/London (GMT)' },
  { value: 'Europe/Berlin', label: 'Europe/Berlin (CET)' },
  { value: 'Europe/Brussels', label: 'Europe/Brussels (CET)' },
  { value: 'Europe/Amsterdam', label: 'Europe/Amsterdam (CET)' },
  { value: 'Europe/Rome', label: 'Europe/Rome (CET)' },
  { value: 'Europe/Madrid', label: 'Europe/Madrid (CET)' },
  { value: 'Europe/Zurich', label: 'Europe/Zurich (CET)' },
  { value: 'America/New_York', label: 'America/New_York (EST)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST)' },
  { value: 'America/Chicago', label: 'America/Chicago (CST)' },
  { value: 'America/Toronto', label: 'America/Toronto (EST)' },
  { value: 'America/Montreal', label: 'America/Montreal (EST)' },
  { value: 'UTC', label: 'UTC' },
];

const LOCALES = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Francais' },
];

const profileSchema = z.object({
  full_name: z.string().max(255).optional().nullable(),
  birth_date: z.string().optional().nullable(),
  timezone: z.string().optional().nullable(),
  locale: z.string().optional().nullable(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

interface ProfileFormProps {
  onSuccess?: () => void;
}

export function ProfileForm({ onSuccess }: ProfileFormProps) {
  const t = useTranslations('Settings');
  const { user, refreshUser } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name || '',
      birth_date: user?.birth_date || '',
      timezone: user?.timezone || '',
      locale: user?.locale || 'en',
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    setServerError(null);
    setSuccess(false);

    const response = await userApi.updateProfile({
      full_name: data.full_name || null,
      birth_date: data.birth_date || null,
      timezone: data.timezone || null,
      locale: data.locale || null,
    });

    if (response.error) {
      setServerError(response.error.message || t('profileSaveError'));
    } else {
      setSuccess(true);
      await refreshUser();
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
          {t('profileSaved')}
        </div>
      )}

      <Input
        {...register('full_name')}
        type="text"
        label={t('fullName')}
        placeholder={t('fullNamePlaceholder')}
        error={errors.full_name?.message}
      />

      <Input
        {...register('birth_date')}
        type="date"
        label={t('birthDate')}
        helperText={t('birthDateHelper')}
        error={errors.birth_date?.message}
      />

      <Select
        {...register('timezone')}
        label={t('timezone')}
        options={TIMEZONES}
        placeholder={t('selectTimezone')}
        error={errors.timezone?.message}
      />

      <Select
        {...register('locale')}
        label={t('locale')}
        options={LOCALES}
        error={errors.locale?.message}
      />

      <div className="pt-2">
        <Button
          type="submit"
          variant="primary"
          disabled={isSubmitting}
        >
          {isSubmitting ? t('saving') : t('saveProfile')}
        </Button>
      </div>
    </form>
  );
}
