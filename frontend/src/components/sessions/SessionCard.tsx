'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import Image from 'next/image';
import { Card, Badge } from '@/components/ui';
import { AvailabilityBadge } from './AvailabilityBadge';
import { SafetyToolsBadges } from './SafetyToolsBadges';
import { ProviderBadge } from '@/components/games/ProviderBadge';
import { formatDate, formatTime } from '@/lib/utils';
import type { GameSession } from '@/lib/api/types';

interface SessionCardProps {
  session: GameSession;
  locale?: string;
  currentUserId?: string | null;
}

export function SessionCard({ session, locale = 'fr', currentUserId }: SessionCardProps) {
  const t = useTranslations('GameTable');
  const tSession = useTranslations('Session');

  // Check if current user is the GM
  const isGM = currentUserId && session.created_by_user_id === currentUserId;

  const sessionDate = formatDate(session.scheduled_start, locale);
  const startTime = formatTime(session.scheduled_start, locale);
  const endTime = formatTime(session.scheduled_end, locale);

  return (
    <Link href={`/sessions/${session.id}`}>
      <Card variant="interactive" className="h-full">
        <Card.Content className="space-y-3">
          {/* Header: Title + Status */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-slate-900 dark:text-white line-clamp-2">
                {session.title}
              </h3>
              {isGM && (
                <Badge size="sm" variant="info" className="mt-1">
                  🎲 {tSession('youAreGM')}
                </Badge>
              )}
            </div>
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
              {session.game_cover_image_url && (
                <Image
                  src={session.game_cover_image_url}
                  alt=""
                  width={32}
                  height={44}
                  className="w-8 h-11 object-cover rounded flex-shrink-0"
                  unoptimized
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              )}
              <span>🎲</span>
              <span className="line-clamp-1">{session.game_title}</span>
              {session.game_external_provider && (
                <ProviderBadge provider={session.game_external_provider} />
              )}
            </div>
          )}

          {/* Date, Time & Location */}
          <div className="flex flex-col gap-1 text-sm text-slate-600 dark:text-slate-400">
            <div className="flex items-center gap-2">
              <span>📅</span>
              <span>{sessionDate}</span>
            </div>
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
