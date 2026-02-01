'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { zonesApi, PhysicalTable } from '@/lib/api';
import { Button, Input } from '@/components/ui';

const batchSchema = z.object({
  prefix: z.string().max(30),
  count: z.coerce.number().min(1).max(200),
  starting_number: z.coerce.number().min(1),
  capacity: z.coerce.number().min(1).max(20),
});

type BatchFormData = z.infer<typeof batchSchema>;

interface BatchTableCreatorProps {
  zoneId: string;
  onTablesCreated: (tables: PhysicalTable[]) => void;
  onCancel: () => void;
}

export function BatchTableCreator({
  zoneId,
  onTablesCreated,
  onCancel,
}: BatchTableCreatorProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<BatchFormData>({
    resolver: zodResolver(batchSchema),
    defaultValues: {
      prefix: 'Table ',
      count: 10,
      starting_number: 1,
      capacity: 6,
    },
  });

  const onSubmit = async (data: BatchFormData) => {
    setError(null);

    const response = await zonesApi.createTablesBatch(zoneId, {
      prefix: data.prefix,
      count: data.count,
      starting_number: data.starting_number,
      capacity: data.capacity,
    });

    if (response.error) {
      setError(response.error.message);
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
          placeholder="Table "
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
