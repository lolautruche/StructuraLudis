'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Button, Card } from '@/components/ui';
import { ExhibitionCard } from '@/components/exhibitions';
import { exhibitionsApi } from '@/lib/api';
import type { Exhibition } from '@/lib/api/types';

export default function HomePage() {
  const t = useTranslations('Home');
  const tCommon = useTranslations('Common');
  const locale = useLocale();

  const [exhibitions, setExhibitions] = useState<Exhibition[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchExhibitions() {
      const response = await exhibitionsApi.list();
      if (response.data) {
        // Sort by start_date, upcoming first
        const sorted = response.data.sort((a, b) =>
          new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
        );
        setExhibitions(sorted);
      }
      setIsLoading(false);
    }
    fetchExhibitions();
  }, []);

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="text-gradient">Structura Ludis</span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-8">
          {t('subtitle')}
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link href="/auth/register">
            <Button variant="primary" size="lg">
              {tCommon('register')}
            </Button>
          </Link>
        </div>
      </section>

      {/* Exhibitions */}
      <section>
        <h2 className="text-2xl font-bold mb-6">{t('upcomingEvents')}</h2>

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
      </section>

      {/* Features */}
      <section>
        <h2 className="text-2xl font-bold mb-6">{t('howItWorks')}</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <Card.Content className="text-center py-8">
              <div className="text-4xl mb-4">🎲</div>
              <h3 className="text-lg font-semibold mb-2">{t('feature1Title')}</h3>
              <p className="text-slate-400 text-sm">
                {t('feature1Description')}
              </p>
            </Card.Content>
          </Card>

          <Card>
            <Card.Content className="text-center py-8">
              <div className="text-4xl mb-4">📅</div>
              <h3 className="text-lg font-semibold mb-2">{t('feature2Title')}</h3>
              <p className="text-slate-400 text-sm">
                {t('feature2Description')}
              </p>
            </Card.Content>
          </Card>

          <Card>
            <Card.Content className="text-center py-8">
              <div className="text-4xl mb-4">🔔</div>
              <h3 className="text-lg font-semibold mb-2">{t('feature3Title')}</h3>
              <p className="text-slate-400 text-sm">
                {t('feature3Description')}
              </p>
            </Card.Content>
          </Card>
        </div>
      </section>
    </div>
  );
}
