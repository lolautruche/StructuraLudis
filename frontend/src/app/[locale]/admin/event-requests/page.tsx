'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { eventRequestsApi } from '@/lib/api';
import { Card, Badge, Button, Select } from '@/components/ui';
import type { EventRequestStatus, EventRequestListResponse } from '@/lib/api/types';

function StatusBadge({ status }: { status: EventRequestStatus }) {
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

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function AdminEventRequestsPage() {
  const t = useTranslations('Admin');
  const searchParams = useSearchParams();
  const statusFilter = (searchParams.get('status') as EventRequestStatus) || undefined;

  const [data, setData] = useState<EventRequestListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>(statusFilter || '');

  // Fetch requests
  useEffect(() => {
    async function fetchRequests() {
      setIsLoading(true);
      setError(null);

      const response = await eventRequestsApi.list({
        status: selectedStatus as EventRequestStatus || undefined,
      });

      if (response.error) {
        setError(response.error.detail || response.error.message);
      } else if (response.data) {
        setData(response.data);
      }
      setIsLoading(false);
    }

    fetchRequests();
  }, [selectedStatus]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {t('eventRequests')}
          </h1>
          {data && (
            <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              {data.pending_count} {t('pendingRequests')}
            </p>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <Card.Content>
          <div className="flex items-center gap-4">
            <Select
              label={t('filterByStatus')}
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              options={[
                { value: '', label: t('allStatuses') },
                { value: 'PENDING', label: 'Pending' },
                { value: 'CHANGES_REQUESTED', label: 'Changes Requested' },
                { value: 'APPROVED', label: 'Approved' },
                { value: 'REJECTED', label: 'Rejected' },
              ]}
              className="w-48"
            />
          </div>
        </Card.Content>
      </Card>

      {/* Error state */}
      {error && (
        <Card>
          <Card.Content>
            <p style={{ color: 'var(--color-text-danger)' }}>{error}</p>
          </Card.Content>
        </Card>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <Card.Content className="space-y-4">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full" />
              </Card.Content>
            </Card>
          ))}
        </div>
      ) : data && data.items.length === 0 ? (
        /* Empty state */
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {t('noEventRequests')}
            </h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              {selectedStatus ? t('noEventRequestsForStatus') : t('noEventRequestsYet')}
            </p>
          </Card.Content>
        </Card>
      ) : (
        /* Requests table */
        <Card>
          <Card.Content className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('eventTitle')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('organization')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('requester')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('eventDates')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('status')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('submitted')}
                    </th>
                    <th className="p-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((request) => (
                    <tr
                      key={request.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      style={{ borderBottom: '1px solid var(--color-border)' }}
                    >
                      <td className="p-4">
                        <div>
                          <p
                            className="font-medium"
                            style={{ color: 'var(--color-text-primary)' }}
                          >
                            {request.event_title}
                          </p>
                          {request.event_city && (
                            <p
                              className="text-sm"
                              style={{ color: 'var(--color-text-muted)' }}
                            >
                              {request.event_city}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="p-4" style={{ color: 'var(--color-text-secondary)' }}>
                        {request.organization_name}
                      </td>
                      <td className="p-4">
                        <div>
                          <p style={{ color: 'var(--color-text-primary)' }}>
                            {request.requester_name || '-'}
                          </p>
                          <p
                            className="text-sm"
                            style={{ color: 'var(--color-text-muted)' }}
                          >
                            {request.requester_email}
                          </p>
                        </div>
                      </td>
                      <td className="p-4" style={{ color: 'var(--color-text-secondary)' }}>
                        {formatDate(request.event_start_date)} - {formatDate(request.event_end_date)}
                      </td>
                      <td className="p-4">
                        <StatusBadge status={request.status as EventRequestStatus} />
                      </td>
                      <td className="p-4" style={{ color: 'var(--color-text-muted)' }}>
                        {formatDate(request.created_at)}
                      </td>
                      <td className="p-4">
                        <Link href={`/admin/event-requests/${request.id}`}>
                          <Button variant="secondary" size="sm">
                            {t('view')}
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card.Content>
        </Card>
      )}
    </div>
  );
}
