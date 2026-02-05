'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useRouter, Link } from '@/i18n/routing';
import { eventRequestsApi } from '@/lib/api';
import { Button, Card, Badge, ModerationDialog } from '@/components/ui';
import type { EventRequest, EventRequestStatus } from '@/lib/api/types';

const STATUS_TRANSLATION_KEYS: Record<EventRequestStatus, string> = {
  PENDING: 'pending',
  CHANGES_REQUESTED: 'changesRequested',
  APPROVED: 'approved',
  REJECTED: 'rejected',
};

function StatusBadge({ status, t }: { status: EventRequestStatus; t: (key: string) => string }) {
  const variants: Record<EventRequestStatus, 'warning' | 'success' | 'danger' | 'default'> = {
    PENDING: 'warning',
    CHANGES_REQUESTED: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger',
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
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AdminEventRequestDetailPage() {
  const t = useTranslations('Admin');
  const tRequest = useTranslations('EventRequest');
  const router = useRouter();
  const params = useParams();
  const requestId = params.id as string;

  const [request, setRequest] = useState<EventRequest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Moderation dialog state
  const [moderationDialog, setModerationDialog] = useState<{
    open: boolean;
    action: 'approve' | 'reject' | 'request_changes';
  }>({ open: false, action: 'approve' });

  // Fetch request
  useEffect(() => {
    async function fetchRequest() {
      setIsLoading(true);
      const response = await eventRequestsApi.getById(requestId);
      if (response.error) {
        setError(response.error.detail || response.error.message);
      } else if (response.data) {
        setRequest(response.data);
      }
      setIsLoading(false);
    }

    fetchRequest();
  }, [requestId]);

  // Handle review action
  const handleReview = async (action: 'approve' | 'reject' | 'request_changes', comment?: string) => {
    setIsProcessing(true);
    setError(null);

    const response = await eventRequestsApi.review(requestId, {
      action,
      admin_comment: comment,
    });

    if (response.error) {
      setError(response.error.detail || response.error.message);
      setIsProcessing(false);
    } else if (response.data) {
      setRequest(response.data);
      setIsProcessing(false);
      setModerationDialog({ open: false, action: 'approve' });

      // Redirect to list after approval
      if (action === 'approve') {
        router.push('/admin/event-requests');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary" />
      </div>
    );
  }

  if (error && !request) {
    return (
      <Card>
        <Card.Content className="text-center py-12">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
            {t('error')}
          </h2>
          <p className="mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            {error}
          </p>
          <Link href="/admin/event-requests">
            <Button variant="primary">{t('backToList')}</Button>
          </Link>
        </Card.Content>
      </Card>
    );
  }

  if (!request) {
    return null;
  }

  const canReview = request.status === 'PENDING' || request.status === 'CHANGES_REQUESTED';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
              {request.event_title}
            </h1>
            <StatusBadge status={request.status as EventRequestStatus} t={tRequest} />
          </div>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            {t('submittedBy')} {request.requester_name || request.requester_email} {t('on')}{' '}
            {formatDate(request.created_at)}
          </p>
        </div>
        <Link href="/admin/event-requests">
          <Button variant="secondary">{t('backToList')}</Button>
        </Link>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Requester message */}
      {request.requester_message && (
        <Card>
          <Card.Header>
            <Card.Title>{t('requesterMessage')}</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="whitespace-pre-wrap" style={{ color: 'var(--color-text-secondary)' }}>{request.requester_message}</p>
          </Card.Content>
        </Card>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {/* Event Details */}
        <Card>
          <Card.Header>
            <Card.Title>{tRequest('eventInfo')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('eventTitle')}
              </p>
              <p style={{ color: 'var(--color-text-primary)' }}>{request.event_title}</p>
            </div>

            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('slug')}
              </p>
              <p style={{ color: 'var(--color-text-secondary)' }}>{request.event_slug}</p>
            </div>

            {request.event_description && (
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                  {t('description')}
                </p>
                <p className="whitespace-pre-wrap" style={{ color: 'var(--color-text-secondary)' }}>{request.event_description}</p>
              </div>
            )}

            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('eventDates')}
              </p>
              <p style={{ color: 'var(--color-text-primary)' }}>
                {formatDate(request.event_start_date)} - {formatDate(request.event_end_date)}
              </p>
            </div>

            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('location')}
              </p>
              <p style={{ color: 'var(--color-text-secondary)' }}>
                {request.event_location_name || '-'}
                {request.event_city && `, ${request.event_city}`}
                {request.event_region && ` (${request.event_region})`}
              </p>
            </div>

            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('timezone')}
              </p>
              <p style={{ color: 'var(--color-text-secondary)' }}>{request.event_timezone}</p>
            </div>
          </Card.Content>
        </Card>

        {/* Organization Details */}
        <Card>
          <Card.Header>
            <Card.Title>{tRequest('organizationInfo')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('organizationName')}
              </p>
              <p style={{ color: 'var(--color-text-primary)' }}>{request.organization_name}</p>
            </div>

            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('slug')}
              </p>
              <p style={{ color: 'var(--color-text-secondary)' }}>{request.organization_slug}</p>
            </div>

            {request.organization_contact_email && (
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                  {t('contactEmail')}
                </p>
                <p style={{ color: 'var(--color-text-secondary)' }}>
                  {request.organization_contact_email}
                </p>
              </div>
            )}

            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {t('requester')}
              </p>
              <p style={{ color: 'var(--color-text-primary)' }}>
                {request.requester_name || '-'}
              </p>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                {request.requester_email}
              </p>
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Review history */}
      {request.reviewed_at && (
        <Card>
          <Card.Header>
            <Card.Title>{t('reviewHistory')}</Card.Title>
          </Card.Header>
          <Card.Content>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              {t('reviewedOn')} {formatDate(request.reviewed_at)}
            </p>
            {request.admin_comment && (
              <div className="mt-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
                <p className="font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>
                  {t('adminComment')}
                </p>
                <p className="whitespace-pre-wrap" style={{ color: 'var(--color-text-secondary)' }}>{request.admin_comment}</p>
              </div>
            )}
          </Card.Content>
        </Card>
      )}

      {/* Approved result */}
      {request.status === 'APPROVED' && request.created_exhibition_id && (
        <Card>
          <Card.Content>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                  {t('exhibitionCreated')}
                </p>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  {t('exhibitionCreatedDescription')}
                </p>
              </div>
              <Link href={`/exhibitions/${request.created_exhibition_id}/manage`}>
                <Button variant="primary">{t('viewExhibition')}</Button>
              </Link>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Actions */}
      {canReview && (
        <Card>
          <Card.Header>
            <Card.Title>{t('reviewActions')}</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="flex gap-4">
              <Button
                variant="primary"
                onClick={() => setModerationDialog({ open: true, action: 'approve' })}
                disabled={isProcessing}
              >
                {t('approveRequest')}
              </Button>
              {request.status === 'PENDING' && (
                <Button
                  variant="secondary"
                  onClick={() => setModerationDialog({ open: true, action: 'request_changes' })}
                  disabled={isProcessing}
                >
                  {t('requestChanges')}
                </Button>
              )}
              <Button
                variant="danger"
                onClick={() => setModerationDialog({ open: true, action: 'reject' })}
                disabled={isProcessing}
              >
                {t('rejectRequest')}
              </Button>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Moderation dialog */}
      <ModerationDialog
        isOpen={moderationDialog.open}
        onClose={() => setModerationDialog({ open: false, action: 'approve' })}
        onConfirm={(reason) => handleReview(moderationDialog.action, reason)}
        title={
          moderationDialog.action === 'approve'
            ? t('confirmApprove')
            : moderationDialog.action === 'reject'
              ? t('confirmReject')
              : t('confirmRequestChanges')
        }
        message={
          moderationDialog.action === 'approve'
            ? t('confirmApproveDescription')
            : moderationDialog.action === 'reject'
              ? t('confirmRejectDescription')
              : t('confirmRequestChangesDescription')
        }
        sessionTitle={request.event_title}
        action={moderationDialog.action}
        confirmLabel={
          moderationDialog.action === 'approve'
            ? t('approveRequest')
            : moderationDialog.action === 'reject'
              ? t('rejectRequest')
              : t('requestChanges')
        }
        cancelLabel={tRequest('cancel')}
        reasonLabel={t('adminCommentLabel')}
        reasonPlaceholder={t('adminCommentLabel')}
        isLoading={isProcessing}
      />
    </div>
  );
}
