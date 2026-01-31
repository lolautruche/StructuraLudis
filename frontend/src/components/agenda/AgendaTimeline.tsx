'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Button } from '@/components/ui';
import { AgendaSessionCard } from './AgendaSessionCard';
import { AgendaBookingCard } from './AgendaBookingCard';
import { ConflictWarning } from './ConflictWarning';
import { formatDate } from '@/lib/utils';
import type { UserAgenda } from '@/lib/api/types';

interface AgendaTimelineProps {
  agenda: UserAgenda;
  locale?: string;
  onCheckIn: (bookingId: string) => Promise<void>;
  onCancelBooking?: (bookingId: string) => Promise<void>;
}

interface TimelineItem {
  type: 'session' | 'booking';
  scheduledStart: string;
  data: UserAgenda['my_sessions'][0] | UserAgenda['my_bookings'][0];
}

export function AgendaTimeline({
  agenda,
  locale = 'fr',
  onCheckIn,
  onCancelBooking,
}: AgendaTimelineProps) {
  const t = useTranslations('Agenda');

  // Combine and sort all items by scheduled_start
  const timelineItems = useMemo(() => {
    const items: TimelineItem[] = [
      ...agenda.my_sessions.map((s) => ({
        type: 'session' as const,
        scheduledStart: s.scheduled_start,
        data: s,
      })),
      ...agenda.my_bookings.map((b) => ({
        type: 'booking' as const,
        scheduledStart: b.scheduled_start,
        data: b,
      })),
    ];

    return items.sort(
      (a, b) =>
        new Date(a.scheduledStart).getTime() - new Date(b.scheduledStart).getTime()
    );
  }, [agenda]);

  // Group items by date
  const groupedByDate = useMemo(() => {
    const groups: Record<string, TimelineItem[]> = {};

    timelineItems.forEach((item) => {
      const dateKey = formatDate(item.scheduledStart, locale);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(item);
    });

    return groups;
  }, [timelineItems, locale]);

  const isEmpty = timelineItems.length === 0;

  if (isEmpty) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📅</div>
        <h3 className="text-lg font-medium text-white mb-2">
          {t('noSessions')}
        </h3>
        <p className="text-slate-400 mb-6 max-w-md mx-auto">
          {t('noSessionsDescription')}
        </p>
        <Link href="/exhibitions">
          <Button variant="primary">{t('findSessions')}</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Conflict warning */}
      {agenda.conflicts.length > 0 && (
        <ConflictWarning conflicts={agenda.conflicts} />
      )}

      {/* Timeline grouped by date */}
      {Object.entries(groupedByDate).map(([date, items]) => (
        <div key={date} className="space-y-4">
          {/* Date header */}
          <div className="sticky top-0 bg-ludis-dark/95 backdrop-blur py-2 z-10">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <span>📅</span>
              {date}
            </h3>
          </div>

          {/* Items for this date */}
          <div className="space-y-3 pl-4 border-l-2 border-slate-700">
            {items.map((item) => (
              <div key={`${item.type}-${item.data.id}`}>
                {item.type === 'session' ? (
                  <AgendaSessionCard
                    session={item.data as UserAgenda['my_sessions'][0]}
                    locale={locale}
                  />
                ) : (
                  <AgendaBookingCard
                    booking={item.data as UserAgenda['my_bookings'][0]}
                    locale={locale}
                    onCheckIn={onCheckIn}
                    onCancel={onCancelBooking}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
