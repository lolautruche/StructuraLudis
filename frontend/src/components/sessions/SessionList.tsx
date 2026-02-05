'use client';

import { useTranslations } from 'next-intl';
import { SessionCard } from './SessionCard';
import { Card } from '@/components/ui';
import type { GameSession, Exhibition } from '@/lib/api/types';

interface SessionsByExhibition {
  exhibition: Exhibition;
  sessions: GameSession[];
}

interface SessionListProps {
  sessionsByExhibition: SessionsByExhibition[];
  isLoading?: boolean;
  locale?: string;
  currentUserId?: string | null;
}

function formatExhibitionDates(exhibition: Exhibition, locale: string): string {
  const startDate = new Date(exhibition.start_date);
  const endDate = new Date(exhibition.end_date);
  const options: Intl.DateTimeFormatOptions = {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  };
  const start = startDate.toLocaleDateString(locale, options);
  const end = endDate.toLocaleDateString(locale, options);
  return `${start} - ${end}`;
}

export function SessionList({
  sessionsByExhibition,
  isLoading = false,
  locale = 'fr',
  currentUserId,
}: SessionListProps) {
  const t = useTranslations('Discovery');

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="space-y-4">
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/3 animate-pulse" />
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
        </div>
      </div>
    );
  }

  // Empty state
  if (sessionsByExhibition.length === 0) {
    return (
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
    );
  }

  // Sessions grouped by exhibition
  return (
    <div className="space-y-10">
      {sessionsByExhibition.map(({ exhibition, sessions }) => (
        <section key={exhibition.id}>
          {/* Exhibition header */}
          <div className="mb-4 pb-2 border-b border-slate-200 dark:border-slate-700">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{exhibition.title}</h2>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-slate-400 mt-1">
              <span>📅 {formatExhibitionDates(exhibition, locale)}</span>
              {exhibition.location_name && (
                <span>📍 {exhibition.location_name}{exhibition.city ? `, ${exhibition.city}` : ''}</span>
              )}
              <span className="text-slate-500 dark:text-slate-500">
                {sessions.length} {sessions.length > 1 ? t('sessions') : t('session')}
              </span>
            </div>
          </div>

          {/* Session grid */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <SessionCard key={session.id} session={session} locale={locale} currentUserId={currentUserId} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
