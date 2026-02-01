'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { Link } from '@/i18n/routing';
import { adminApi, Exhibition, ExhibitionStatus } from '@/lib/api';
import { Card, Select, Badge, Button } from '@/components/ui';

const STATUS_OPTIONS: ExhibitionStatus[] = ['DRAFT', 'PUBLISHED', 'ARCHIVED'];

const STATUS_COLORS: Record<ExhibitionStatus, 'warning' | 'success' | 'default'> = {
  DRAFT: 'warning',
  PUBLISHED: 'success',
  ARCHIVED: 'default',
};

export default function AdminExhibitionsPage() {
  const t = useTranslations('SuperAdmin.exhibitionManagement');
  const searchParams = useSearchParams();

  const [exhibitions, setExhibitions] = useState<Exhibition[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>(
    searchParams.get('status') || ''
  );

  const loadExhibitions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const params: { status?: string } = {};
    if (statusFilter) params.status = statusFilter;

    const response = await adminApi.listExhibitions(params);

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setExhibitions(response.data);
    }

    setIsLoading(false);
  }, [statusFilter]);

  useEffect(() => {
    loadExhibitions();
  }, [loadExhibitions]);

  const statusOptions = [
    { value: '', label: t('allStatuses') },
    ...STATUS_OPTIONS.map((status) => ({ value: status, label: status })),
  ];

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
      <div className="flex items-center justify-between">
        <h2
          className="text-xl font-semibold"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('title')}
        </h2>
        <Link href="/admin/exhibitions/create">
          <Button>{t('createNew')}</Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="w-48">
          <Select
            options={statusOptions}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          />
        </div>
      </div>

      {/* Exhibitions list */}
      <Card>
        <Card.Content className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 rounded"
                  style={{ backgroundColor: 'var(--color-bg-secondary)' }}
                />
              ))}
            </div>
          ) : exhibitions.length === 0 ? (
            <div className="p-6 text-center">
              <p style={{ color: 'var(--color-text-muted)' }}>
                {t('noExhibitions')}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr
                    className="border-b"
                    style={{ borderColor: 'var(--color-border)' }}
                  >
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('exhibitionTitle')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('dates')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('location')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('status')}
                    </th>
                    <th
                      className="text-right p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('actions')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {exhibitions.map((exhibition) => (
                    <tr
                      key={exhibition.id}
                      className="border-b last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      style={{ borderColor: 'var(--color-border)' }}
                    >
                      <td className="p-4">
                        <span
                          className="font-medium"
                          style={{ color: 'var(--color-text-primary)' }}
                        >
                          {exhibition.title}
                        </span>
                        <span
                          className="block text-sm"
                          style={{ color: 'var(--color-text-muted)' }}
                        >
                          /{exhibition.slug}
                        </span>
                      </td>
                      <td className="p-4">
                        <span style={{ color: 'var(--color-text-secondary)' }}>
                          {new Date(exhibition.start_date).toLocaleDateString()}{' '}
                          - {new Date(exhibition.end_date).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="p-4">
                        <span style={{ color: 'var(--color-text-secondary)' }}>
                          {exhibition.city || '-'}
                        </span>
                      </td>
                      <td className="p-4">
                        <Badge variant={STATUS_COLORS[exhibition.status]}>
                          {exhibition.status}
                        </Badge>
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex justify-end gap-2">
                          <Link href={`/exhibitions/${exhibition.id}`}>
                            <Button variant="ghost" size="sm">
                              {t('view')}
                            </Button>
                          </Link>
                          <Link href={`/exhibitions/${exhibition.id}/manage`}>
                            <Button variant="secondary" size="sm">
                              {t('manage')}
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
