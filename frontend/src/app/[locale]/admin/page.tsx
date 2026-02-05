'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { adminApi, eventRequestsApi, PlatformStats, Exhibition } from '@/lib/api';
import { Card, Button, Badge } from '@/components/ui';
import type { EventRequestStatus, EventRequestListResponse } from '@/lib/api/types';

interface StatCardProps {
  label: string;
  value: number;
  href?: string;
}

function StatCard({ label, value, href }: StatCardProps) {
  const content = (
    <Card className="h-full">
      <Card.Content>
        <p
          className="text-sm font-medium mb-1"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          {label}
        </p>
        <p
          className="text-3xl font-bold"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {value}
        </p>
      </Card.Content>
    </Card>
  );

  if (href) {
    return (
      <Link href={href} className="block hover:opacity-80 transition-opacity">
        {content}
      </Link>
    );
  }

  return content;
}

function RequestStatusBadge({ status }: { status: EventRequestStatus }) {
  const variants: Record<EventRequestStatus, 'warning' | 'success' | 'danger' | 'default'> = {
    PENDING: 'warning',
    CHANGES_REQUESTED: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger',
  };

  return (
    <Badge variant={variants[status]}>
      {status === 'CHANGES_REQUESTED' && '⚠️ '}
      {status}
    </Badge>
  );
}

export default function AdminDashboardPage() {
  const t = useTranslations('SuperAdmin');
  const tAdmin = useTranslations('Admin');

  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [recentExhibitions, setRecentExhibitions] = useState<Exhibition[]>([]);
  const [eventRequestsData, setEventRequestsData] = useState<EventRequestListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);

      try {
        const [statsResponse, exhibitionsResponse, requestsResponse] = await Promise.all([
          adminApi.getStats(),
          adminApi.listExhibitions({ limit: 5 }),
          eventRequestsApi.list({ status: 'PENDING' }),
        ]);

        if (statsResponse.error) {
          setError(statsResponse.error.message);
        } else if (statsResponse.data) {
          setStats(statsResponse.data);
        }

        if (exhibitionsResponse.data) {
          setRecentExhibitions(exhibitionsResponse.data);
        }

        if (requestsResponse.data) {
          setEventRequestsData(requestsResponse.data);
        }
      } catch {
        setError('Failed to load dashboard data');
      }

      setIsLoading(false);
    }

    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-24 rounded-lg"
              style={{ backgroundColor: 'var(--color-bg-secondary)' }}
            />
          ))}
        </div>
        <div
          className="h-64 rounded-lg"
          style={{ backgroundColor: 'var(--color-bg-secondary)' }}
        />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <Card.Content>
          <p style={{ color: 'var(--color-text-danger)' }}>{error}</p>
        </Card.Content>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard
          label={t('stats.totalUsers')}
          value={stats?.users.total || 0}
          href="/admin/users"
        />
        <StatCard
          label={t('stats.admins')}
          value={stats?.users.by_role?.ADMIN || 0}
          href="/admin/users?role=ADMIN"
        />
        <StatCard
          label={t('stats.publishedExhibitions')}
          value={stats?.exhibitions.by_status?.PUBLISHED || 0}
          href="/admin/exhibitions?status=PUBLISHED"
        />
        <StatCard
          label={t('stats.draftExhibitions')}
          value={stats?.exhibitions.by_status?.DRAFT || 0}
          href="/admin/exhibitions?status=DRAFT"
        />
        <StatCard
          label={t('stats.pendingRequests')}
          value={eventRequestsData?.pending_count || 0}
          href="/admin/event-requests?status=PENDING"
        />
      </div>

      {/* Exhibition stats breakdown */}
      <Card>
        <Card.Header>
          <Card.Title>{t('exhibitions')}</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p
                className="text-2xl font-bold"
                style={{ color: 'var(--color-text-warning)' }}
              >
                {stats?.exhibitions.by_status?.DRAFT || 0}
              </p>
              <p
                className="text-sm"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('stats.draftExhibitions')}
              </p>
            </div>
            <div>
              <p
                className="text-2xl font-bold"
                style={{ color: 'var(--color-text-success)' }}
              >
                {stats?.exhibitions.by_status?.PUBLISHED || 0}
              </p>
              <p
                className="text-sm"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('stats.publishedExhibitions')}
              </p>
            </div>
            <div>
              <p
                className="text-2xl font-bold"
                style={{ color: 'var(--color-text-muted)' }}
              >
                {stats?.exhibitions.by_status?.ARCHIVED || 0}
              </p>
              <p
                className="text-sm"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('stats.archivedExhibitions')}
              </p>
            </div>
          </div>
        </Card.Content>
      </Card>

      {/* Pending event requests */}
      {eventRequestsData && eventRequestsData.items.length > 0 && (
        <Card>
          <Card.Header>
            <div className="flex items-center justify-between">
              <Card.Title>{t('pendingEventRequests')}</Card.Title>
              <Link
                href="/admin/event-requests"
                className="text-sm font-medium hover:underline"
                style={{ color: 'var(--color-primary)' }}
              >
                {t('viewAll')}
              </Link>
            </div>
          </Card.Header>
          <Card.Content>
            <div className="space-y-3">
              {eventRequestsData.items.slice(0, 5).map((request) => (
                <div
                  key={request.id}
                  className="flex items-center justify-between p-3 rounded-lg"
                  style={{ backgroundColor: 'var(--color-bg-secondary)' }}
                >
                  <div className="flex-1 min-w-0">
                    <p
                      className="font-medium truncate"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {request.event_title}
                    </p>
                    <p
                      className="text-sm truncate"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {request.organization_name} • {request.requester_name || request.requester_email}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 ml-4">
                    <RequestStatusBadge status={request.status as EventRequestStatus} />
                    <Link href={`/admin/event-requests/${request.id}`}>
                      <Button variant="secondary" size="sm">
                        {tAdmin('view')}
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Recent exhibitions */}
      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <Card.Title>{t('recentExhibitions')}</Card.Title>
            <Link
              href="/admin/exhibitions"
              className="text-sm font-medium hover:underline"
              style={{ color: 'var(--color-primary)' }}
            >
              {t('viewAll')}
            </Link>
          </div>
        </Card.Header>
        <Card.Content>
          {recentExhibitions.length === 0 ? (
            <p style={{ color: 'var(--color-text-muted)' }}>
              {t('noExhibitions')}
            </p>
          ) : (
            <div className="space-y-3">
              {recentExhibitions.map((exhibition) => (
                <div
                  key={exhibition.id}
                  className="flex items-center justify-between p-3 rounded-lg"
                  style={{ backgroundColor: 'var(--color-bg-secondary)' }}
                >
                  <div className="flex-1 min-w-0">
                    <p
                      className="font-medium truncate"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {exhibition.title}
                    </p>
                    <p
                      className="text-sm"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {new Date(exhibition.start_date).toLocaleDateString()} -{' '}
                      {new Date(exhibition.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 ml-4">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded ${
                        exhibition.status === 'PUBLISHED'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : exhibition.status === 'DRAFT'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            : 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
                      }`}
                    >
                      {exhibition.status}
                    </span>
                    <Link href={`/exhibitions/${exhibition.id}/manage`}>
                      <Button variant="secondary" size="sm">
                        {tAdmin('view')}
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
