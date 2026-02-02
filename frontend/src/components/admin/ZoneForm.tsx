'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { Zone, ZoneCreate, ZoneType } from '@/lib/api';
import { Button, Input, Select, Textarea, Checkbox } from '@/components/ui';

const ZONE_TYPE_VALUES: ZoneType[] = ['MIXED', 'RPG', 'BOARD_GAME', 'WARGAME', 'TCG', 'DEMO'];

const zoneSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional().nullable(),
  type: z.enum(['RPG', 'BOARD_GAME', 'WARGAME', 'TCG', 'DEMO', 'MIXED']),
  moderation_required: z.boolean(),
  allow_public_proposals: z.boolean(),
});

type ZoneFormData = z.infer<typeof zoneSchema>;

interface ZoneFormProps {
  zone?: Zone | null;
  exhibitionId: string;
  onSubmit: (data: ZoneCreate) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

export function ZoneForm({
  zone,
  exhibitionId,
  onSubmit,
  onCancel,
  isSubmitting,
}: ZoneFormProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ZoneFormData>({
    resolver: zodResolver(zoneSchema),
    defaultValues: {
      name: '',
      description: '',
      type: 'MIXED',
      moderation_required: true,
      allow_public_proposals: false,
    },
  });

  useEffect(() => {
    if (zone) {
      reset({
        name: zone.name,
        description: zone.description || '',
        type: zone.type,
        moderation_required: zone.moderation_required ?? true,
        allow_public_proposals: zone.allow_public_proposals ?? false,
      });
    } else {
      reset({
        name: '',
        description: '',
        type: 'MIXED',
        moderation_required: true,
        allow_public_proposals: false,
      });
    }
  }, [zone, reset]);

  const handleFormSubmit = async (data: ZoneFormData) => {
    const payload: ZoneCreate & { moderation_required?: boolean; allow_public_proposals?: boolean } = {
      exhibition_id: exhibitionId,
      name: data.name,
      description: data.description || undefined,
      type: data.type,
      allow_public_proposals: data.allow_public_proposals,
    };
    // Include moderation_required when editing (update)
    if (zone) {
      payload.moderation_required = data.moderation_required;
    }
    await onSubmit(payload as ZoneCreate);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Input
        {...register('name')}
        label={t('zoneName')}
        placeholder={t('zoneNamePlaceholder')}
        error={errors.name?.message}
      />

      <Textarea
        {...register('description')}
        label={t('zoneDescription')}
        rows={2}
        error={errors.description?.message}
      />

      <Select
        {...register('type')}
        label={t('zoneType')}
        options={ZONE_TYPE_VALUES.map((type) => ({
          value: type,
          label: t(`zoneTypes.${type}`),
        }))}
        error={errors.type?.message}
      />

      {/* Allow public proposals toggle */}
      <div className="flex items-start gap-3 py-2">
        <Checkbox
          {...register('allow_public_proposals')}
          id="allow_public_proposals"
          className="mt-0.5"
        />
        <div>
          <label
            htmlFor="allow_public_proposals"
            className="text-sm font-medium cursor-pointer"
            style={{ color: 'var(--color-text-primary)' }}
          >
            {t('allowPublicProposals')}
          </label>
          <p
            className="text-xs mt-0.5"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            {t('allowPublicProposalsHelp')}
          </p>
        </div>
      </div>

      {/* Session moderation toggle - only show when editing and public proposals enabled */}
      {zone && (
        <div className="flex items-start gap-3 py-2">
          <Checkbox
            {...register('moderation_required')}
            id="moderation_required"
            className="mt-0.5"
          />
          <div>
            <label
              htmlFor="moderation_required"
              className="text-sm font-medium cursor-pointer"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {t('moderationRequired')}
            </label>
            <p
              className="text-xs mt-0.5"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              {t('moderationRequiredHelp')}
            </p>
          </div>
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          {tCommon('cancel')}
        </Button>
        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? t('saving') : tCommon('save')}
        </Button>
      </div>
    </form>
  );
}
