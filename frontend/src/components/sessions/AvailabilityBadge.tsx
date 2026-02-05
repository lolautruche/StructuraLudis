'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui';
import type { SessionStatus } from '@/lib/api/types';

interface AvailabilityBadgeProps {
  status: SessionStatus;
  availableSeats: number;
  totalSeats: number;
  waitlistCount?: number;
}

export function AvailabilityBadge({
  status,
  availableSeats,
  totalSeats,
  waitlistCount = 0,
}: AvailabilityBadgeProps) {
  const t = useTranslations('Session');

  // Handle non-bookable statuses
  if (status === 'CANCELLED') {
    return <Badge variant="danger">{t('cancelled')}</Badge>;
  }

  if (status === 'FINISHED') {
    return <Badge variant="secondary">{t('finished')}</Badge>;
  }

  if (status === 'IN_PROGRESS') {
    return <Badge variant="info">{t('inProgress')}</Badge>;
  }

  // Bookable statuses (VALIDATED)
  if (availableSeats > 0) {
    return (
      <Badge variant="success">
        {t('seats', { available: availableSeats, total: totalSeats })}
      </Badge>
    );
  }

  // Full but has waitlist
  if (waitlistCount > 0) {
    return (
      <Badge
        variant="warning"
        title={`${t('full')} - ${t('waitlistInfo', { count: waitlistCount })}`}
      >
        {t('full')} +{waitlistCount}
      </Badge>
    );
  }

  // Full, no waitlist info
  return (
    <Badge variant="warning">
      {t('full')}
    </Badge>
  );
}
