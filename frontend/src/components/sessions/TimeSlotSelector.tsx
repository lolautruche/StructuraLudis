'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Select, Input } from '@/components/ui';
import type { TimeSlot } from '@/lib/api/types';

interface TimeSlotSelectorProps {
  timeSlots: TimeSlot[];
  selectedSlotId: string | null;
  scheduledStart: string;
  scheduledEnd: string;
  onSlotChange: (slotId: string) => void;
  onStartChange: (start: string) => void;
  onEndChange: (end: string) => void;
  slotError?: string;
  startError?: string;
  endError?: string;
}

export function TimeSlotSelector({
  timeSlots,
  selectedSlotId,
  scheduledStart,
  scheduledEnd,
  onSlotChange,
  onStartChange,
  onEndChange,
  slotError,
  startError,
  endError,
}: TimeSlotSelectorProps) {
  const t = useTranslations('SessionForm');

  // Get selected slot
  const selectedSlot = useMemo(() => {
    return timeSlots.find((slot) => slot.id === selectedSlotId);
  }, [timeSlots, selectedSlotId]);

  // Format time for display
  const formatSlotTime = (slot: TimeSlot) => {
    const startDate = new Date(slot.start_time);
    const endDate = new Date(slot.end_time);

    const dateStr = startDate.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
    const startTimeStr = startDate.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });
    const endTimeStr = endDate.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });

    return `${slot.name} - ${dateStr} ${startTimeStr} - ${endTimeStr}`;
  };

  // Calculate duration in minutes
  const calculateDuration = useMemo(() => {
    if (!scheduledStart || !scheduledEnd) return 0;
    const start = new Date(scheduledStart);
    const end = new Date(scheduledEnd);
    return Math.round((end.getTime() - start.getTime()) / 60000);
  }, [scheduledStart, scheduledEnd]);

  // Duration validation message
  const durationWarning = useMemo(() => {
    if (!selectedSlot || !calculateDuration) return null;
    if (calculateDuration > selectedSlot.max_duration_minutes) {
      return t('durationExceedsMax', { max: selectedSlot.max_duration_minutes });
    }
    if (calculateDuration < 30) {
      return t('durationTooShort');
    }
    return null;
  }, [selectedSlot, calculateDuration, t]);

  // Convert datetime-local to ISO string and vice versa
  const toDatetimeLocal = (isoString: string) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    // Format for datetime-local input: YYYY-MM-DDTHH:mm
    return date.toISOString().slice(0, 16);
  };

  const fromDatetimeLocal = (localString: string) => {
    if (!localString) return '';
    // datetime-local format: YYYY-MM-DDTHH:mm
    return new Date(localString).toISOString();
  };

  // Set default times when slot changes
  const handleSlotChange = (slotId: string) => {
    onSlotChange(slotId);
    const slot = timeSlots.find((s) => s.id === slotId);
    if (slot) {
      onStartChange(slot.start_time);
      // Default end time: start + 2 hours (or max duration if less)
      const startDate = new Date(slot.start_time);
      const defaultDuration = Math.min(120, slot.max_duration_minutes);
      const endDate = new Date(startDate.getTime() + defaultDuration * 60000);
      onEndChange(endDate.toISOString());
    }
  };

  return (
    <div className="space-y-4">
      {/* Time slot selection */}
      <Select
        label={t('timeSlot')}
        value={selectedSlotId || ''}
        onChange={(e) => handleSlotChange(e.target.value)}
        options={timeSlots.map((slot) => ({
          value: slot.id,
          label: formatSlotTime(slot),
        }))}
        placeholder={t('selectTimeSlot')}
        error={slotError}
      />

      {/* Start and end time (only show when slot is selected) */}
      {selectedSlot && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label={t('startTime')}
              type="datetime-local"
              value={toDatetimeLocal(scheduledStart)}
              onChange={(e) => onStartChange(fromDatetimeLocal(e.target.value))}
              min={toDatetimeLocal(selectedSlot.start_time)}
              max={toDatetimeLocal(selectedSlot.end_time)}
              error={startError}
            />
            <Input
              label={t('endTime')}
              type="datetime-local"
              value={toDatetimeLocal(scheduledEnd)}
              onChange={(e) => onEndChange(fromDatetimeLocal(e.target.value))}
              min={toDatetimeLocal(scheduledStart || selectedSlot.start_time)}
              max={toDatetimeLocal(selectedSlot.end_time)}
              error={endError}
            />
          </div>

          {/* Duration display */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600 dark:text-slate-400">
              {t('duration')}: {calculateDuration} {t('minutes')}
            </span>
            <span className="text-slate-600 dark:text-slate-400">
              {t('maxDuration')}: {selectedSlot.max_duration_minutes} {t('minutes')}
            </span>
          </div>

          {/* Duration warning */}
          {durationWarning && (
            <p className="text-sm text-yellow-500">{durationWarning}</p>
          )}
        </>
      )}
    </div>
  );
}
