'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { partnerApi, sessionsApi, PartnerSession, PartnerZone, SessionStatus } from '@/lib/api';
import { Badge, Button, Select, Card, ModerationDialog, ModerationAction } from '@/components/ui';
import { Link } from '@/i18n/routing';
import { useToast } from '@/contexts/ToastContext';
import { SeriesCreator } from './SeriesCreator';
import { SingleSessionCreator } from './SingleSessionCreator';

interface PartnerSessionListProps {
  exhibitionId: string;
}

const STATUS_FILTERS: { value: SessionStatus | 'ALL'; labelKey: string }[] = [
  { value: 'ALL', labelKey: 'allStatuses' },
  { value: 'DRAFT', labelKey: 'draft' },
  { value: 'PENDING_MODERATION', labelKey: 'pendingModeration' },
  { value: 'VALIDATED', labelKey: 'validated' },
  { value: 'CHANGES_REQUESTED', labelKey: 'changesRequested' },
  { value: 'REJECTED', labelKey: 'rejected' },
  { value: 'IN_PROGRESS', labelKey: 'inProgress' },
  { value: 'FINISHED', labelKey: 'finished' },
];

interface ModerationDialogState {
  isOpen: boolean;
  action: ModerationAction;
  sessionId: string;
  sessionTitle: string;
}

export function PartnerSessionList({ exhibitionId }: PartnerSessionListProps) {
  const t = useTranslations('Partner');
  const tSession = useTranslations('Sessions');
  const tCommon = useTranslations('Common');
  const { showError } = useToast();

  const [sessions, setSessions] = useState<PartnerSession[]>([]);
  const [zones, setZones] = useState<PartnerZone[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<SessionStatus | 'ALL'>('ALL');
  const [zoneFilter, setZoneFilter] = useState<string>('ALL');
  const [showSeriesCreator, setShowSeriesCreator] = useState(false);
  const [showSingleSessionCreator, setShowSingleSessionCreator] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [moderationDialog, setModerationDialog] = useState<ModerationDialogState>({
    isOpen: false,
    action: 'submit',
    sessionId: '',
    sessionTitle: '',
  });
  const { showSuccess } = useToast();

  // Load zones for the filter dropdown
  useEffect(() => {
    async function loadZones() {
      const response = await partnerApi.listZones(exhibitionId);
      if (response.data) {
        setZones(response.data);
      }
    }
    loadZones();
  }, [exhibitionId]);

  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    const response = await partnerApi.listSessions(exhibitionId, {
      status: statusFilter === 'ALL' ? undefined : statusFilter,
      zoneId: zoneFilter === 'ALL' ? undefined : zoneFilter,
    });

    if (response.error) {
      showError(response.error.message);
    } else if (response.data) {
      setSessions(response.data);
    }
    setIsLoading(false);
  }, [exhibitionId, statusFilter, zoneFilter, showError]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const getStatusBadgeVariant = (status: SessionStatus) => {
    switch (status) {
      case 'DRAFT':
        return 'default';
      case 'VALIDATED':
        return 'success';
      case 'PENDING_MODERATION':
        return 'warning';
      case 'CHANGES_REQUESTED':
        return 'warning';
      case 'REJECTED':
        return 'danger';
      case 'IN_PROGRESS':
        return 'info';
      case 'FINISHED':
        return 'default';
      case 'CANCELLED':
        return 'danger';
      default:
        return 'default';
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="animate-pulse h-24 bg-slate-200 dark:bg-slate-700 rounded"
          />
        ))}
      </div>
    );
  }

  const handleSeriesCreated = () => {
    setShowSeriesCreator(false);
    loadSessions();
  };

  const handleSingleSessionCreated = () => {
    setShowSingleSessionCreator(false);
    loadSessions();
  };

  const openModerationDialog = (action: ModerationAction, sessionId: string, sessionTitle: string) => {
    setModerationDialog({
      isOpen: true,
      action,
      sessionId,
      sessionTitle,
    });
  };

  const closeModerationDialog = () => {
    setModerationDialog((prev) => ({ ...prev, isOpen: false }));
  };

  const handleModerationConfirm = async (reason?: string) => {
    const { action, sessionId } = moderationDialog;
    setIsProcessing(true);

    let response;

    if (action === 'submit') {
      response = await sessionsApi.submit(sessionId);
      if (!response.error) {
        showSuccess(t('sessionSubmitted'));
      }
    } else if (action === 'approve') {
      response = await sessionsApi.moderate(sessionId, { action: 'approve' });
      if (!response.error) {
        showSuccess(t('sessionApproved'));
      }
    } else if (action === 'reject') {
      response = await sessionsApi.moderate(sessionId, {
        action: 'reject',
        rejection_reason: reason || '',
      });
      if (!response.error) {
        showSuccess(t('sessionRejected'));
      }
    } else if (action === 'request_changes') {
      response = await sessionsApi.moderate(sessionId, {
        action: 'request_changes',
        comment: reason || '',
      });
      if (!response.error) {
        showSuccess(t('changesRequested'));
      }
    }

    if (response?.error) {
      showError(response.error.message);
    } else {
      closeModerationDialog();
      loadSessions();
    }

    setIsProcessing(false);
  };

  const getModerationDialogContent = () => {
    const { action } = moderationDialog;
    switch (action) {
      case 'submit':
        return {
          title: t('confirmSubmit'),
          message: t('confirmSubmitMessage'),
          confirmLabel: t('submit'),
        };
      case 'approve':
        return {
          title: t('confirmApprove'),
          message: t('confirmApproveMessage'),
          confirmLabel: t('approve'),
        };
      case 'reject':
        return {
          title: t('confirmReject'),
          message: t('confirmRejectMessage'),
          confirmLabel: t('reject'),
          reasonLabel: t('rejectionReason'),
          reasonPlaceholder: t('rejectionReasonPlaceholder'),
        };
      case 'request_changes':
        return {
          title: t('confirmRequestChanges'),
          message: t('confirmRequestChangesMessage'),
          confirmLabel: t('requestChanges'),
          reasonLabel: t('requestedChanges'),
          reasonPlaceholder: t('requestedChangesPlaceholder'),
        };
      default:
        return {
          title: '',
          message: '',
          confirmLabel: tCommon('confirm'),
        };
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex gap-4 flex-wrap">
          <div className="flex-shrink-0">
            <Select
              label={t('filterByZone')}
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              options={[
                { value: 'ALL', label: t('allZones') },
                ...zones.map((zone) => ({
                  value: zone.id,
                  label: zone.name,
                })),
              ]}
            />
          </div>
          <div className="flex-shrink-0">
            <Select
              label={t('filterByStatus')}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as SessionStatus | 'ALL')}
              options={STATUS_FILTERS.map((filter) => ({
                value: filter.value,
                label: t(filter.labelKey),
              }))}
            />
          </div>
        </div>
        {!showSeriesCreator && !showSingleSessionCreator && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setShowSingleSessionCreator(true)}>
              {t('createSession')}
            </Button>
            <Button variant="primary" onClick={() => setShowSeriesCreator(true)}>
              {t('createSeries')}
            </Button>
          </div>
        )}
      </div>

      {/* Single Session Creator */}
      {showSingleSessionCreator && (
        <Card>
          <Card.Content>
            <h3
              className="text-lg font-medium mb-4"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {t('createSession')}
            </h3>
            <SingleSessionCreator
              exhibitionId={exhibitionId}
              onSuccess={handleSingleSessionCreated}
              onCancel={() => setShowSingleSessionCreator(false)}
            />
          </Card.Content>
        </Card>
      )}

      {/* Series Creator */}
      {showSeriesCreator && (
        <Card>
          <Card.Content>
            <h3
              className="text-lg font-medium mb-4"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {t('createSeries')}
            </h3>
            <SeriesCreator
              exhibitionId={exhibitionId}
              onSuccess={handleSeriesCreated}
              onCancel={() => setShowSeriesCreator(false)}
            />
          </Card.Content>
        </Card>
      )}

      {/* Sessions list */}
      {sessions.length === 0 ? (
        <p
          className="text-center py-8"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          {t('noSessions')}
        </p>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="p-4 rounded-lg border"
              style={{
                borderColor: 'var(--color-border)',
                backgroundColor: 'var(--color-bg-secondary)',
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3
                      className="font-medium"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {session.title}
                    </h3>
                    <Badge variant={getStatusBadgeVariant(session.status)}>
                      {tSession(`status.${session.status}`)}
                    </Badge>
                  </div>

                  <p
                    className="text-sm mb-2"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    {session.game_title}
                  </p>

                  <div
                    className="flex flex-wrap gap-4 text-sm"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    <span>
                      {formatDate(session.scheduled_start)} {formatTime(session.scheduled_start)} - {formatTime(session.scheduled_end)}
                    </span>
                    <span>
                      {session.zone_name} / {session.table_label}
                    </span>
                    <span>
                      {session.confirmed_players_count}/{session.max_players_count} {t('players')}
                    </span>
                  </div>
                </div>

                {/* Actions based on session status */}
                <div className="flex gap-2 ml-4">
                  {/* Edit button for editable sessions */}
                  {!['FINISHED', 'CANCELLED', 'IN_PROGRESS'].includes(session.status) && (
                    <Link href={`/sessions/${session.id}/edit`}>
                      <Button size="sm" variant="secondary">
                        {tCommon('edit')}
                      </Button>
                    </Link>
                  )}

                  {/* Submit button for DRAFT sessions */}
                  {session.status === 'DRAFT' && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => openModerationDialog('submit', session.id, session.title)}
                    >
                      {t('submit')}
                    </Button>
                  )}

                  {/* Moderation buttons for pending sessions */}
                  {session.status === 'PENDING_MODERATION' && (
                    <>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => openModerationDialog('approve', session.id, session.title)}
                      >
                        {t('approve')}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => openModerationDialog('request_changes', session.id, session.title)}
                      >
                        {t('requestChanges')}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => openModerationDialog('reject', session.id, session.title)}
                      >
                        {t('reject')}
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Moderation Dialog */}
      <ModerationDialog
        isOpen={moderationDialog.isOpen}
        onClose={closeModerationDialog}
        onConfirm={handleModerationConfirm}
        action={moderationDialog.action}
        sessionTitle={moderationDialog.sessionTitle}
        cancelLabel={tCommon('cancel')}
        isLoading={isProcessing}
        {...getModerationDialogContent()}
      />
    </div>
  );
}
