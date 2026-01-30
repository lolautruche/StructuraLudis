'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui';
import { Link } from '@/i18n/routing';
import type { GameSession, Booking } from '@/lib/api/types';

interface BookingButtonProps {
  session: GameSession;
  userBooking?: Booking | null;
  isAuthenticated?: boolean;
  onBook?: () => Promise<void>;
  onJoinWaitlist?: () => Promise<void>;
  onCancelBooking?: () => Promise<void>;
  isLoading?: boolean;
}

export function BookingButton({
  session,
  userBooking,
  isAuthenticated = false,
  onBook,
  onJoinWaitlist,
  onCancelBooking,
  isLoading = false,
}: BookingButtonProps) {
  const t = useTranslations('Session');

  const availableSeats = session.max_players_count - session.confirmed_players_count;
  const isFull = availableSeats <= 0;
  const canBook = session.status === 'VALIDATED' && session.has_available_seats;
  const canJoinWaitlist = session.status === 'VALIDATED' && isFull;

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
      <Link href="/login">
        <Button variant="primary" className="w-full sm:w-auto">
          {t('loginToBook')}
        </Button>
      </Link>
    );
  }

  // User has a booking
  if (userBooking) {
    const { status } = userBooking;

    // Already confirmed or checked in
    if (status === 'CONFIRMED' || status === 'CHECKED_IN') {
      return (
        <div className="flex flex-col sm:flex-row gap-3">
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
          <span className="text-amber-400 text-sm">
            {t('waitlistPosition', { position: session.waitlist_count })}
          </span>
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
