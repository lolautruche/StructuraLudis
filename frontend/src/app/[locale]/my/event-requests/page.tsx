'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter, Link } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { eventRequestsApi } from '@/lib/api';
import { Button, Card, Badge } from '@/components/ui';
import type { EventRequest, EventRequestStatus } from '@/lib/api/types';

function StatusBadge({ status }: { status: EventRequestStatus }) {
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

function formatDate(dateStr: string, locale: string) {
  return new Date(dateStr).toLocaleDateString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function MyEventRequestsPage() {
  const t = useTranslations('EventRequest');
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [requests, setRequests] = useState<EventRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showArchived, setShowArchived] = useState(false);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch my requests
  useEffect(() => {
    async function fetchRequests() {
      setIsLoading(true);
      const response = await eventRequestsApi.listMy();
      if (response.data) {
        setRequests(response.data);
      }
      setIsLoading(false);
    }

    if (isAuthenticated) {
      fetchRequests();
    }
  }, [isAuthenticated]);

  // Handle cancel request
  const handleCancel = async (id: string) => {
    if (!confirm(t('confirmCancel'))) return;

    setCancellingId(id);
    const response = await eventRequestsApi.cancel(id);
    if (response.data) {
      setRequests(requests.map(r => r.id === id ? response.data! : r));
    }
    setCancellingId(null);
  };

  // Filter requests based on showArchived toggle
  const filteredRequests = showArchived
    ? requests
    : requests.filter(r => !['CANCELLED', 'REJECTED'].includes(r.status));

  const archivedCount = requests.filter(r => ['CANCELLED', 'REJECTED'].includes(r.status)).length;

  if (authLoading || !isAuthenticated) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {t('myRequests')}
          </h1>
          <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
            {t('myRequestsSubtitle')}
          </p>
        </div>
        <Link href="/events/request">
          <Button variant="primary">{t('newRequest')}</Button>
        </Link>
      </div>

      {/* Filter toggle */}
      {archivedCount > 0 && (
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
              className="rounded border-gray-300 text-ludis-primary focus:ring-ludis-primary"
            />
            <span style={{ color: 'var(--color-text-secondary)' }}>
              {t('showArchived', { count: archivedCount })}
            </span>
          </label>
        </div>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <Card.Content className="space-y-4">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full" />
              </Card.Content>
            </Card>
          ))}
        </div>
      ) : filteredRequests.length === 0 ? (
        /* Empty state */
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {t('noRequests')}
            </h3>
            <p className="mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              {t('noRequestsDescription')}
            </p>
            <Link href="/events/request">
              <Button variant="primary">{t('createRequest')}</Button>
            </Link>
          </Card.Content>
        </Card>
      ) : (
        /* Requests list */
        <div className="space-y-4">
          {filteredRequests.map((request) => (
            <Card key={request.id}>
              <Card.Content>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                        {request.event_title}
                      </h3>
                      <StatusBadge status={request.status as EventRequestStatus} />
                    </div>
                    <p className="text-sm mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                      {request.organization_name} • {request.event_city || t('noCity')}
                    </p>
                    <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                      {formatDate(request.event_start_date, 'fr')} - {formatDate(request.event_end_date, 'fr')}
                    </p>

                    {/* Admin comment for CHANGES_REQUESTED or REJECTED */}
                    {request.admin_comment && ['CHANGES_REQUESTED', 'REJECTED'].includes(request.status) && (
                      <div
                        className="mt-4 p-3 rounded-lg"
                        style={{ backgroundColor: 'var(--color-bg-secondary)' }}
                      >
                        <p className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>
                          {t('adminComment')}
                        </p>
                        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                          {request.admin_comment}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2">
                    {request.status === 'CHANGES_REQUESTED' && (
                      <Link href={`/my/event-requests/${request.id}/edit`}>
                        <Button variant="primary" size="sm">
                          {t('editAndResubmit')}
                        </Button>
                      </Link>
                    )}
                    {request.status === 'APPROVED' && request.created_exhibition_id && (
                      <Link href={`/exhibitions/${request.created_exhibition_id}/manage`}>
                        <Button variant="primary" size="sm">
                          {t('manageExhibition')}
                        </Button>
                      </Link>
                    )}
                    {!['APPROVED', 'CANCELLED'].includes(request.status) && (
                      <Link href={`/my/event-requests/${request.id}/edit`}>
                        <Button variant="secondary" size="sm">
                          {t('viewDetails')}
                        </Button>
                      </Link>
                    )}
                    {['PENDING', 'CHANGES_REQUESTED'].includes(request.status) && (
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleCancel(request.id)}
                        disabled={cancellingId === request.id}
                      >
                        {cancellingId === request.id ? t('cancelling') : t('cancelRequest')}
                      </Button>
                    )}
                  </div>
                </div>
              </Card.Content>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
