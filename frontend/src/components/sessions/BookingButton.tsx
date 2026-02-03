'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui';
import { Link } from '@/i18n/routing';
import type { GameSession, Booking, Exhibition } from '@/lib/api/types';

interface BookingButtonProps {
  session: GameSession;
  userBooking?: Booking | null;
  isAuthenticated?: boolean;
  onBook?: () => Promise<void>;
  onJoinWaitlist?: () => Promise<void>;
  onCancelBooking?: () => Promise<void>;
  onCheckIn?: () => Promise<void>;
  isLoading?: boolean;
  /** Exhibition data for registration check (Issue #77) */
  exhibition?: Exhibition | null;
}

export function BookingButton({
  session,
  userBooking,
  isAuthenticated = false,
  onBook,
  onJoinWaitlist,
  onCancelBooking,
  onCheckIn,
  isLoading = false,
  exhibition,
}: BookingButtonProps) {
  const t = useTranslations('Session');
  const tExhibition = useTranslations('Exhibition');

  const availableSeats = session.max_players_count - session.confirmed_players_count;
  const isFull = availableSeats <= 0;
  const canBook = session.status === 'VALIDATED' && session.has_available_seats;
  const canJoinWaitlist = session.status === 'VALIDATED' && isFull;

  // Check if registration is required but user is not registered (Issue #77)
  const requiresRegistration = exhibition?.requires_registration ?? false;
  const isUserRegistered = exhibition?.is_user_registered ?? false;
  const needsRegistration = requiresRegistration && !isUserRegistered;

  // Check if check-in is available (30 minutes before start until session starts)
  const now = new Date();
  const sessionStart = new Date(session.scheduled_start);
  const checkInWindowStart = new Date(sessionStart.getTime() - 30 * 60 * 1000);
  const isInCheckInWindow = now >= checkInWindowStart && now < sessionStart;
  const canCheckIn = userBooking?.status === 'CONFIRMED' && isInCheckInWindow;

  // Session not bookable (finished, cancelled, in progress, etc.)
  if (!['VALIDATED'].includes(session.status)) {
    return (
      <Button variant="secondary" disabled className="w-full sm:w-auto">
        {session.status === 'IN_PROGRESS' && t('inProgress')}
        {session.status === 'FINISHED' && t('finished')}
        {session.status === 'CANCELLED' && t('cancelled')}
        {!['IN_PROGRESS', 'FINISHED', 'CANCELLED'].includes(session.status) && t('cancelled')}
      </Button>
    );
  }

  // Not authenticated - show login prompt
  if (!isAuthenticated) {
    return (
      <Link href="/auth/login">
        <Button variant="primary" className="w-full sm:w-auto">
          {t('loginToBook')}
        </Button>
      </Link>
    );
  }

  // Registration required but user not registered (Issue #77)
  if (needsRegistration) {
    return (
      <Link href={`/exhibitions/${session.exhibition_id}/sessions`}>
        <Button variant="secondary" className="w-full sm:w-auto">
          {tExhibition('registrationRequired')}
        </Button>
      </Link>
    );
  }

  // User has a booking
  if (userBooking) {
    const { status } = userBooking;

    // Already checked in
    if (status === 'CHECKED_IN') {
      return (
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <span className="text-emerald-600 dark:text-emerald-400 font-medium">
            ✓ {t('bookingSuccess')}
          </span>
        </div>
      );
    }

    // Confirmed booking
    if (status === 'CONFIRMED') {
      return (
        <div className="flex flex-col sm:flex-row gap-3">
          {canCheckIn && (
            <Button
              variant="success"
              onClick={onCheckIn}
              isLoading={isLoading}
              className="w-full sm:w-auto"
            >
              {t('checkIn')}
            </Button>
          )}
          <Button
            variant="danger"
            onClick={onCancelBooking}
            isLoading={isLoading}
            className="w-full sm:w-auto"
          >
            {t('cancelBooking')}
          </Button>
        </div>
      );
    }

    // On waitlist
    if (status === 'WAITING_LIST') {
      return (
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <span className="text-amber-500 dark:text-amber-400 text-sm font-medium">
            {t('waitlistSuccess')}
          </span>
          <Button
            variant="ghost"
            onClick={onCancelBooking}
            isLoading={isLoading}
            className="w-full sm:w-auto text-red-600 dark:text-red-400"
          >
            {t('cancelBooking')}
          </Button>
        </div>
      );
    }
  }

  // Can book a seat
  if (canBook) {
    return (
      <Button
        variant="success"
        onClick={onBook}
        isLoading={isLoading}
        className="w-full sm:w-auto"
      >
        {t('book')}
      </Button>
    );
  }

  // Session full - can join waitlist
  if (canJoinWaitlist) {
    return (
      <Button
        variant="secondary"
        onClick={onJoinWaitlist}
        isLoading={isLoading}
        className="w-full sm:w-auto"
      >
        {t('joinWaitlist')}
      </Button>
    );
  }

  // Fallback
  return (
    <Button variant="secondary" disabled className="w-full sm:w-auto">
      {t('full')}
    </Button>
  );
}
