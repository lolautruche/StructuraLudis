'use client';

import { useTranslations } from 'next-intl';
import { Card, Badge } from '@/components/ui';
import { AvailabilityBadge } from './AvailabilityBadge';
import { SafetyToolsBadges } from './SafetyToolsBadges';
import { BookingButton } from './BookingButton';
import { formatDate, formatTime } from '@/lib/utils';
import type { GameSession, Booking } from '@/lib/api/types';

interface SessionDetailProps {
  session: GameSession;
  locale?: string;
  userBooking?: Booking | null;
  isAuthenticated?: boolean;
  onBook?: () => Promise<void>;
  onJoinWaitlist?: () => Promise<void>;
  onCancelBooking?: () => Promise<void>;
  onCheckIn?: () => Promise<void>;
  isLoading?: boolean;
}

export function SessionDetail({
  session,
  locale = 'fr',
  userBooking,
  isAuthenticated = false,
  onBook,
  onJoinWaitlist,
  onCancelBooking,
  onCheckIn,
  isLoading = false,
}: SessionDetailProps) {
  const t = useTranslations('Session');
  const tTable = useTranslations('GameTable');

  const startDate = formatDate(session.scheduled_start, locale);
  const startTime = formatTime(session.scheduled_start, locale);
  const endTime = formatTime(session.scheduled_end, locale);

  const availableSeats = session.max_players_count - session.confirmed_players_count;
  const isFull = availableSeats <= 0;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <Card.Content className="space-y-4">
          {/* Title and Status */}
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="space-y-2">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{session.title}</h1>
              {session.game_title && (
                <div className="flex items-center gap-2 text-lg text-slate-700 dark:text-slate-300">
                  <span>🎲</span>
                  <span>{session.game_title}</span>
                </div>
              )}
            </div>
            <AvailabilityBadge
              status={session.status}
              availableSeats={availableSeats}
              totalSeats={session.max_players_count}
              waitlistCount={session.waitlist_count}
            />
          </div>

          {/* Description */}
          {session.description && (
            <p className="text-slate-600 dark:text-slate-400">{session.description}</p>
          )}

          {/* Booking Button */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
            <BookingButton
              session={session}
              userBooking={userBooking}
              isAuthenticated={isAuthenticated}
              onBook={onBook}
              onJoinWaitlist={onJoinWaitlist}
              onCancelBooking={onCancelBooking}
              onCheckIn={onCheckIn}
              isLoading={isLoading}
            />
          </div>
        </Card.Content>
      </Card>

      {/* Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Schedule & Location */}
        <Card>
          <Card.Header>
            <Card.Title>{t('schedule')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-xl">📅</span>
              <div>
                <p className="text-slate-900 dark:text-white font-medium">{startDate}</p>
                <p className="text-slate-600 dark:text-slate-400 text-sm">
                  {t('from')} {startTime} {t('to')} {endTime}
                </p>
              </div>
            </div>

            {(session.zone_name || session.table_label) && (
              <div className="flex items-center gap-3">
                <span className="text-xl">📍</span>
                <div>
                  {session.zone_name && (
                    <p className="text-slate-900 dark:text-white font-medium">
                      {t('zone')}: {session.zone_name}
                    </p>
                  )}
                  {session.table_label && (
                    <p className="text-slate-600 dark:text-slate-400 text-sm">
                      {t('table')}: {session.table_label}
                    </p>
                  )}
                </div>
              </div>
            )}
          </Card.Content>
        </Card>

        {/* Players & GM */}
        <Card>
          <Card.Header>
            <Card.Title>{t('players')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            {/* GM */}
            {session.gm_name && (
              <div className="flex items-center gap-3">
                <span className="text-xl">👤</span>
                <div>
                  <p className="text-slate-600 dark:text-slate-400 text-sm">{tTable('gm')}</p>
                  <p className="text-slate-900 dark:text-white font-medium">{session.gm_name}</p>
                </div>
              </div>
            )}

            {/* Organized by */}
            {session.provided_by_group_name && (
              <div className="flex items-center gap-3">
                <span className="text-xl">🏢</span>
                <div>
                  <p className="text-slate-900 dark:text-white font-medium">
                    {tTable('organizedBy', { name: session.provided_by_group_name })}
                  </p>
                </div>
              </div>
            )}

            {/* Seats info */}
            <div className="flex items-center gap-3">
              <span className="text-xl">🎯</span>
              <div>
                {isFull ? (
                  <p className="text-red-600 dark:text-red-400 font-medium">{t('full')}</p>
                ) : (
                  <p className="text-emerald-600 dark:text-emerald-400 font-medium">
                    {t('spotsLeft', { count: availableSeats })}
                  </p>
                )}
                <p className="text-slate-600 dark:text-slate-400 text-sm">
                  {session.confirmed_players_count}/{session.max_players_count} {t('players').toLowerCase()}
                </p>
              </div>
            </div>

            {/* Waitlist info */}
            {session.waitlist_count > 0 && (
              <div className="text-amber-600 dark:text-amber-400 text-sm">
                {t('waitlistInfo', { count: session.waitlist_count })}
              </div>
            )}
          </Card.Content>
        </Card>
      </div>

      {/* Additional Info */}
      <Card>
        <Card.Header>
          <Card.Title>{t('details')}</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="flex flex-wrap gap-3">
            {/* Language */}
            <Badge variant="default" size="md">
              {tTable('language')}: {session.language.toUpperCase()}
            </Badge>

            {/* Min age */}
            {session.min_age > 0 && (
              <Badge variant="warning" size="md">
                {tTable('minAge', { age: session.min_age })}
              </Badge>
            )}

            {/* Accessibility */}
            {session.is_accessible_disability && (
              <Badge variant="info" size="md">
                ♿ {t('accessibleSession')}
              </Badge>
            )}
          </div>

          {/* Safety tools */}
          {session.safety_tools && session.safety_tools.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
              <p className="text-slate-600 dark:text-slate-400 text-sm mb-2">{tTable('safetyTools')}</p>
              <SafetyToolsBadges tools={session.safety_tools} />
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
