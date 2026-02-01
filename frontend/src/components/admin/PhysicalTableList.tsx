'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { zonesApi, PhysicalTable } from '@/lib/api';
import { Button, Badge, ConfirmDialog } from '@/components/ui';
import { BatchTableCreator } from './BatchTableCreator';

interface PhysicalTableListProps {
  zoneId: string;
}

const STATUS_COLORS: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
  AVAILABLE: 'success',
  OCCUPIED: 'warning',
  RESERVED: 'default',
  MAINTENANCE: 'danger',
};

export function PhysicalTableList({ zoneId }: PhysicalTableListProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');

  const [tables, setTables] = useState<PhysicalTable[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showBatchCreator, setShowBatchCreator] = useState(false);
  const [deleteTable, setDeleteTable] = useState<PhysicalTable | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load tables
  useEffect(() => {
    async function loadTables() {
      setIsLoading(true);
      setError(null);

      const response = await zonesApi.getTables(zoneId);

      if (response.error) {
        setError(response.error.message);
      } else if (response.data) {
        setTables(response.data);
      }

      setIsLoading(false);
    }

    loadTables();
  }, [zoneId]);

  const handleTablesCreated = (newTables: PhysicalTable[]) => {
    setTables((prev) =>
      [...prev, ...newTables].sort((a, b) => a.label.localeCompare(b.label))
    );
    setShowBatchCreator(false);
  };

  const handleDelete = async () => {
    if (!deleteTable) return;

    setIsDeleting(true);
    setError(null);

    const response = await zonesApi.deleteTable(zoneId, deleteTable.id);

    if (response.error) {
      setError(response.error.message);
    } else {
      setTables((prev) => prev.filter((t) => t.id !== deleteTable.id));
      setDeleteTable(null);
    }

    setIsDeleting(false);
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-10 bg-slate-200 dark:bg-slate-700 rounded"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Batch creator */}
      {showBatchCreator ? (
        <div
          className="p-4 border rounded-lg"
          style={{ borderColor: 'var(--color-border)' }}
        >
          <h5
            className="font-medium mb-3"
            style={{ color: 'var(--color-text-primary)' }}
          >
            {t('addTables')}
          </h5>
          <BatchTableCreator
            zoneId={zoneId}
            onTablesCreated={handleTablesCreated}
            onCancel={() => setShowBatchCreator(false)}
          />
        </div>
      ) : (
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setShowBatchCreator(true)}
        >
          {t('addTables')}
        </Button>
      )}

      {/* Table list */}
      {tables.length === 0 ? (
        <div
          className="text-sm py-4 text-center"
          style={{ color: 'var(--color-text-muted)' }}
        >
          {t('noTables')}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {tables.map((table) => (
            <div
              key={table.id}
              className="flex items-center justify-between p-2 rounded border text-sm"
              style={{
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-bg-secondary)',
              }}
            >
              <div>
                <span
                  className="font-medium"
                  style={{ color: 'var(--color-text-primary)' }}
                >
                  {table.label}
                </span>
                <span
                  className="ml-2 text-xs"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  ({table.capacity})
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={STATUS_COLORS[table.status]} size="sm">
                  {table.status}
                </Badge>
                <button
                  onClick={() => setDeleteTable(table)}
                  className="text-red-500 hover:text-red-700 text-xs"
                  title={tCommon('delete')}
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        isOpen={!!deleteTable}
        title={t('confirmDeleteTableTitle')}
        message={t('confirmDeleteTableMessage', { label: deleteTable?.label })}
        confirmLabel={tCommon('delete')}
        cancelLabel={tCommon('cancel')}
        variant="danger"
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onClose={() => setDeleteTable(null)}
      />
    </div>
  );
}
