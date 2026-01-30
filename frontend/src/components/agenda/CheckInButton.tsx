'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui';
import type { BookingStatus } from '@/lib/api/types';

interface CheckInButtonProps {
  bookingId: string;
  status: BookingStatus;
  scheduledStart: string;
  onCheckIn: (bookingId: string) => Promise<void>;
  gracePeriodMinutes?: number;
}

export function CheckInButton({
  bookingId,
  status,
  scheduledStart,
  onCheckIn,
  gracePeriodMinutes = 15,
}: CheckInButtonProps) {
  const t = useTranslations('Agenda');
  const [isLoading, setIsLoading] = useState(false);

  const now = new Date();
  const startTime = new Date(scheduledStart);
  const checkInWindowStart = new Date(startTime.getTime() - gracePeriodMinutes * 60 * 1000);
  const minutesUntilCheckIn = Math.ceil((checkInWindowStart.getTime() - now.getTime()) / 60000);

  const canCheckIn = status === 'CONFIRMED' && now >= checkInWindowStart && now <= startTime;
  const isCheckedIn = status === 'CHECKED_IN';
  const showCountdown = status === 'CONFIRMED' && minutesUntilCheckIn > 0 && minutesUntilCheckIn <= 60;

  const handleCheckIn = async () => {
    setIsLoading(true);
    try {
      await onCheckIn(bookingId);
    } finally {
      setIsLoading(false);
    }
  };

  if (isCheckedIn) {
    return (
      <span className="inline-flex items-center gap-1 text-sm text-emerald-400">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
        {t('checkedIn')}
      </span>
    );
  }

  if (showCountdown) {
    return (
      <span className="text-sm text-slate-400">
        {t('checkInCountdown', { minutes: minutesUntilCheckIn })}
      </span>
    );
  }

  if (canCheckIn) {
    return (
      <Button
        variant="success"
        size="sm"
        onClick={handleCheckIn}
        isLoading={isLoading}
      >
        {t('checkInAvailable')}
      </Button>
    );
  }

  return null;
}
