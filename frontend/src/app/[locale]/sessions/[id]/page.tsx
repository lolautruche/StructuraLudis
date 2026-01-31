'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Button, ConfirmDialog } from '@/components/ui';
import { SessionDetail } from '@/components/sessions';
import { sessionsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { GameSession, Booking } from '@/lib/api/types';

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const t = useTranslations('Session');
  const locale = useLocale();
  const { isAuthenticated } = useAuth();

  const [session, setSession] = useState<GameSession | null>(null);
  const [userBooking, setUserBooking] = useState<Booking | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBooking, setIsBooking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  // Fetch session details and user booking in parallel
  const fetchSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    // Fetch session and booking in parallel
    const [sessionResponse, bookingResponse] = await Promise.all([
      sessionsApi.getById(sessionId),
      isAuthenticated ? sessionsApi.getMyBooking(sessionId) : Promise.resolve({ data: null }),
    ]);

    if (sessionResponse.data) {
      setSession(sessionResponse.data);
    } else {
      setError(sessionResponse.error?.message || 'Session not found');
    }

    if (bookingResponse.data) {
      setUserBooking(bookingResponse.data);
    }

    setIsLoading(false);
  }, [sessionId, isAuthenticated]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  // Map backend error messages to translated ones
  const translateBookingError = useCallback((errorMessage: string): string => {
    // Check for age restriction error
    const ageMatch = errorMessage.match(/minimum age of (\d+)/);
    if (ageMatch) {
      return t('errorAgeRestriction', { age: ageMatch[1] });
    }
    if (errorMessage.includes('full') || errorMessage.includes('no available seats')) {
      return t('errorSessionFull');
    }
    if (errorMessage.includes('already booked') || errorMessage.includes('already registered')) {
      return t('errorAlreadyBooked');
    }
    // Return original message if no match (fallback)
    return errorMessage;
  }, [t]);

  // Handle booking
  const handleBook = useCallback(async () => {
    if (!session) return;
    setIsBooking(true);
    setBookingError(null);

    const response = await sessionsApi.book(session.id);
    if (response.data) {
      setUserBooking(response.data);
      // Refresh session to get updated counts
      await fetchSession();
    } else if (response.error) {
      setBookingError(translateBookingError(response.error.message));
    }

    setIsBooking(false);
  }, [session, fetchSession, translateBookingError]);

  // Handle join waitlist
  const handleJoinWaitlist = useCallback(async () => {
    if (!session) return;
    setIsBooking(true);

    const response = await sessionsApi.joinWaitlist(session.id);
    if (response.data) {
      setUserBooking(response.data);
      await fetchSession();
    }

    setIsBooking(false);
  }, [session, fetchSession]);

  // Show cancel confirmation dialog
  const handleCancelBooking = useCallback(async () => {
    setShowCancelDialog(true);
  }, []);

  // Actually cancel the booking after confirmation
  const handleConfirmCancel = useCallback(async () => {
    if (!userBooking) return;
    setIsBooking(true);

    const response = await sessionsApi.cancelBooking(userBooking.id);
    if (!response.error) {
      setUserBooking(null);
      await fetchSession();
    }

    setIsBooking(false);
    setShowCancelDialog(false);
  }, [userBooking, fetchSession]);

  // Handle check-in
  const handleCheckIn = useCallback(async () => {
    if (!userBooking) return;
    setIsBooking(true);

    const response = await sessionsApi.checkIn(userBooking.id);
    if (response.data) {
      setUserBooking(response.data);
    }

    setIsBooking(false);
  }, [userBooking]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !session) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
          {t('sessionNotFound')}
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">{t('sessionNotFoundDescription')}</p>
        <Link href="/exhibitions">
          <Button variant="primary">{t('backToSessions')}</Button>
        </Link>
      </div>
    );
  }

  const backUrl = `/exhibitions/${session.exhibition_id}/sessions`;

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href={backUrl}
        className="inline-flex items-center text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
      >
        <svg
          className="w-5 h-5 mr-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        {t('backToSessions')}
      </Link>

      {/* Booking error message */}
      {bookingError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-red-500 dark:text-red-400 text-xl">⚠️</span>
            <p className="text-red-700 dark:text-red-300 flex-1">{bookingError}</p>
            <button
              onClick={() => setBookingError(null)}
              className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-200"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Session detail */}
      <SessionDetail
        session={session}
        locale={locale}
        userBooking={userBooking}
        isAuthenticated={isAuthenticated}
        onBook={handleBook}
        onJoinWaitlist={handleJoinWaitlist}
        onCancelBooking={handleCancelBooking}
        onCheckIn={handleCheckIn}
        isLoading={isBooking}
      />

      {/* Cancel confirmation dialog */}
      <ConfirmDialog
        isOpen={showCancelDialog}
        onClose={() => setShowCancelDialog(false)}
        onConfirm={handleConfirmCancel}
        title={t('cancelConfirmTitle')}
        message={t('cancelConfirmMessage')}
        confirmLabel={t('confirmCancel')}
        cancelLabel={t('keepBooking')}
        variant="danger"
        isLoading={isBooking}
      />
    </div>
  );
}
