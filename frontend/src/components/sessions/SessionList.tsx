'use client';

import { useTranslations } from 'next-intl';
import { SessionCard } from './SessionCard';
import { Card } from '@/components/ui';
import type { GameSession } from '@/lib/api/types';

interface SessionListProps {
  sessions: GameSession[];
  isLoading?: boolean;
  locale?: string;
}

export function SessionList({ sessions, isLoading = false, locale = 'fr' }: SessionListProps) {
  const t = useTranslations('Discovery');

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <Card.Content className="space-y-3">
              <div className="h-6 bg-slate-700 rounded w-3/4" />
              <div className="h-4 bg-slate-700 rounded w-1/2" />
              <div className="h-4 bg-slate-700 rounded w-2/3" />
              <div className="h-4 bg-slate-700 rounded w-1/3" />
            </Card.Content>
          </Card>
        ))}
      </div>
    );
  }

  // Empty state
  if (sessions.length === 0) {
    return (
      <Card>
        <Card.Content className="text-center py-12">
          <div className="text-4xl mb-4">🎲</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            {t('noResults')}
          </h3>
          <p className="text-slate-400">
            {t('noResultsDescription')}
          </p>
        </Card.Content>
      </Card>
    );
  }

  // Session grid
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {sessions.map((session) => (
        <SessionCard key={session.id} session={session} locale={locale} />
      ))}
    </div>
  );
}
