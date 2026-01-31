'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Badge, Button } from '@/components/ui';
import { formatTime } from '@/lib/utils';
import type { MySessionSummary } from '@/lib/api/types';

interface AgendaSessionCardProps {
  session: MySessionSummary;
  locale?: string;
}

export function AgendaSessionCard({ session, locale = 'fr' }: AgendaSessionCardProps) {
  const t = useTranslations('Agenda');
  const tSession = useTranslations('Session');

  const startTime = formatTime(session.scheduled_start, locale);
  const endTime = formatTime(session.scheduled_end, locale);

  const getStatusBadge = () => {
    switch (session.status) {
      case 'VALIDATED':
        return <Badge variant="success" size="sm">{t('confirmed')}</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="info" size="sm">{tSession('inProgress')}</Badge>;
      case 'FINISHED':
        return <Badge variant="secondary" size="sm">{tSession('finished')}</Badge>;
      case 'DRAFT':
        return <Badge variant="warning" size="sm">Draft</Badge>;
      default:
        return null;
    }
  };

  return (
    <Card className="border-l-4 border-l-violet-500">
      <Card.Content className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="purple" size="sm">{t('asGm')}</Badge>
            {getStatusBadge()}
          </div>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-white">{session.title}</h3>

        {/* Time & Location */}
        <div className="flex flex-col gap-1 text-sm text-slate-400">
          <div className="flex items-center gap-2">
            <span>⏰</span>
            <span>{startTime} - {endTime}</span>
          </div>
          {(session.zone_name || session.table_label) && (
            <div className="flex items-center gap-2">
              <span>📍</span>
              <span>
                {[session.zone_name, session.table_label].filter(Boolean).join(' - ')}
              </span>
            </div>
          )}
        </div>

        {/* Players & Availability */}
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            <span>👥</span>
            <span className="text-slate-300">
              {session.confirmed_players}/{session.max_players_count}
            </span>
          </div>
          {session.confirmed_players < session.max_players_count ? (
            <span className="text-emerald-400">
              {tSession('spotsLeft', { count: session.max_players_count - session.confirmed_players })}
            </span>
          ) : (
            <span className="text-red-400">{tSession('full')}</span>
          )}
          {session.waitlist_count > 0 && (
            <span className="text-amber-400">
              (+{session.waitlist_count} {t('waitlisted').toLowerCase()})
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2 border-t border-slate-700">
          <Link href={`/sessions/${session.id}`}>
            <Button variant="ghost" size="sm">
              {t('viewDetails')}
            </Button>
          </Link>
          {session.status === 'VALIDATED' && (
            <Button variant="primary" size="sm">
              {t('startSession')}
            </Button>
          )}
        </div>
      </Card.Content>
    </Card>
  );
}
