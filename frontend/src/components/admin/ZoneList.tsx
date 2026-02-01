'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { zonesApi, Zone, ZoneCreate } from '@/lib/api';
import { Button, Card, Badge, ConfirmDialog } from '@/components/ui';
import { ZoneForm } from './ZoneForm';
import { PhysicalTableList } from './PhysicalTableList';

interface ZoneListProps {
  exhibitionId: string;
}

const ZONE_TYPE_COLORS: Record<string, 'default' | 'success' | 'warning' | 'danger'> = {
  MIXED: 'default',
  RPG: 'success',
  BOARD_GAME: 'warning',
  WARGAME: 'danger',
  TCG: 'default',
  DEMO: 'default',
};

export function ZoneList({ exhibitionId }: ZoneListProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');

  const [zones, setZones] = useState<Zone[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingZone, setEditingZone] = useState<Zone | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [expandedZoneId, setExpandedZoneId] = useState<string | null>(null);
  const [deleteZone, setDeleteZone] = useState<Zone | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load zones
  useEffect(() => {
    async function loadZones() {
      setIsLoading(true);
      setError(null);

      const response = await zonesApi.list(exhibitionId);

      if (response.error) {
        setError(response.error.message);
      } else if (response.data) {
        setZones(response.data);
      }

      setIsLoading(false);
    }

    loadZones();
  }, [exhibitionId]);

  const handleCreate = async (data: ZoneCreate) => {
    setIsSubmitting(true);
    setError(null);

    const response = await zonesApi.create(data);

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setZones((prev) =>
        [...prev, response.data!].sort((a, b) => a.name.localeCompare(b.name))
      );
      setIsFormOpen(false);
    }

    setIsSubmitting(false);
  };

  const handleUpdate = async (data: ZoneCreate) => {
    if (!editingZone) return;

    setIsSubmitting(true);
    setError(null);

    const response = await zonesApi.update(editingZone.id, {
      name: data.name,
      description: data.description,
      type: data.type,
    });

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setZones((prev) =>
        prev
          .map((z) => (z.id === editingZone.id ? response.data! : z))
          .sort((a, b) => a.name.localeCompare(b.name))
      );
      setEditingZone(null);
    }

    setIsSubmitting(false);
  };

  const handleDelete = async () => {
    if (!deleteZone) return;

    setIsDeleting(true);
    setError(null);

    const response = await zonesApi.delete(deleteZone.id);

    if (response.error) {
      setError(response.error.message);
    } else {
      setZones((prev) => prev.filter((z) => z.id !== deleteZone.id));
      setDeleteZone(null);
      if (expandedZoneId === deleteZone.id) {
        setExpandedZoneId(null);
      }
    }

    setIsDeleting(false);
  };

  const toggleExpand = (zoneId: string) => {
    setExpandedZoneId((prev) => (prev === zoneId ? null : zoneId));
  };

  const openCreateForm = () => {
    setEditingZone(null);
    setIsFormOpen(true);
  };

  const openEditForm = (zone: Zone) => {
    setIsFormOpen(false);
    setEditingZone(zone);
  };

  const closeForm = () => {
    setIsFormOpen(false);
    setEditingZone(null);
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-20 bg-slate-200 dark:bg-slate-700 rounded"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Add button */}
      {!isFormOpen && !editingZone && (
        <div className="flex justify-end">
          <Button variant="primary" onClick={openCreateForm}>
            {t('addZone')}
          </Button>
        </div>
      )}

      {/* Create form */}
      {isFormOpen && (
        <Card>
          <Card.Content>
            <h4
              className="text-lg font-medium mb-4"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {t('addZone')}
            </h4>
            <ZoneForm
              exhibitionId={exhibitionId}
              onSubmit={handleCreate}
              onCancel={closeForm}
              isSubmitting={isSubmitting}
            />
          </Card.Content>
        </Card>
      )}

      {/* Zone list */}
      {zones.length === 0 && !isFormOpen ? (
        <div
          className="text-center py-8"
          style={{ color: 'var(--color-text-muted)' }}
        >
          {t('noZones')}
        </div>
      ) : (
        <div className="space-y-3">
          {zones.map((zone) => (
            <div key={zone.id}>
              {editingZone?.id === zone.id ? (
                <Card>
                  <Card.Content>
                    <h4
                      className="text-lg font-medium mb-4"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {t('editZone')}
                    </h4>
                    <ZoneForm
                      zone={zone}
                      exhibitionId={exhibitionId}
                      onSubmit={handleUpdate}
                      onCancel={closeForm}
                      isSubmitting={isSubmitting}
                    />
                  </Card.Content>
                </Card>
              ) : (
                <div
                  className="border rounded-lg overflow-hidden"
                  style={{ borderColor: 'var(--color-border)' }}
                >
                  {/* Zone header */}
                  <div
                    className="flex items-center justify-between p-4 cursor-pointer"
                    style={{ backgroundColor: 'var(--color-bg-secondary)' }}
                    onClick={() => toggleExpand(zone.id)}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="text-lg"
                        style={{ color: 'var(--color-text-muted)' }}
                      >
                        {expandedZoneId === zone.id ? '▼' : '▶'}
                      </span>
                      <div>
                        <div
                          className="font-medium"
                          style={{ color: 'var(--color-text-primary)' }}
                        >
                          {zone.name}
                        </div>
                        {zone.description && (
                          <div
                            className="text-sm"
                            style={{ color: 'var(--color-text-secondary)' }}
                          >
                            {zone.description}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={ZONE_TYPE_COLORS[zone.type]}>
                        {zone.type}
                      </Badge>
                      <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => openEditForm(zone)}
                        >
                          {tCommon('edit')}
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => setDeleteZone(zone)}
                        >
                          {tCommon('delete')}
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Tables section (expanded) */}
                  {expandedZoneId === zone.id && (
                    <div
                      className="p-4 border-t"
                      style={{ borderColor: 'var(--color-border)' }}
                    >
                      <h5
                        className="font-medium mb-3"
                        style={{ color: 'var(--color-text-primary)' }}
                      >
                        {t('tables')}
                      </h5>
                      <PhysicalTableList zoneId={zone.id} />
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        isOpen={!!deleteZone}
        title={t('confirmDeleteZoneTitle')}
        message={t('confirmDeleteZoneMessage', { name: deleteZone?.name })}
        confirmLabel={tCommon('delete')}
        cancelLabel={tCommon('cancel')}
        variant="danger"
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onClose={() => setDeleteZone(null)}
      />
    </div>
  );
}
