'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { Zone, ZoneCreate, ZoneType } from '@/lib/api';
import { Button, Input, Select, Textarea } from '@/components/ui';

const ZONE_TYPE_VALUES: ZoneType[] = ['MIXED', 'RPG', 'BOARD_GAME', 'WARGAME', 'TCG', 'DEMO'];

const zoneSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional().nullable(),
  type: z.enum(['RPG', 'BOARD_GAME', 'WARGAME', 'TCG', 'DEMO', 'MIXED']),
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
    },
  });

  useEffect(() => {
    if (zone) {
      reset({
        name: zone.name,
        description: zone.description || '',
        type: zone.type,
      });
    } else {
      reset({
        name: '',
        description: '',
        type: 'MIXED',
      });
    }
  }, [zone, reset]);

  const handleFormSubmit = async (data: ZoneFormData) => {
    const payload: ZoneCreate = {
      exhibition_id: exhibitionId,
      name: data.name,
      description: data.description || undefined,
      type: data.type,
    };
    await onSubmit(payload);
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
