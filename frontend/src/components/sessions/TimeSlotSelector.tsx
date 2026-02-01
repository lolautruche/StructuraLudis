'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
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

// Sub-component: Time Slot Card
interface TimeSlotCardProps {
  slot: TimeSlot;
  isSelected: boolean;
  onSelect: () => void;
}

function TimeSlotCard({ slot, isSelected, onSelect }: TimeSlotCardProps) {
  const t = useTranslations('SessionForm');

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

  // Calculate slot duration in hours
  const slotDurationHours = Math.round((endDate.getTime() - startDate.getTime()) / 3600000 * 10) / 10;

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'w-full text-left p-4 rounded-lg border-2 transition-all',
        'hover:border-slate-400 dark:hover:border-slate-500',
        'focus:outline-none focus:ring-2 focus:ring-ludis-primary focus:ring-offset-2 dark:focus:ring-offset-ludis-dark',
        isSelected
          ? 'border-l-4 border-l-ludis-primary border-ludis-primary bg-blue-50/50 dark:bg-blue-900/20'
          : 'border-slate-200 dark:border-slate-700'
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <Badge variant={isSelected ? 'info' : 'secondary'} size="sm">
          {slot.name}
        </Badge>
        <Badge variant="secondary" size="sm">
          {t('maxDuration')}: {slot.max_duration_minutes} {t('minutes')}
        </Badge>
      </div>
      <p className="text-sm text-slate-700 dark:text-slate-300 font-medium">
        {dateStr}
      </p>
      <p className="text-sm text-slate-500 dark:text-slate-400">
        {startTimeStr} - {endTimeStr} ({slotDurationHours}h {t('slotWindow')})
      </p>
    </button>
  );
}

// Sub-component: Time Range Visualizer
interface TimeRangeVisualizerProps {
  slot: TimeSlot;
  scheduledStart: string;
  scheduledEnd: string;
  hasError: boolean;
  hasDurationWarning: boolean;
}

function TimeRangeVisualizer({
  slot,
  scheduledStart,
  scheduledEnd,
  hasError,
  hasDurationWarning
}: TimeRangeVisualizerProps) {
  const t = useTranslations('SessionForm');

  const slotStart = new Date(slot.start_time).getTime();
  const slotEnd = new Date(slot.end_time).getTime();
  const slotDuration = slotEnd - slotStart;

  const start = scheduledStart ? new Date(scheduledStart).getTime() : slotStart;
  const end = scheduledEnd ? new Date(scheduledEnd).getTime() : slotStart;

  // Calculate percentages (clamped to 0-100)
  const startPercent = Math.max(0, Math.min(100, ((start - slotStart) / slotDuration) * 100));
  const endPercent = Math.max(0, Math.min(100, ((end - slotStart) / slotDuration) * 100));
  const rangeWidth = Math.max(0, endPercent - startPercent);

  // Determine bar color
  const barColor = hasError
    ? 'bg-red-500'
    : hasDurationWarning
      ? 'bg-amber-500'
      : 'bg-ludis-primary';

  // Format times for display
  const formatTime = (dateStr: string) => {
    if (!dateStr) return '--:--';
    return new Date(dateStr).toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>{t('slotWindow')}</span>
        <span>{t('selectedRange')}</span>
      </div>

      {/* Visual bar container */}
      <div className="relative h-4 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
        {/* Selected range */}
        {rangeWidth > 0 && (
          <div
            className={cn('absolute h-full transition-all rounded-full', barColor)}
            style={{
              left: `${startPercent}%`,
              width: `${rangeWidth}%`,
            }}
          />
        )}
      </div>

      {/* Time labels */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-500 dark:text-slate-400">
          {formatTime(slot.start_time)}
        </span>
        <span className={cn(
          'font-medium',
          hasError ? 'text-red-500' : hasDurationWarning ? 'text-amber-500' : 'text-ludis-primary'
        )}>
          {formatTime(scheduledStart)} - {formatTime(scheduledEnd)}
        </span>
        <span className="text-slate-500 dark:text-slate-400">
          {formatTime(slot.end_time)}
        </span>
      </div>
    </div>
  );
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

  // Calculate duration in minutes
  const durationMinutes = useMemo(() => {
    if (!scheduledStart || !scheduledEnd) return 0;
    const start = new Date(scheduledStart);
    const end = new Date(scheduledEnd);
    return Math.round((end.getTime() - start.getTime()) / 60000);
  }, [scheduledStart, scheduledEnd]);

  // Validation states
  const validationState = useMemo(() => {
    if (!selectedSlot || !scheduledStart || !scheduledEnd) {
      return { hasError: false, hasDurationWarning: false, errors: [] };
    }

    const start = new Date(scheduledStart);
    const end = new Date(scheduledEnd);
    const slotStart = new Date(selectedSlot.start_time);
    const slotEnd = new Date(selectedSlot.end_time);
    const duration = (end.getTime() - start.getTime()) / 60000;

    const errors: string[] = [];
    let hasError = false;
    let hasDurationWarning = false;

    // Check time boundaries
    if (start < slotStart) {
      hasError = true;
    }
    if (end > slotEnd) {
      hasError = true;
    }

    // Check duration
    if (duration > selectedSlot.max_duration_minutes) {
      hasDurationWarning = true;
    }
    if (duration < 30 && duration > 0) {
      hasDurationWarning = true;
    }

    return { hasError, hasDurationWarning, errors };
  }, [selectedSlot, scheduledStart, scheduledEnd]);

  // Convert datetime-local to ISO string and vice versa
  const toDatetimeLocal = (isoString: string) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const fromDatetimeLocal = (localString: string) => {
    if (!localString) return '';
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

  // Empty state
  if (timeSlots.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-slate-500 dark:text-slate-400">{t('noSlotsAvailable')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Slot Cards Grid */}
      <div>
        <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-3">
          {t('availableSlots')}
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {timeSlots.map((slot) => (
            <TimeSlotCard
              key={slot.id}
              slot={slot}
              isSelected={slot.id === selectedSlotId}
              onSelect={() => handleSlotChange(slot.id)}
            />
          ))}
        </div>
        {slotError && (
          <p className="mt-2 text-sm text-red-500">{slotError}</p>
        )}
      </div>

      {/* Selected slot details with time inputs */}
      {selectedSlot && (
        <div className={cn(
          'p-4 rounded-lg border-2 space-y-4',
          validationState.hasError || startError || endError
            ? 'border-red-300 dark:border-red-700 bg-red-50/50 dark:bg-red-900/10'
            : 'border-ludis-primary/30 bg-blue-50/30 dark:bg-blue-900/10'
        )}>
          {/* Visual time range */}
          <TimeRangeVisualizer
            slot={selectedSlot}
            scheduledStart={scheduledStart}
            scheduledEnd={scheduledEnd}
            hasError={validationState.hasError || !!startError || !!endError}
            hasDurationWarning={validationState.hasDurationWarning}
          />

          {/* Time inputs */}
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

          {/* Duration display with validation status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {t('duration')}:
              </span>
              <Badge
                variant={
                  validationState.hasError || startError || endError
                    ? 'danger'
                    : validationState.hasDurationWarning
                      ? 'warning'
                      : 'success'
                }
                size="sm"
              >
                {durationMinutes} {t('minutes')}
              </Badge>
            </div>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {t('maxDuration')}: {selectedSlot.max_duration_minutes} {t('minutes')}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
