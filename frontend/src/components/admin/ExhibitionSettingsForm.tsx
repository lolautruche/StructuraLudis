'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { exhibitionsApi, Exhibition, ExhibitionUpdate } from '@/lib/api';
import { Button, Input, Select, Textarea, Checkbox } from '@/components/ui';

const TIMEZONES = [
  { value: 'Europe/Paris', label: 'Europe/Paris (CET)' },
  { value: 'Europe/London', label: 'Europe/London (GMT)' },
  { value: 'Europe/Berlin', label: 'Europe/Berlin (CET)' },
  { value: 'Europe/Brussels', label: 'Europe/Brussels (CET)' },
  { value: 'UTC', label: 'UTC' },
];

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Francais' },
];

const STATUS_VALUES = ['DRAFT', 'PUBLISHED', 'SUSPENDED', 'ARCHIVED'] as const;

const settingsSchema = z.object({
  title: z.string().min(1).max(255),
  description: z.string().optional().nullable(),
  start_date: z.string().min(1),
  end_date: z.string().min(1),
  location_name: z.string().max(255).optional().nullable(),
  city: z.string().max(100).optional().nullable(),
  timezone: z.string().max(50),
  grace_period_minutes: z.coerce.number().min(0).max(120),
  status: z.enum(['DRAFT', 'PUBLISHED', 'SUSPENDED', 'ARCHIVED']),
  is_registration_open: z.boolean(),
  registration_opens_at: z.string().optional().nullable(),
  registration_closes_at: z.string().optional().nullable(),
  requires_registration: z.boolean(),
  primary_language: z.string().max(10),
});

type SettingsFormData = z.infer<typeof settingsSchema>;

interface ExhibitionSettingsFormProps {
  exhibition: Exhibition;
  onUpdate: (exhibition: Exhibition) => void;
}

function formatDateTimeLocal(isoString: string | null): string {
  if (!isoString) return '';
  const date = new Date(isoString);
  // Format as YYYY-MM-DDTHH:mm for datetime-local input
  return date.toISOString().slice(0, 16);
}

export function ExhibitionSettingsForm({
  exhibition,
  onUpdate,
}: ExhibitionSettingsFormProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      title: exhibition.title,
      description: exhibition.description || '',
      start_date: formatDateTimeLocal(exhibition.start_date),
      end_date: formatDateTimeLocal(exhibition.end_date),
      location_name: exhibition.location_name || '',
      city: exhibition.city || '',
      timezone: exhibition.timezone,
      grace_period_minutes: exhibition.grace_period_minutes,
      status: exhibition.status,
      is_registration_open: exhibition.is_registration_open,
      registration_opens_at: formatDateTimeLocal(exhibition.registration_opens_at),
      registration_closes_at: formatDateTimeLocal(exhibition.registration_closes_at),
      requires_registration: exhibition.requires_registration,
      primary_language: exhibition.primary_language,
    },
  });

  const requiresRegistration = watch('requires_registration');

  const onSubmit = async (data: SettingsFormData) => {
    setServerError(null);
    setSuccess(false);

    const updateData: ExhibitionUpdate = {
      title: data.title,
      description: data.description || undefined,
      start_date: new Date(data.start_date).toISOString(),
      end_date: new Date(data.end_date).toISOString(),
      location_name: data.location_name || undefined,
      city: data.city || undefined,
      timezone: data.timezone,
      grace_period_minutes: data.grace_period_minutes,
      status: data.status,
      is_registration_open: data.is_registration_open,
      registration_opens_at: data.registration_opens_at
        ? new Date(data.registration_opens_at).toISOString()
        : null,
      registration_closes_at: data.registration_closes_at
        ? new Date(data.registration_closes_at).toISOString()
        : null,
      requires_registration: data.requires_registration,
      primary_language: data.primary_language,
    };

    const response = await exhibitionsApi.update(exhibition.id, updateData);

    if (response.error) {
      setServerError(response.error.message || t('saveError'));
    } else if (response.data) {
      setSuccess(true);
      onUpdate(response.data);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {serverError && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-600 dark:text-red-400 text-sm">
          {serverError}
        </div>
      )}

      {success && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-600 dark:text-emerald-400 text-sm">
          {t('settingsSaved')}
        </div>
      )}

      {/* Basic Info */}
      <div className="space-y-4">
        <h3
          className="text-lg font-medium"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('basicInfo')}
        </h3>

        <Input
          {...register('title')}
          label={t('exhibitionTitle')}
          error={errors.title?.message}
        />

        <Textarea
          {...register('description')}
          label={t('description')}
          rows={3}
          error={errors.description?.message}
        />

        <Select
          {...register('status')}
          label={t('status')}
          options={STATUS_VALUES.map((status) => ({
            value: status,
            label: t(`statuses.${status}`),
          }))}
          error={errors.status?.message}
        />
      </div>

      {/* Dates */}
      <div className="space-y-4">
        <h3
          className="text-lg font-medium"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('dates')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            {...register('start_date')}
            type="datetime-local"
            label={t('startDate')}
            error={errors.start_date?.message}
          />

          <Input
            {...register('end_date')}
            type="datetime-local"
            label={t('endDate')}
            error={errors.end_date?.message}
          />
        </div>
      </div>

      {/* Location */}
      <div className="space-y-4">
        <h3
          className="text-lg font-medium"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('location')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            {...register('location_name')}
            label={t('locationName')}
            error={errors.location_name?.message}
          />

          <Input
            {...register('city')}
            label={t('city')}
            error={errors.city?.message}
          />
        </div>

        <Select
          {...register('timezone')}
          label={t('timezone')}
          options={TIMEZONES}
          error={errors.timezone?.message}
        />
      </div>

      {/* Registration */}
      <div className="space-y-4">
        <h3
          className="text-lg font-medium"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('registration')}
        </h3>

        <div className="space-y-1">
          <Checkbox
            {...register('requires_registration')}
            label={t('requiresRegistration')}
          />
          <p className="text-xs text-slate-500 dark:text-slate-400 ml-7">
            {t('requiresRegistrationHelper')}
          </p>
        </div>

        <Checkbox
          {...register('is_registration_open')}
          label={t('registrationOpen')}
          disabled={!requiresRegistration}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            {...register('registration_opens_at')}
            type="datetime-local"
            label={t('registrationOpensAt')}
            error={errors.registration_opens_at?.message}
          />

          <Input
            {...register('registration_closes_at')}
            type="datetime-local"
            label={t('registrationClosesAt')}
            error={errors.registration_closes_at?.message}
          />
        </div>
      </div>

      {/* Settings */}
      <div className="space-y-4">
        <h3
          className="text-lg font-medium"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('sessionSettings')}
        </h3>

        <Input
          {...register('grace_period_minutes')}
          type="number"
          min={0}
          max={120}
          label={t('gracePeriod')}
          helperText={t('gracePeriodHelper')}
          error={errors.grace_period_minutes?.message}
        />

        <Select
          {...register('primary_language')}
          label={t('primaryLanguage')}
          options={LANGUAGES}
          error={errors.primary_language?.message}
        />
      </div>

      {/* Submit */}
      <div className="pt-4 flex justify-end">
        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? t('saving') : tCommon('save')}
        </Button>
      </div>
    </form>
  );
}
