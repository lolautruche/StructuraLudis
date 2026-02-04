'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter, Link } from '@/i18n/routing';
import { userApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { ExhibitionCard } from '@/components/exhibitions';
import { Card, Button } from '@/components/ui';
import type { MyExhibitions } from '@/lib/api/types';

export default function MyEventsPage() {
  const t = useTranslations('MyEvents');
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [myExhibitions, setMyExhibitions] = useState<MyExhibitions | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch my exhibitions
  useEffect(() => {
    async function fetchMyExhibitions() {
      setIsLoading(true);
      const response = await userApi.getMyExhibitions();
      if (response.data) {
        setMyExhibitions(response.data);
      }
      setIsLoading(false);
    }

    if (isAuthenticated) {
      fetchMyExhibitions();
    }
  }, [isAuthenticated]);

  if (authLoading || !isAuthenticated) {
    return null;
  }

  const hasOrganized = myExhibitions && myExhibitions.organized.length > 0;
  const hasRegistered = myExhibitions && myExhibitions.registered.length > 0;
  const hasBoth = hasOrganized && hasRegistered;
  const hasNone = !hasOrganized && !hasRegistered;

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
      ) : hasNone ? (
        /* Empty state */
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">📅</div>
            <h3
              className="text-lg font-semibold mb-2"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {t('noEvents')}
            </h3>
            <p className="mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              {t('noEventsDescription')}
            </p>
            <Link href="/exhibitions">
              <Button variant="primary">{t('browseEvents')}</Button>
            </Link>
          </Card.Content>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* Organized exhibitions */}
          {hasOrganized && (
            <section>
              {hasBoth && (
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                  <span>📋</span>
                  {t('organizedSection')}
                </h2>
              )}
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {myExhibitions!.organized.map((exhibition) => (
                  <ExhibitionCard
                    key={exhibition.id}
                    exhibition={exhibition}
                    locale={locale}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Registered exhibitions */}
          {hasRegistered && (
            <section>
              {hasBoth && (
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                  <span>🎮</span>
                  {t('registeredSection')}
                </h2>
              )}
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {myExhibitions!.registered.map((exhibition) => (
                  <ExhibitionCard
                    key={exhibition.id}
                    exhibition={exhibition}
                    locale={locale}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
