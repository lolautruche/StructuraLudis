'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useRouter, Link } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { eventRequestsApi } from '@/lib/api';
import { Button, Card, Input, Textarea, Select, Badge } from '@/components/ui';
import type { EventRequest, EventRequestUpdate } from '@/lib/api/types';

// Region options
const REGION_OPTIONS = [
  { value: 'auvergne-rhone-alpes', label: 'Auvergne-Rhône-Alpes' },
  { value: 'bourgogne-franche-comte', label: 'Bourgogne-Franche-Comté' },
  { value: 'bretagne', label: 'Bretagne' },
  { value: 'centre-val-de-loire', label: 'Centre-Val de Loire' },
  { value: 'corse', label: 'Corse' },
  { value: 'grand-est', label: 'Grand Est' },
  { value: 'hauts-de-france', label: 'Hauts-de-France' },
  { value: 'ile-de-france', label: 'Île-de-France' },
  { value: 'normandie', label: 'Normandie' },
  { value: 'nouvelle-aquitaine', label: 'Nouvelle-Aquitaine' },
  { value: 'occitanie', label: 'Occitanie' },
  { value: 'pays-de-la-loire', label: 'Pays de la Loire' },
  { value: 'provence-alpes-cote-dazur', label: "Provence-Alpes-Côte d'Azur" },
  { value: 'belgium', label: 'Belgium' },
  { value: 'switzerland', label: 'Switzerland' },
  { value: 'luxembourg', label: 'Luxembourg' },
  { value: 'germany', label: 'Germany' },
  { value: 'spain', label: 'Spain' },
  { value: 'italy', label: 'Italy' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'other', label: 'Other' },
];

const TIMEZONE_OPTIONS = [
  { value: 'Europe/Paris', label: 'Europe/Paris (CET)' },
  { value: 'Europe/London', label: 'Europe/London (GMT)' },
  { value: 'Europe/Brussels', label: 'Europe/Brussels (CET)' },
  { value: 'Europe/Berlin', label: 'Europe/Berlin (CET)' },
  { value: 'Europe/Rome', label: 'Europe/Rome (CET)' },
  { value: 'Europe/Madrid', label: 'Europe/Madrid (CET)' },
  { value: 'Europe/Zurich', label: 'Europe/Zurich (CET)' },
  { value: 'America/New_York', label: 'America/New_York (EST)' },
  { value: 'UTC', label: 'UTC' },
];

function formatDateForInput(dateStr: string): string {
  const date = new Date(dateStr);
  // Format as YYYY-MM-DDTHH:mm for datetime-local input in LOCAL timezone
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export default function EditEventRequestPage() {
  const t = useTranslations('EventRequest');
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const requestId = params.id as string;

  const [request, setRequest] = useState<EventRequest | null>(null);
  const [formData, setFormData] = useState<EventRequestUpdate>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isResubmitting, setIsResubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch request
  useEffect(() => {
    async function fetchRequest() {
      setIsLoading(true);
      const response = await eventRequestsApi.getById(requestId);
      if (response.data) {
        setRequest(response.data);
        setFormData({
          event_title: response.data.event_title,
          event_description: response.data.event_description || '',
          event_start_date: formatDateForInput(response.data.event_start_date),
          event_end_date: formatDateForInput(response.data.event_end_date),
          event_location_name: response.data.event_location_name || '',
          event_city: response.data.event_city || '',
          event_region: response.data.event_region || '',
          event_timezone: response.data.event_timezone,
          organization_name: response.data.organization_name,
          organization_contact_email: response.data.organization_contact_email || '',
          requester_message: response.data.requester_message || '',
        });
      } else if (response.error) {
        setError(response.error.detail || response.error.message);
      }
      setIsLoading(false);
    }

    if (isAuthenticated && requestId) {
      fetchRequest();
    }
  }, [isAuthenticated, requestId]);

  // Handle save
  const handleSave = async () => {
    setError(null);
    setIsSaving(true);

    const updateData = {
      ...formData,
      event_start_date: formData.event_start_date
        ? new Date(formData.event_start_date).toISOString()
        : undefined,
      event_end_date: formData.event_end_date
        ? new Date(formData.event_end_date).toISOString()
        : undefined,
    };

    const response = await eventRequestsApi.update(requestId, updateData);

    if (response.error) {
      setError(response.error.detail || response.error.message);
    } else if (response.data) {
      setRequest(response.data);
      setSuccess(true);
    }
    setIsSaving(false);
  };

  // Handle resubmit
  const handleResubmit = async () => {
    setError(null);
    setIsResubmitting(true);

    // First save changes
    const updateData = {
      ...formData,
      event_start_date: formData.event_start_date
        ? new Date(formData.event_start_date).toISOString()
        : undefined,
      event_end_date: formData.event_end_date
        ? new Date(formData.event_end_date).toISOString()
        : undefined,
    };

    const updateResponse = await eventRequestsApi.update(requestId, updateData);
    if (updateResponse.error) {
      setError(updateResponse.error.detail || updateResponse.error.message);
      setIsResubmitting(false);
      return;
    }

    // Then resubmit
    const resubmitResponse = await eventRequestsApi.resubmit(requestId);

    if (resubmitResponse.error) {
      setError(resubmitResponse.error.detail || resubmitResponse.error.message);
    } else {
      router.push('/my/event-requests');
    }
    setIsResubmitting(false);
  };

  // Update form field
  const updateField = (field: keyof EventRequestUpdate, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSuccess(false);
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (error && !request) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">❌</div>
            <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {t('error')}
            </h2>
            <p className="mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              {error}
            </p>
            <Link href="/my/event-requests">
              <Button variant="primary">{t('backToList')}</Button>
            </Link>
          </Card.Content>
        </Card>
      </div>
    );
  }

  if (!request) {
    return null;
  }

  const canEdit = request.status === 'CHANGES_REQUESTED';
  const isReadOnly = !canEdit;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {canEdit ? t('editRequest') : t('viewRequest')}
          </h1>
          <div className="mt-2 flex items-center gap-2">
            <Badge
              variant={
                request.status === 'APPROVED'
                  ? 'success'
                  : request.status === 'REJECTED'
                    ? 'danger'
                    : 'warning'
              }
            >
              {request.status === 'PENDING' && t('pending')}
              {request.status === 'CHANGES_REQUESTED' && t('changesRequested')}
              {request.status === 'APPROVED' && t('approved')}
              {request.status === 'REJECTED' && t('rejected')}
            </Badge>
          </div>
        </div>
        <Link href="/my/event-requests">
          <Button variant="secondary">{t('backToList')}</Button>
        </Link>
      </div>

      {/* Admin comment */}
      {request.admin_comment && (
        <Card className="mb-6">
          <Card.Content>
            <div className="flex items-start gap-3">
              <span className="text-xl">💬</span>
              <div>
                <p className="font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>
                  {t('adminComment')}
                </p>
                <p className="whitespace-pre-wrap" style={{ color: 'var(--color-text-secondary)' }}>{request.admin_comment}</p>
              </div>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Success message */}
      {success && (
        <div className="mb-6 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300">
          {t('changesSaved')}
        </div>
      )}

      <div className="space-y-8">
        {/* Event Information */}
        <Card>
          <Card.Header>
            <Card.Title>{t('eventInfo')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <Input
              label={t('eventTitle')}
              value={formData.event_title || ''}
              onChange={(e) => updateField('event_title', e.target.value)}
              disabled={isReadOnly}
            />

            <Textarea
              label={t('eventDescription')}
              value={formData.event_description || ''}
              onChange={(e) => updateField('event_description', e.target.value)}
              rows={4}
              disabled={isReadOnly}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                type="datetime-local"
                label={t('startDate')}
                value={formData.event_start_date || ''}
                onChange={(e) => updateField('event_start_date', e.target.value)}
                disabled={isReadOnly}
              />
              <Input
                type="datetime-local"
                label={t('endDate')}
                value={formData.event_end_date || ''}
                onChange={(e) => updateField('event_end_date', e.target.value)}
                disabled={isReadOnly}
              />
            </div>

            <Input
              label={t('locationName')}
              value={formData.event_location_name || ''}
              onChange={(e) => updateField('event_location_name', e.target.value)}
              disabled={isReadOnly}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label={t('city')}
                value={formData.event_city || ''}
                onChange={(e) => updateField('event_city', e.target.value)}
                disabled={isReadOnly}
              />
              <Select
                label={t('region')}
                value={formData.event_region || ''}
                onChange={(e) => updateField('event_region', e.target.value)}
                options={[{ value: '', label: t('selectRegion') }, ...REGION_OPTIONS]}
                disabled={isReadOnly}
              />
            </div>

            <Select
              label={t('timezone')}
              value={formData.event_timezone || 'Europe/Paris'}
              onChange={(e) => updateField('event_timezone', e.target.value)}
              options={TIMEZONE_OPTIONS}
              disabled={isReadOnly}
            />
          </Card.Content>
        </Card>

        {/* Organization Information */}
        <Card>
          <Card.Header>
            <Card.Title>{t('organizationInfo')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <Input
              label={t('organizationName')}
              value={formData.organization_name || ''}
              onChange={(e) => updateField('organization_name', e.target.value)}
              disabled={isReadOnly}
            />

            <Input
              type="email"
              label={t('contactEmail')}
              value={formData.organization_contact_email || ''}
              onChange={(e) => updateField('organization_contact_email', e.target.value)}
              disabled={isReadOnly}
            />
          </Card.Content>
        </Card>

        {/* Message to Admins */}
        <Card>
          <Card.Header>
            <Card.Title>{t('messageToAdmins')}</Card.Title>
          </Card.Header>
          <Card.Content>
            <Textarea
              value={formData.requester_message || ''}
              onChange={(e) => updateField('requester_message', e.target.value)}
              rows={4}
              maxLength={2000}
              disabled={isReadOnly}
            />
          </Card.Content>
        </Card>

        {/* Actions */}
        {canEdit && (
          <div className="flex justify-end gap-4">
            <Button type="button" variant="secondary" onClick={handleSave} isLoading={isSaving}>
              {t('saveChanges')}
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={handleResubmit}
              isLoading={isResubmitting}
            >
              {t('resubmit')}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
