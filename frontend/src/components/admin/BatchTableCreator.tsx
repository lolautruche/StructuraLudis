'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { zonesApi, PhysicalTable } from '@/lib/api';
import { Button, Input, Checkbox } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';

const batchSchema = z.object({
  prefix: z.string().max(30).optional(),
  count: z.coerce.number().min(1).max(200),
  starting_number: z.coerce.number().min(1).optional().nullable(),
  capacity: z.coerce.number().min(1).max(20),
  fill_gaps: z.boolean(),
});

type BatchFormData = z.infer<typeof batchSchema>;

interface BatchTableCreatorProps {
  zoneId: string;
  zonePrefix?: string | null; // Issue #93 - Zone-level prefix
  onTablesCreated: (tables: PhysicalTable[]) => void;
  onCancel: () => void;
}

export function BatchTableCreator({
  zoneId,
  zonePrefix,
  onTablesCreated,
  onCancel,
}: BatchTableCreatorProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');
  const { showError } = useToast();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<BatchFormData>({
    resolver: zodResolver(batchSchema),
    defaultValues: {
      prefix: zonePrefix || '',
      count: 10,
      starting_number: null,
      capacity: 6,
      fill_gaps: false,
    },
  });

  const fillGaps = watch('fill_gaps');

  const onSubmit = async (data: BatchFormData) => {
    setError(null);

    const response = await zonesApi.createTablesBatch(zoneId, {
      prefix: data.prefix || undefined,
      count: data.count,
      starting_number: data.starting_number || undefined,
      capacity: data.capacity,
      fill_gaps: data.fill_gaps,
    });

    if (response.error) {
      setError(response.error.message);
      showError(t('tableCreateError'));
    } else if (response.data) {
      onTablesCreated(response.data.tables);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Input
          {...register('prefix')}
          label={t('tablePrefix')}
          placeholder={zonePrefix || 'Table '}
          helperText={zonePrefix ? t('tablePrefixFromZone', { prefix: zonePrefix }) : undefined}
          error={errors.prefix?.message}
        />

        <Input
          {...register('count')}
          type="number"
          min={1}
          max={200}
          label={t('tableCount')}
          error={errors.count?.message}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          {...register('starting_number')}
          type="number"
          min={1}
          label={t('startingNumber')}
          placeholder={t('autoCalculate')}
          helperText={t('startingNumberHelp')}
          error={errors.starting_number?.message}
        />

        <Input
          {...register('capacity')}
          type="number"
          min={1}
          max={20}
          label={t('tableCapacity')}
          error={errors.capacity?.message}
        />
      </div>

      {/* Smart numbering option (Issue #93) */}
      <div className="flex items-start gap-3 py-2">
        <Checkbox
          {...register('fill_gaps')}
          id="fill_gaps"
          className="mt-0.5"
          disabled={fillGaps === undefined}
        />
        <div>
          <label
            htmlFor="fill_gaps"
            className="text-sm font-medium cursor-pointer"
            style={{ color: 'var(--color-text-primary)' }}
          >
            {t('fillGaps')}
          </label>
          <p
            className="text-xs mt-0.5"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            {t('fillGapsHelp')}
          </p>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          {tCommon('cancel')}
        </Button>
        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? t('creating') : t('createTables')}
        </Button>
      </div>
    </form>
  );
}
