'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Badge } from '@/components/ui';
import { AvailabilityBadge } from './AvailabilityBadge';
import { SafetyToolsBadges } from './SafetyToolsBadges';
import { formatTime } from '@/lib/utils';
import type { GameSession } from '@/lib/api/types';

interface SessionCardProps {
  session: GameSession;
  locale?: string;
}

export function SessionCard({ session, locale = 'fr' }: SessionCardProps) {
  const t = useTranslations('GameTable');

  const startTime = formatTime(session.scheduled_start, locale);
  const endTime = formatTime(session.scheduled_end, locale);

  return (
    <Link href={`/sessions/${session.id}`}>
      <Card variant="interactive" className="h-full">
        <Card.Content className="space-y-3">
          {/* Header: Title + Status */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-slate-900 dark:text-white line-clamp-2">
              {session.title}
            </h3>
            <AvailabilityBadge
              status={session.status}
              availableSeats={session.max_players_count - session.confirmed_players_count}
              totalSeats={session.max_players_count}
              waitlistCount={session.waitlist_count}
            />
          </div>

          {/* Game info */}
          {session.game_title && (
            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
              <span>🎲</span>
              <span className="line-clamp-1">{session.game_title}</span>
            </div>
          )}

          {/* Time & Location */}
          <div className="flex flex-col gap-1 text-sm text-slate-600 dark:text-slate-400">
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

          {/* GM */}
          {session.gm_name && (
            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
              <span>👤</span>
              <span>{t('gm')}: {session.gm_name}</span>
            </div>
          )}

          {/* Footer: Badges */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-700">
            {/* Language */}
            <Badge size="sm" variant="default">
              {session.language.toUpperCase()}
            </Badge>

            {/* Min age */}
            {session.min_age > 0 && (
              <Badge size="sm" variant="default">
                {t('minAge', { age: session.min_age })}
              </Badge>
            )}

            {/* Accessibility */}
            {session.is_accessible_disability && (
              <Badge size="sm" variant="info">
                ♿
              </Badge>
            )}
          </div>

          {/* Safety tools */}
          {session.safety_tools && session.safety_tools.length > 0 && (
            <SafetyToolsBadges tools={session.safety_tools} max={2} />
          )}
        </Card.Content>
      </Card>
    </Link>
  );
}
