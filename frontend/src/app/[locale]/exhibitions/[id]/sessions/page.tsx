'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useParams, useSearchParams } from 'next/navigation';
import { useRouter, usePathname, Link } from '@/i18n/routing';
import {
  SessionFilters,
  defaultFilters,
  type SessionFiltersState,
} from '@/components/sessions';
import { SessionCard } from '@/components/sessions/SessionCard';
import { RegistrationButton } from '@/components/exhibitions';
import { Button, Card } from '@/components/ui';
import { sessionsApi, exhibitionsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { GameSession, Exhibition } from '@/lib/api/types';

export default function ExhibitionSessionsPage() {
  const t = useTranslations('Discovery');
  const tExhibition = useTranslations('Exhibition');
  const locale = useLocale();
  const params = useParams();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const exhibitionId = params.id as string;
  const { isAuthenticated, user } = useAuth();

  const [exhibition, setExhibition] = useState<Exhibition | null>(null);
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

  // Fetch data function (can be called to refresh)
  const fetchData = useCallback(async () => {
    setIsLoading(true);

    // Fetch exhibition details
    const exhibitionResponse = await exhibitionsApi.getById(exhibitionId);
    if (exhibitionResponse.data) {
      setExhibition(exhibitionResponse.data);
    }

    // Fetch sessions
    const sessionsResponse = await sessionsApi.search({
      exhibition_id: exhibitionId,
      status: 'VALIDATED',
      has_available_seats: filters.hasSeats || undefined,
      language: filters.language || undefined,
    });

    if (sessionsResponse.data) {
      setSessions(sessionsResponse.data);
    }
    setIsLoading(false);
  }, [exhibitionId, filters.hasSeats, filters.language]);

  // Fetch exhibition and sessions
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Client-side filtering for text search
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

  // Format exhibition dates
  const formatDateRange = (startDate: string, endDate: string): string => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const options: Intl.DateTimeFormatOptions = {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    };
    return `${start.toLocaleDateString(locale, options)} - ${end.toLocaleDateString(locale, options)}`;
  };

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link href="/exhibitions" className="text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">
        ← {tExhibition('backToEvents')}
      </Link>

      {/* Exhibition Header */}
      {exhibition && (
        <div className="border-b border-slate-200 dark:border-slate-700 pb-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">{exhibition.title}</h1>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-slate-400">
                <span>📅 {formatDateRange(exhibition.start_date, exhibition.end_date)}</span>
                {(exhibition.location_name || exhibition.city) && (
                  <span>📍 {[exhibition.location_name, exhibition.city].filter(Boolean).join(', ')}</span>
                )}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <RegistrationButton
                exhibition={exhibition}
                onRegistrationChange={fetchData}
              />
              {exhibition.can_manage && (
                <Link href={`/exhibitions/${exhibitionId}/manage`}>
                  <Button variant="secondary">
                    {tExhibition('manage')}
                  </Button>
                </Link>
              )}
              {isAuthenticated && (
                // Hide propose session if registration required and not registered (unless user has a role)
                (!exhibition.requires_registration ||
                  exhibition.is_user_registered ||
                  exhibition.user_exhibition_role) && (
                  <Link href={`/my/sessions/new?exhibition=${exhibitionId}`}>
                    <Button variant="primary">
                      {tExhibition('proposeSession')}
                    </Button>
                  </Link>
                )
              )}
            </div>
          </div>
          {exhibition.description && (
            <p className="text-slate-600 dark:text-slate-400 mt-3">{exhibition.description}</p>
          )}
        </div>
      )}

      {/* Sessions count */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">{t('title')}</h2>
        <span className="text-sm text-slate-600 dark:text-slate-400">
          {filteredSessions.length} {t('allSessions').toLowerCase()}
        </span>
      </div>

      {/* Filters */}
      <SessionFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onReset={handleReset}
      />

      {/* Sessions Grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <Card.Content className="space-y-3">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
              </Card.Content>
            </Card>
          ))}
        </div>
      ) : filteredSessions.length === 0 ? (
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">🎲</div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              {t('noResults')}
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              {t('noResultsDescription')}
            </p>
          </Card.Content>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredSessions.map((session) => (
            <SessionCard key={session.id} session={session} locale={locale} currentUserId={user?.id} />
          ))}
        </div>
      )}
    </div>
  );
}
