'use client';

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { eventRequestsApi } from '@/lib/api';
import { Card, Badge, Button, Select, Input } from '@/components/ui';
import type { EventRequestStatus, EventRequestListResponse } from '@/lib/api/types';

const STATUS_TRANSLATION_KEYS: Record<EventRequestStatus, string> = {
  PENDING: 'pending',
  CHANGES_REQUESTED: 'changesRequested',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  CANCELLED: 'cancelled',
};

type SortField = 'created_at' | 'event_title' | 'organization_name';
type SortDirection = 'asc' | 'desc';

function StatusBadge({ status, t }: { status: EventRequestStatus; t: (key: string) => string }) {
  const variants: Record<EventRequestStatus, 'warning' | 'success' | 'danger' | 'default'> = {
    PENDING: 'warning',
    CHANGES_REQUESTED: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger',
    CANCELLED: 'default',
  };

  return (
    <Badge variant={variants[status]}>
      {status === 'CHANGES_REQUESTED' && '⚠️ '}
      {t(STATUS_TRANSLATION_KEYS[status])}
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
  const tEventRequest = useTranslations('EventRequest');
  const searchParams = useSearchParams();
  const statusFilter = (searchParams.get('status') as EventRequestStatus) || undefined;

  const [data, setData] = useState<EventRequestListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>(statusFilter || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

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

  // Filter and sort data
  const filteredAndSortedItems = useMemo(() => {
    if (!data?.items) return [];

    let items = [...data.items];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      items = items.filter((item) => {
        return (
          item.event_title.toLowerCase().includes(query) ||
          item.organization_name.toLowerCase().includes(query) ||
          (item.requester_name && item.requester_name.toLowerCase().includes(query)) ||
          (item.requester_email && item.requester_email.toLowerCase().includes(query)) ||
          (item.event_city && item.event_city.toLowerCase().includes(query))
        );
      });
    }

    // Sort
    items.sort((a, b) => {
      let valueA: string | number;
      let valueB: string | number;

      switch (sortField) {
        case 'event_title':
          valueA = a.event_title.toLowerCase();
          valueB = b.event_title.toLowerCase();
          break;
        case 'organization_name':
          valueA = a.organization_name.toLowerCase();
          valueB = b.organization_name.toLowerCase();
          break;
        case 'created_at':
        default:
          valueA = new Date(a.created_at).getTime();
          valueB = new Date(b.created_at).getTime();
          break;
      }

      if (valueA < valueB) return sortDirection === 'asc' ? -1 : 1;
      if (valueA > valueB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return items;
  }, [data?.items, searchQuery, sortField, sortDirection]);

  // Sortable column header component
  const SortableHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => {
    const isActive = sortField === field;
    return (
      <th
        className="text-left p-4 font-medium cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 select-none"
        style={{ color: 'var(--color-text-secondary)' }}
        onClick={() => {
          if (isActive) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
          } else {
            setSortField(field);
            setSortDirection('asc');
          }
        }}
      >
        <div className="flex items-center gap-1">
          {children}
          {isActive && (
            <span className="text-xs">
              {sortDirection === 'asc' ? '↑' : '↓'}
            </span>
          )}
        </div>
      </th>
    );
  };

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
          <div className="flex flex-col md:flex-row items-start md:items-end gap-4">
            {/* Search */}
            <div className="w-full md:w-64">
              <Input
                label={t('search')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('searchPlaceholder')}
              />
            </div>

            {/* Status filter */}
            <Select
              label={t('filterByStatus')}
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              options={[
                { value: '', label: t('allStatuses') },
                { value: 'PENDING', label: tEventRequest('pending') },
                { value: 'CHANGES_REQUESTED', label: tEventRequest('changesRequested') },
                { value: 'APPROVED', label: tEventRequest('approved') },
                { value: 'REJECTED', label: tEventRequest('rejected') },
              ]}
              className="w-full md:w-48"
            />

            {/* Sort */}
            <Select
              label={t('sortBy')}
              value={sortField}
              onChange={(e) => setSortField(e.target.value as SortField)}
              options={[
                { value: 'created_at', label: t('sortSubmittedDate') },
                { value: 'event_title', label: t('sortEventTitle') },
                { value: 'organization_name', label: t('sortOrganization') },
              ]}
              className="w-full md:w-48"
            />

            {/* Sort direction */}
            <Select
              label=" "
              value={sortDirection}
              onChange={(e) => setSortDirection(e.target.value as SortDirection)}
              options={[
                { value: 'desc', label: t('sortDesc') },
                { value: 'asc', label: t('sortAsc') },
              ]}
              className="w-full md:w-32"
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
      ) : filteredAndSortedItems.length === 0 ? (
        /* Empty state */
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {t('noEventRequests')}
            </h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              {selectedStatus || searchQuery ? t('noEventRequestsForStatus') : t('noEventRequestsYet')}
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
                    <SortableHeader field="event_title">
                      {t('eventTitle')}
                    </SortableHeader>
                    <SortableHeader field="organization_name">
                      {t('organization')}
                    </SortableHeader>
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
                    <SortableHeader field="created_at">
                      {t('submitted')}
                    </SortableHeader>
                    <th className="p-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAndSortedItems.map((request) => (
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
                        <StatusBadge status={request.status as EventRequestStatus} t={tEventRequest} />
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
