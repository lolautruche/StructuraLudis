'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Button } from '@/components/ui';
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

  // Fetch session details
  const fetchSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const response = await sessionsApi.getById(sessionId);
    if (response.data) {
      setSession(response.data);
    } else {
      setError(response.error?.message || 'Session not found');
    }

    setIsLoading(false);
  }, [sessionId]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  // Handle booking
  const handleBook = useCallback(async () => {
    if (!session) return;
    setIsBooking(true);

    const response = await sessionsApi.book(session.id);
    if (response.data) {
      setUserBooking(response.data);
      // Refresh session to get updated counts
      await fetchSession();
    }

    setIsBooking(false);
  }, [session, fetchSession]);

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

  // Handle cancel booking
  const handleCancelBooking = useCallback(async () => {
    if (!userBooking) return;
    setIsBooking(true);

    const response = await sessionsApi.cancelBooking(userBooking.id);
    if (!response.error) {
      setUserBooking(null);
      await fetchSession();
    }

    setIsBooking(false);
  }, [userBooking, fetchSession]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary mx-auto mb-4" />
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !session) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <h2 className="text-xl font-semibold text-white mb-2">
          {t('sessionNotFound')}
        </h2>
        <p className="text-slate-400 mb-6">{t('sessionNotFoundDescription')}</p>
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
        className="inline-flex items-center text-slate-400 hover:text-white transition-colors"
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

      {/* Session detail */}
      <SessionDetail
        session={session}
        locale={locale}
        userBooking={userBooking}
        isAuthenticated={isAuthenticated}
        onBook={handleBook}
        onJoinWaitlist={handleJoinWaitlist}
        onCancelBooking={handleCancelBooking}
        isLoading={isBooking}
      />
    </div>
  );
}
