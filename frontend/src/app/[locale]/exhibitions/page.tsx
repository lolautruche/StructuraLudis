'use client';

import { useState, useEffect, useMemo } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Card } from '@/components/ui';
import { ExhibitionCard } from '@/components/exhibitions';
import { exhibitionsApi } from '@/lib/api';
import type { Exhibition } from '@/lib/api/types';

export default function ExhibitionsPage() {
  const t = useTranslations('Exhibition');
  const locale = useLocale();

  const [exhibitions, setExhibitions] = useState<Exhibition[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchExhibitions() {
      const response = await exhibitionsApi.list();
      if (response.data) {
        // Sort by start_date
        const sorted = response.data.sort((a, b) =>
          new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
        );
        setExhibitions(sorted);
      }
      setIsLoading(false);
    }
    fetchExhibitions();
  }, []);

  // Separate current/upcoming from past exhibitions
  const { currentAndUpcoming, past } = useMemo(() => {
    const now = new Date();
    const current: Exhibition[] = [];
    const pastExhibitions: Exhibition[] = [];

    exhibitions.forEach((exhibition) => {
      const endDate = new Date(exhibition.end_date);
      if (endDate < now) {
        pastExhibitions.push(exhibition);
      } else {
        current.push(exhibition);
      }
    });

    return {
      currentAndUpcoming: current,
      past: pastExhibitions.reverse(), // Most recent past first
    };
  }, [exhibitions]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-slate-400 mt-1">{t('selectEvent')}</p>
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <Card.Content className="space-y-4">
                <div className="h-6 bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-700 rounded w-full" />
                <div className="h-4 bg-slate-700 rounded w-1/2" />
                <div className="h-4 bg-slate-700 rounded w-2/3" />
              </Card.Content>
            </Card>
          ))}
        </div>
      ) : exhibitions.length === 0 ? (
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">📅</div>
            <h3 className="text-lg font-semibold text-white mb-2">
              {t('noEvents')}
            </h3>
            <p className="text-slate-400">
              {t('noEventsDescription')}
            </p>
          </Card.Content>
        </Card>
      ) : (
        <>
          {/* Current & Upcoming Events */}
          {currentAndUpcoming.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-4">{t('upcomingAndCurrent')}</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {currentAndUpcoming.map((exhibition) => (
                  <ExhibitionCard
                    key={exhibition.id}
                    exhibition={exhibition}
                    locale={locale}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Past Events */}
          {past.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-4 text-slate-400">{t('pastEvents')}</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 opacity-75">
                {past.map((exhibition) => (
                  <ExhibitionCard
                    key={exhibition.id}
                    exhibition={exhibition}
                    locale={locale}
                  />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
