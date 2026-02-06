'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Badge, Button } from '@/components/ui';
import { AvailabilityBadge } from './AvailabilityBadge';
import { SafetyToolsBadges } from './SafetyToolsBadges';
import { BookingButton } from './BookingButton';
import { ProviderBadge } from '@/components/games/ProviderBadge';
import { formatDate, formatTime } from '@/lib/utils';
import type { GameSession, Booking, Exhibition, GlobalRole } from '@/lib/api/types';

interface SessionDetailProps {
  session: GameSession;
  locale?: string;
  userBooking?: Booking | null;
  isAuthenticated?: boolean;
  onBook?: () => Promise<void>;
  onJoinWaitlist?: () => Promise<void>;
  onCancelBooking?: () => Promise<void>;
  onCheckIn?: () => Promise<void>;
  onStartSession?: () => Promise<void>;
  isLoading?: boolean;
  isStarting?: boolean;
  /** Exhibition data for registration check (Issue #77) */
  exhibition?: Exhibition | null;
  /** Current user's ID to check if they are the GM */
  currentUserId?: string | null;
  /** Current user's global role for admin access */
  currentUserRole?: GlobalRole | null;
  /** List of bookings for this session (for GMs/organizers) */
  bookings?: Booking[];
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
  onStartSession,
  isLoading = false,
  isStarting = false,
  exhibition,
  currentUserId,
  currentUserRole,
  bookings = [],
}: SessionDetailProps) {
  const t = useTranslations('Session');
  const tTable = useTranslations('GameTable');
  const tCommon = useTranslations('Common');

  const startDate = formatDate(session.scheduled_start, locale);
  const startTime = formatTime(session.scheduled_start, locale);
  const endTime = formatTime(session.scheduled_end, locale);

  const availableSeats = session.max_players_count - session.confirmed_players_count;
  const isFull = availableSeats <= 0;

  // Check if current user is the GM
  const isGM = currentUserId && session.created_by_user_id === currentUserId;

  // Check if user can manage this session
  const isAdmin = currentUserRole === 'SUPER_ADMIN' || currentUserRole === 'ADMIN';
  const canManageExhibition = exhibition?.can_manage ?? false;
  const canManageSession = isGM || isAdmin || canManageExhibition;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <Card.Content className="space-y-4">
          {/* Title and Status */}
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{session.title}</h1>
                {isGM && (
                  <Badge variant="info" size="sm">{t('youAreGM')}</Badge>
                )}
              </div>
              {session.game_title && (
                <div className="flex items-center gap-3 text-lg text-slate-700 dark:text-slate-300">
                  {session.game_cover_image_url && (
                    <img
                      src={session.game_cover_image_url}
                      alt={session.game_title}
                      className="w-12 h-16 object-cover rounded flex-shrink-0"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <span>🎲</span>
                      <span>{session.game_title}</span>
                      {session.game_external_provider && (
                        <ProviderBadge provider={session.game_external_provider} />
                      )}
                    </div>
                    {session.game_themes && session.game_themes.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {session.game_themes.map((theme) => (
                          <span
                            key={theme}
                            className="inline-block px-1.5 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                          >
                            {theme}
                          </span>
                        ))}
                      </div>
                    )}
                    {session.game_external_url && (
                      <a
                        href={session.game_external_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-1 text-sm text-ludis-primary hover:underline"
                      >
                        {t('viewGameReference')}
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <AvailabilityBadge
                status={session.status}
                availableSeats={availableSeats}
                totalSeats={session.max_players_count}
                waitlistCount={session.waitlist_count}
              />
              {/* Start Session button - only for GM when session is VALIDATED */}
              {isGM && session.status === 'VALIDATED' && onStartSession && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onStartSession}
                  disabled={isStarting}
                >
                  {isStarting ? t('starting') : t('startSession')}
                </Button>
              )}
              {canManageSession && (
                <Link href={`/sessions/${session.id}/edit`}>
                  <Button variant="secondary" size="sm">
                    {tCommon('edit')}
                  </Button>
                </Link>
              )}
            </div>
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
              exhibition={exhibition}
              currentUserId={currentUserId}
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

      {/* Participant List (for GMs/organizers) */}
      {canManageSession && bookings.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>{t('registeredPlayers')}</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="space-y-2">
              {/* Confirmed players */}
              {bookings.filter(b => b.status === 'CONFIRMED' || b.status === 'CHECKED_IN').length > 0 && (
                <div className="space-y-2">
                  {bookings
                    .filter(b => b.status === 'CONFIRMED' || b.status === 'CHECKED_IN')
                    .map((booking) => (
                      <div
                        key={booking.id}
                        className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-lg">
                            {booking.status === 'CHECKED_IN' ? '✅' : '👤'}
                          </span>
                          <div>
                            <p className="font-medium text-slate-900 dark:text-white">
                              {booking.user_name || t('anonymousPlayer')}
                            </p>
                            {booking.user_email && (
                              <p className="text-sm text-slate-500 dark:text-slate-400">
                                {booking.user_email}
                              </p>
                            )}
                          </div>
                        </div>
                        <Badge
                          variant={booking.status === 'CHECKED_IN' ? 'success' : 'default'}
                          size="sm"
                        >
                          {booking.status === 'CHECKED_IN' ? t('checkedIn') : t('confirmed')}
                        </Badge>
                      </div>
                    ))}
                </div>
              )}

              {/* Waitlist */}
              {bookings.filter(b => b.status === 'WAITING_LIST').length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">
                    {t('waitlist')}
                  </p>
                  {bookings
                    .filter(b => b.status === 'WAITING_LIST')
                    .map((booking, index) => (
                      <div
                        key={booking.id}
                        className="flex items-center justify-between p-2 rounded-lg bg-amber-50 dark:bg-amber-900/20"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-lg text-amber-600 dark:text-amber-400 font-bold">
                            #{index + 1}
                          </span>
                          <p className="font-medium text-slate-900 dark:text-white">
                            {booking.user_name || t('anonymousPlayer')}
                          </p>
                        </div>
                        <Badge variant="warning" size="sm">
                          {t('onWaitlist')}
                        </Badge>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </Card.Content>
        </Card>
      )}

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
