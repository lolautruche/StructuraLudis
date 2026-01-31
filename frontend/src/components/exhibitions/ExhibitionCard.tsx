'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Badge } from '@/components/ui';
import type { Exhibition } from '@/lib/api/types';

interface ExhibitionCardProps {
  exhibition: Exhibition;
  locale?: string;
}

function formatDateRange(startDate: string, endDate: string, locale: string): string {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const options: Intl.DateTimeFormatOptions = {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  };
  return `${start.toLocaleDateString(locale, options)} - ${end.toLocaleDateString(locale, options)}`;
}

export function ExhibitionCard({ exhibition, locale = 'fr' }: ExhibitionCardProps) {
  const t = useTranslations('Exhibition');

  const isOpen = exhibition.is_registration_open;
  const isPast = new Date(exhibition.end_date) < new Date();

  return (
    <Link href={`/exhibitions/${exhibition.id}/sessions`}>
      <Card variant="interactive" className="h-full">
        <Card.Content className="space-y-4">
          {/* Header: Title + Status */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-xl font-bold text-white line-clamp-2">
              {exhibition.title}
            </h3>
            {isPast ? (
              <Badge variant="default" size="sm">{t('past')}</Badge>
            ) : isOpen ? (
              <Badge variant="success" size="sm">{t('registrationOpen')}</Badge>
            ) : (
              <Badge variant="warning" size="sm">{t('registrationClosed')}</Badge>
            )}
          </div>

          {/* Description */}
          {exhibition.description && (
            <p className="text-slate-400 text-sm line-clamp-2">
              {exhibition.description}
            </p>
          )}

          {/* Date & Location */}
          <div className="flex flex-col gap-2 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <span>📅</span>
              <span>{formatDateRange(exhibition.start_date, exhibition.end_date, locale)}</span>
            </div>
            {(exhibition.location_name || exhibition.city) && (
              <div className="flex items-center gap-2">
                <span>📍</span>
                <span>
                  {[exhibition.location_name, exhibition.city].filter(Boolean).join(', ')}
                </span>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="pt-2 border-t border-slate-700">
            <span className="text-sm text-primary-400 font-medium">
              {t('viewSessions')} →
            </span>
          </div>
        </Card.Content>
      </Card>
    </Link>
  );
}
