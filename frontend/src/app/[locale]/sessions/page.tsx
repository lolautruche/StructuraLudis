'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { useRouter, usePathname } from '@/i18n/routing';
import {
  SessionList,
  SessionFilters,
  defaultFilters,
  type SessionFiltersState,
} from '@/components/sessions';
import { sessionsApi } from '@/lib/api';
import type { GameSession } from '@/lib/api/types';

export default function SessionsPage() {
  const t = useTranslations('Discovery');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [sessions, setSessions] = useState<GameSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize filters from URL
  const [filters, setFilters] = useState<SessionFiltersState>(() => ({
    query: searchParams.get('q') || '',
    hasSeats: searchParams.get('hasSeats') === 'true',
    language: searchParams.get('lang') || '',
  }));

  // Sync filters to URL
  const updateUrl = useCallback(
    (newFilters: SessionFiltersState) => {
      const params = new URLSearchParams();
      if (newFilters.query) params.set('q', newFilters.query);
      if (newFilters.hasSeats) params.set('hasSeats', 'true');
      if (newFilters.language) params.set('lang', newFilters.language);

      const queryString = params.toString();
      router.replace(`${pathname}${queryString ? `?${queryString}` : ''}`, {
        scroll: false,
      });
    },
    [router, pathname]
  );

  const handleFiltersChange = useCallback(
    (newFilters: SessionFiltersState) => {
      setFilters(newFilters);
      updateUrl(newFilters);
    },
    [updateUrl]
  );

  const handleReset = useCallback(() => {
    setFilters(defaultFilters);
    updateUrl(defaultFilters);
  }, [updateUrl]);

  // Fetch sessions
  useEffect(() => {
    async function fetchSessions() {
      setIsLoading(true);
      const response = await sessionsApi.search({
        status: 'VALIDATED',
        has_available_seats: filters.hasSeats || undefined,
        language: filters.language || undefined,
      });

      if (response.data) {
        setSessions(response.data.items || []);
      }
      setIsLoading(false);
    }

    fetchSessions();
  }, [filters.hasSeats, filters.language]);

  // Client-side filtering for text search (instant feedback)
  const filteredSessions = useMemo(() => {
    if (!filters.query) return sessions;

    const query = filters.query.toLowerCase();
    return sessions.filter(
      (session) =>
        session.title.toLowerCase().includes(query) ||
        session.game_title?.toLowerCase().includes(query) ||
        session.gm_name?.toLowerCase().includes(query)
    );
  }, [sessions, filters.query]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <span className="text-sm text-slate-400">
          {filteredSessions.length} {t('allSessions').toLowerCase()}
        </span>
      </div>

      {/* Filters */}
      <SessionFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onReset={handleReset}
      />

      {/* Session List */}
      <SessionList
        sessions={filteredSessions}
        isLoading={isLoading}
        locale={locale}
      />
    </div>
  );
}
