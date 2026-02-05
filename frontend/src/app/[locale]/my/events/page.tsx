'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter, Link } from '@/i18n/routing';
import { userApi, eventRequestsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { ExhibitionCard } from '@/components/exhibitions';
import { Card, Button, Badge } from '@/components/ui';
import type { MyExhibitions, EventRequest, EventRequestStatus } from '@/lib/api/types';

function RequestStatusBadge({ status }: { status: EventRequestStatus }) {
  const t = useTranslations('EventRequest');

  const variants: Record<EventRequestStatus, 'warning' | 'success' | 'danger' | 'default'> = {
    PENDING: 'warning',
    CHANGES_REQUESTED: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger',
    CANCELLED: 'default',
  };

  const labels: Record<EventRequestStatus, string> = {
    PENDING: t('pending'),
    CHANGES_REQUESTED: t('changesRequested'),
    APPROVED: t('approved'),
    REJECTED: t('rejected'),
    CANCELLED: t('cancelled'),
  };

  return (
    <Badge variant={variants[status]}>
      {status === 'CHANGES_REQUESTED' && '⚠️ '}
      {labels[status]}
    </Badge>
  );
}

export default function MyEventsPage() {
  const t = useTranslations('MyEvents');
  const tRequest = useTranslations('EventRequest');
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();

  const [myExhibitions, setMyExhibitions] = useState<MyExhibitions | null>(null);
  const [eventRequests, setEventRequests] = useState<EventRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch my exhibitions and event requests
  useEffect(() => {
    async function fetchData() {
      setIsLoading(true);

      const [exhibitionsResponse, requestsResponse] = await Promise.all([
        userApi.getMyExhibitions(),
        eventRequestsApi.listMy(),
      ]);

      if (exhibitionsResponse.data) {
        setMyExhibitions(exhibitionsResponse.data);
      }
      if (requestsResponse.data) {
        setEventRequests(requestsResponse.data);
      }

      setIsLoading(false);
    }

    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  if (authLoading || !isAuthenticated) {
    return null;
  }

  const hasOrganized = myExhibitions && myExhibitions.organized.length > 0;
  const hasRegistered = myExhibitions && myExhibitions.registered.length > 0;
  const hasRequests = eventRequests.length > 0;
  const hasAny = hasOrganized || hasRegistered || hasRequests;
  const hasNone = !hasAny;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {t('title')}
          </h1>
          <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
            {t('subtitle')}
          </p>
        </div>
        {user?.email_verified && (
          <Link href="/events/request">
            <Button variant="primary">{t('proposeEvent')}</Button>
          </Link>
        )}
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
            <div className="flex justify-center gap-4">
              <Link href="/exhibitions">
                <Button variant="secondary">{t('browseEvents')}</Button>
              </Link>
              {user?.email_verified && (
                <Link href="/events/request">
                  <Button variant="primary">{t('proposeEvent')}</Button>
                </Link>
              )}
            </div>
          </Card.Content>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* Event Requests */}
          {hasRequests && (
            <section>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                <span>📝</span>
                {t('requestsSection')}
              </h2>
              <div className="space-y-4">
                {eventRequests.map((request) => (
                  <Card key={request.id}>
                    <Card.Content>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                              {request.event_title}
                            </h3>
                            <RequestStatusBadge status={request.status as EventRequestStatus} />
                          </div>
                          <p className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                            {request.organization_name} • {request.event_city || tRequest('noCity')}
                          </p>
                          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                            {new Date(request.event_start_date).toLocaleDateString(locale)} - {new Date(request.event_end_date).toLocaleDateString(locale)}
                          </p>
                          {request.admin_comment && ['CHANGES_REQUESTED', 'REJECTED'].includes(request.status) && (
                            <div
                              className="mt-3 p-3 rounded-lg"
                              style={{ backgroundColor: 'var(--color-bg-secondary)' }}
                            >
                              <p className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>
                                {tRequest('adminComment')}
                              </p>
                              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                                {request.admin_comment}
                              </p>
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col gap-2">
                          {request.status === 'CHANGES_REQUESTED' && (
                            <Link href={`/my/event-requests/${request.id}/edit`}>
                              <Button variant="primary" size="sm">
                                {tRequest('editAndResubmit')}
                              </Button>
                            </Link>
                          )}
                          {request.status === 'APPROVED' && request.created_exhibition_id && (
                            <Link href={`/exhibitions/${request.created_exhibition_id}/manage`}>
                              <Button variant="primary" size="sm">
                                {tRequest('viewExhibition')}
                              </Button>
                            </Link>
                          )}
                          <Link href={`/my/event-requests/${request.id}/edit`}>
                            <Button variant="secondary" size="sm">
                              {tRequest('viewDetails')}
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </Card.Content>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Organized exhibitions */}
          {hasOrganized && (
            <section>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                <span>📋</span>
                {t('organizedSection')}
              </h2>
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
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                <span>🎮</span>
                {t('registeredSection')}
              </h2>
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
