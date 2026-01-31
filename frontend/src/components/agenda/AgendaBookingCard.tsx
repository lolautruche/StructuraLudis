'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Badge, Button } from '@/components/ui';
import { CheckInButton } from './CheckInButton';
import { formatTime } from '@/lib/utils';
import type { MyBookingSummary } from '@/lib/api/types';

interface AgendaBookingCardProps {
  booking: MyBookingSummary;
  locale?: string;
  onCheckIn: (bookingId: string) => Promise<void>;
  onCancel?: (bookingId: string) => Promise<void>;
}

export function AgendaBookingCard({
  booking,
  locale = 'fr',
  onCheckIn,
  onCancel,
}: AgendaBookingCardProps) {
  const t = useTranslations('Agenda');
  const tSession = useTranslations('Session');

  const startTime = formatTime(booking.scheduled_start, locale);
  const endTime = formatTime(booking.scheduled_end, locale);

  const getStatusBadge = () => {
    switch (booking.status) {
      case 'CONFIRMED':
        return <Badge variant="success" size="sm">{t('confirmed')}</Badge>;
      case 'CHECKED_IN':
        return <Badge variant="info" size="sm">{t('checkedIn')}</Badge>;
      case 'WAITING_LIST':
        return <Badge variant="warning" size="sm">{t('waitlisted')}</Badge>;
      default:
        return null;
    }
  };

  return (
    <Card className="border-l-4 border-l-emerald-500">
      <Card.Content className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="success" size="sm">{t('asPlayer')}</Badge>
            {getStatusBadge()}
          </div>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-slate-900 dark:text-white">{booking.session_title}</h3>

        {/* Time & Location */}
        <div className="flex flex-col gap-1 text-sm text-slate-600 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <span>⏰</span>
            <span>{startTime} - {endTime}</span>
          </div>
          {(booking.zone_name || booking.table_label) && (
            <div className="flex items-center gap-2">
              <span>📍</span>
              <span>
                {[booking.zone_name, booking.table_label].filter(Boolean).join(' - ')}
              </span>
            </div>
          )}
        </div>

        {/* GM */}
        {booking.gm_name && (
          <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
            <span>👤</span>
            <span>MJ: {booking.gm_name}</span>
          </div>
        )}

        {/* Players & Availability */}
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            <span>👥</span>
            <span className="text-slate-700 dark:text-slate-300">
              {booking.confirmed_players}/{booking.max_players_count}
            </span>
          </div>
          {booking.confirmed_players < booking.max_players_count ? (
            <span className="text-emerald-600 dark:text-emerald-400">
              {tSession('spotsLeft', { count: booking.max_players_count - booking.confirmed_players })}
            </span>
          ) : (
            <span className="text-red-600 dark:text-red-400">{tSession('full')}</span>
          )}
          {booking.waitlist_count > 0 && (
            <span className="text-amber-600 dark:text-amber-400">
              (+{booking.waitlist_count} {t('waitlisted').toLowerCase()})
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-700">
          <Link href={`/sessions/${booking.game_session_id}`}>
            <Button variant="ghost" size="sm">
              {t('viewDetails')}
            </Button>
          </Link>

          {/* Check-in button */}
          {(booking.status === 'CONFIRMED' || booking.status === 'CHECKED_IN') && (
            <CheckInButton
              bookingId={booking.id}
              status={booking.status}
              scheduledStart={booking.scheduled_start}
              onCheckIn={onCheckIn}
            />
          )}

          {/* Cancel button */}
          {booking.status !== 'CHECKED_IN' && onCancel && (
            <Button
              variant="ghost"
              size="sm"
              className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
              onClick={() => onCancel(booking.id)}
            >
              {tSession('cancelBooking')}
            </Button>
          )}
        </div>
      </Card.Content>
    </Card>
  );
}
