'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { AgendaTimeline } from '@/components/agenda';
import { userApi, exhibitionsApi, sessionsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { UserAgenda } from '@/lib/api/types';

export default function AgendaPage() {
  const t = useTranslations('Agenda');
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [agenda, setAgenda] = useState<UserAgenda | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exhibitionId, setExhibitionId] = useState<string | null>(null);

  // Fetch exhibitions to get the first one (for now)
  useEffect(() => {
    async function fetchExhibition() {
      // Get first available exhibition
      const response = await exhibitionsApi.list();
      if (response.data?.[0]) {
        setExhibitionId(response.data[0].id);
      } else {
        // No exhibition found, stop loading
        setIsLoading(false);
      }
    }

    if (isAuthenticated && !exhibitionId) {
      fetchExhibition();
    }
  }, [isAuthenticated, exhibitionId]);

  // Fetch agenda
  const fetchAgenda = useCallback(async () => {
    if (!exhibitionId) return;

    setIsLoading(true);
    setError(null);

    const response = await userApi.getMyAgenda(exhibitionId);
    if (response.data) {
      setAgenda(response.data);
    } else {
      setError(response.error?.message || 'Failed to load agenda');
    }

    setIsLoading(false);
  }, [exhibitionId]);

  useEffect(() => {
    if (isAuthenticated && exhibitionId) {
      fetchAgenda();
    }
  }, [isAuthenticated, exhibitionId, fetchAgenda]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Handle check-in
  const handleCheckIn = async (bookingId: string) => {
    const response = await userApi.checkIn(bookingId);
    if (response.data) {
      // Refresh agenda
      await fetchAgenda();
    }
  };

  // Handle cancel booking
  const handleCancelBooking = async (bookingId: string) => {
    const response = await sessionsApi.cancelBooking(bookingId);
    if (!response.error) {
      // Refresh agenda
      await fetchAgenda();
    }
  };

  // Loading state
  if (authLoading || (isAuthenticated && isLoading)) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return null; // Will redirect
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  // No exhibition found
  if (!exhibitionId) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{t('title')}</h1>
        <div className="text-center py-12">
          <p className="text-slate-600 dark:text-slate-400">{t('noSessions')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{t('title')}</h1>
        {agenda && (
          <span className="text-sm text-slate-600 dark:text-slate-400">
            {agenda.exhibition_title}
          </span>
        )}
      </div>

      {/* Agenda Timeline */}
      {agenda && (
        <AgendaTimeline
          agenda={agenda}
          locale={locale}
          onCheckIn={handleCheckIn}
          onCancelBooking={handleCancelBooking}
        />
      )}
    </div>
  );
}
