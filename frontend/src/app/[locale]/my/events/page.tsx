'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { exhibitionsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { ExhibitionCard } from '@/components/exhibitions';
import { Card } from '@/components/ui';
import type { Exhibition } from '@/lib/api/types';

export default function MyEventsPage() {
  const t = useTranslations('MyEvents');
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [exhibitions, setExhibitions] = useState<Exhibition[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch exhibitions user can manage
  useEffect(() => {
    async function fetchExhibitions() {
      setIsLoading(true);
      const response = await exhibitionsApi.list();
      if (response.data) {
        // Filter to only exhibitions user can manage
        const manageable = response.data.filter((e) => e.can_manage);
        // Sort by start_date
        const sorted = manageable.sort(
          (a, b) =>
            new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
        );
        setExhibitions(sorted);
      }
      setIsLoading(false);
    }

    if (isAuthenticated) {
      fetchExhibitions();
    }
  }, [isAuthenticated]);

  if (authLoading || !isAuthenticated) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
          {t('title')}
        </h1>
        <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          {t('subtitle')}
        </p>
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <Card.Content className="space-y-4">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
              </Card.Content>
            </Card>
          ))}
        </div>
      ) : exhibitions.length === 0 ? (
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">📅</div>
            <h3
              className="text-lg font-semibold mb-2"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {t('noEvents')}
            </h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              {t('noEventsDescription')}
            </p>
          </Card.Content>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {exhibitions.map((exhibition) => (
            <ExhibitionCard
              key={exhibition.id}
              exhibition={exhibition}
              locale={locale}
            />
          ))}
        </div>
      )}
    </div>
  );
}
