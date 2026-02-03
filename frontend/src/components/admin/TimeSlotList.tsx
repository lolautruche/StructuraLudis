'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { zonesApi, TimeSlot, TimeSlotCreate } from '@/lib/api';
import { Button, Card, ConfirmDialog } from '@/components/ui';
import { TimeSlotForm } from './TimeSlotForm';

interface TimeSlotListProps {
  zoneId: string;
  /** Exhibition start date for time slot defaults and constraints */
  exhibitionStartDate?: string;
  /** Exhibition end date for time slot constraints */
  exhibitionEndDate?: string;
}

function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}min`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h${mins}`;
}

export function TimeSlotList({ zoneId, exhibitionStartDate, exhibitionEndDate }: TimeSlotListProps) {
  const t = useTranslations('Admin');
  const tCommon = useTranslations('Common');

  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState<TimeSlot | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [deleteSlot, setDeleteSlot] = useState<TimeSlot | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load slots for this zone (#105)
  useEffect(() => {
    async function loadSlots() {
      setIsLoading(true);
      setError(null);

      const response = await zonesApi.getTimeSlots(zoneId);

      if (response.error) {
        setError(response.error.message);
      } else if (response.data) {
        setSlots(response.data);
      }

      setIsLoading(false);
    }

    loadSlots();
  }, [zoneId]);

  const handleCreate = async (data: TimeSlotCreate) => {
    setIsSubmitting(true);
    setError(null);

    const response = await zonesApi.createTimeSlot(zoneId, data);

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setSlots((prev) =>
        [...prev, response.data!].sort(
          (a, b) =>
            new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        )
      );
      setIsFormOpen(false);
    }

    setIsSubmitting(false);
  };

  const handleUpdate = async (data: TimeSlotCreate) => {
    if (!editingSlot) return;

    setIsSubmitting(true);
    setError(null);

    const response = await zonesApi.updateTimeSlot(
      zoneId,
      editingSlot.id,
      data
    );

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setSlots((prev) =>
        prev
          .map((s) => (s.id === editingSlot.id ? response.data! : s))
          .sort(
            (a, b) =>
              new Date(a.start_time).getTime() -
              new Date(b.start_time).getTime()
          )
      );
      setEditingSlot(null);
    }

    setIsSubmitting(false);
  };

  const handleDelete = async () => {
    if (!deleteSlot) return;

    setIsDeleting(true);
    setError(null);

    const response = await zonesApi.deleteTimeSlot(
      zoneId,
      deleteSlot.id
    );

    if (response.error) {
      setError(response.error.message);
    } else {
      setSlots((prev) => prev.filter((s) => s.id !== deleteSlot.id));
      setDeleteSlot(null);
    }

    setIsDeleting(false);
  };

  const openCreateForm = () => {
    setEditingSlot(null);
    setIsFormOpen(true);
  };

  const openEditForm = (slot: TimeSlot) => {
    setIsFormOpen(false);
    setEditingSlot(slot);
  };

  const closeForm = () => {
    setIsFormOpen(false);
    setEditingSlot(null);
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 bg-slate-200 dark:bg-slate-700 rounded"
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
      {!isFormOpen && !editingSlot && (
        <div className="flex justify-end">
          <Button variant="primary" onClick={openCreateForm}>
            {t('addSlot')}
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
              {t('addSlot')}
            </h4>
            <TimeSlotForm
              onSubmit={handleCreate}
              onCancel={closeForm}
              isSubmitting={isSubmitting}
              exhibitionStartDate={exhibitionStartDate}
              exhibitionEndDate={exhibitionEndDate}
            />
          </Card.Content>
        </Card>
      )}

      {/* Slot list */}
      {slots.length === 0 && !isFormOpen ? (
        <div
          className="text-center py-8"
          style={{ color: 'var(--color-text-muted)' }}
        >
          {t('noSlots')}
        </div>
      ) : (
        <div className="space-y-3">
          {slots.map((slot) => (
            <div key={slot.id}>
              {editingSlot?.id === slot.id ? (
                <Card>
                  <Card.Content>
                    <h4
                      className="text-lg font-medium mb-4"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {t('editSlot')}
                    </h4>
                    <TimeSlotForm
                      slot={slot}
                      onSubmit={handleUpdate}
                      onCancel={closeForm}
                      isSubmitting={isSubmitting}
                      exhibitionStartDate={exhibitionStartDate}
                      exhibitionEndDate={exhibitionEndDate}
                    />
                  </Card.Content>
                </Card>
              ) : (
                <div
                  className="flex items-center justify-between p-4 rounded-lg border"
                  style={{
                    borderColor: 'var(--color-border)',
                    backgroundColor: 'var(--color-bg-secondary)',
                  }}
                >
                  <div className="flex-1">
                    <div
                      className="font-medium"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {slot.name}
                    </div>
                    <div
                      className="text-sm"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {formatDateTime(slot.start_time)} -{' '}
                      {formatDateTime(slot.end_time)}
                    </div>
                    <div
                      className="text-xs mt-1"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      {t('maxDurationValue', {
                        duration: formatDuration(slot.max_duration_minutes),
                      })}{' '}
                      &bull;{' '}
                      {t('bufferTimeValue', {
                        duration: formatDuration(slot.buffer_time_minutes),
                      })}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openEditForm(slot)}
                    >
                      {tCommon('edit')}
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => setDeleteSlot(slot)}
                    >
                      {tCommon('delete')}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        isOpen={!!deleteSlot}
        title={t('confirmDeleteSlotTitle')}
        message={t('confirmDeleteSlotMessage', { name: deleteSlot?.name })}
        confirmLabel={tCommon('delete')}
        cancelLabel={tCommon('cancel')}
        variant="danger"
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onClose={() => setDeleteSlot(null)}
      />
    </div>
  );
}
