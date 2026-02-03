'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import { TimeSlot, TimeSlotCreate } from '@/lib/api';
import { Button, Input } from '@/components/ui';

const timeSlotSchema = z.object({
  name: z.string().min(1).max(100),
  start_time: z.string().min(1),
  end_time: z.string().min(1),
  max_duration_minutes: z.coerce.number().min(30).max(720),
  buffer_time_minutes: z.coerce.number().min(0).max(60),
});

type TimeSlotFormData = z.infer<typeof timeSlotSchema>;

interface TimeSlotFormProps {
  slot?: TimeSlot | null;
  onSubmit: (data: TimeSlotCreate) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  /** Exhibition start date for defaults and constraints */
  exhibitionStartDate?: string;
  /** Exhibition end date for constraints */
  exhibitionEndDate?: string;
}

function formatDateTimeLocal(isoString: string): string {
  const date = new Date(isoString);
  return date.toISOString().slice(0, 16);
}

export function TimeSlotForm({
  slot,
  onSubmit,
  onCancel,
  isSubmitting,
  exhibitionStartDate,
  exhibitionEndDate,
}: TimeSlotFormProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');

  // Format exhibition dates for datetime-local inputs (min/max constraints)
  const minDateTime = exhibitionStartDate ? formatDateTimeLocal(exhibitionStartDate) : undefined;
  const maxDateTime = exhibitionEndDate ? formatDateTimeLocal(exhibitionEndDate) : undefined;

  // Default start time: exhibition start date at 09:00
  const defaultStartTime = exhibitionStartDate
    ? formatDateTimeLocal(new Date(new Date(exhibitionStartDate).setHours(9, 0, 0, 0)).toISOString())
    : '';
  // Default end time: exhibition start date at 13:00
  const defaultEndTime = exhibitionStartDate
    ? formatDateTimeLocal(new Date(new Date(exhibitionStartDate).setHours(13, 0, 0, 0)).toISOString())
    : '';

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TimeSlotFormData>({
    resolver: zodResolver(timeSlotSchema),
    defaultValues: {
      name: '',
      start_time: defaultStartTime,
      end_time: defaultEndTime,
      max_duration_minutes: 240,
      buffer_time_minutes: 15,
    },
  });

  useEffect(() => {
    if (slot) {
      reset({
        name: slot.name,
        start_time: formatDateTimeLocal(slot.start_time),
        end_time: formatDateTimeLocal(slot.end_time),
        max_duration_minutes: slot.max_duration_minutes,
        buffer_time_minutes: slot.buffer_time_minutes,
      });
    } else {
      reset({
        name: '',
        start_time: defaultStartTime,
        end_time: defaultEndTime,
        max_duration_minutes: 240,
        buffer_time_minutes: 15,
      });
    }
  }, [slot, reset, defaultStartTime, defaultEndTime]);

  const handleFormSubmit = async (data: TimeSlotFormData) => {
    const payload = {
      name: data.name,
      start_time: new Date(data.start_time).toISOString(),
      end_time: new Date(data.end_time).toISOString(),
      max_duration_minutes: data.max_duration_minutes,
      buffer_time_minutes: data.buffer_time_minutes,
    };
    await onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Input
        {...register('name')}
        label={t('slotName')}
        placeholder={t('slotNamePlaceholder')}
        error={errors.name?.message}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          {...register('start_time')}
          type="datetime-local"
          label={t('startTime')}
          min={minDateTime}
          max={maxDateTime}
          error={errors.start_time?.message}
        />

        <Input
          {...register('end_time')}
          type="datetime-local"
          label={t('endTime')}
          min={minDateTime}
          max={maxDateTime}
          error={errors.end_time?.message}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          {...register('max_duration_minutes')}
          type="number"
          min={30}
          max={720}
          label={t('maxDuration')}
          helperText={t('maxDurationHelper')}
          error={errors.max_duration_minutes?.message}
        />

        <Input
          {...register('buffer_time_minutes')}
          type="number"
          min={0}
          max={60}
          label={t('bufferTime')}
          helperText={t('bufferTimeHelper')}
          error={errors.buffer_time_minutes?.message}
        />
      </div>

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
