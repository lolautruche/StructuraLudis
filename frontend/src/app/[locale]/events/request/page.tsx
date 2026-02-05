'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter, Link } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { eventRequestsApi } from '@/lib/api';
import { Button, Card, Input, Textarea, Select } from '@/components/ui';
import type { EventRequestCreate } from '@/lib/api/types';

// Region options (same as in EventFilters)
const REGION_OPTIONS = [
  // French regions
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
  // Neighboring countries
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

export default function EventRequestPage() {
  const t = useTranslations('EventRequest');
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();

  const [formData, setFormData] = useState<EventRequestCreate>({
    event_title: '',
    event_description: '',
    event_start_date: '',
    event_end_date: '',
    event_location_name: '',
    event_city: '',
    event_country_code: 'FR',
    event_region: '',
    event_timezone: 'Europe/Paris',
    organization_name: '',
    organization_contact_email: '',
    requester_message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    // Convert dates to ISO format
    const submitData = {
      ...formData,
      event_start_date: new Date(formData.event_start_date).toISOString(),
      event_end_date: new Date(formData.event_end_date).toISOString(),
    };

    const response = await eventRequestsApi.create(submitData);

    if (response.error) {
      setError(response.error.detail || response.error.message);
      setIsSubmitting(false);
    } else {
      setSuccess(true);
      setIsSubmitting(false);
    }
  };

  // Update form field
  const updateField = (field: keyof EventRequestCreate, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  // Check if email is verified
  if (user && !user.email_verified) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">✉️</div>
            <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {t('emailVerificationRequired')}
            </h2>
            <p className="mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              {t('emailVerificationDescription')}
            </p>
            <Link href="/my/settings">
              <Button variant="primary">{t('goToSettings')}</Button>
            </Link>
          </Card.Content>
        </Card>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">🎉</div>
            <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {t('successTitle')}
            </h2>
            <p className="mb-6" style={{ color: 'var(--color-text-secondary)' }}>
              {t('successMessage')}
            </p>
            <div className="flex justify-center gap-4">
              <Link href="/my/event-requests">
                <Button variant="primary">{t('viewMyRequests')}</Button>
              </Link>
              <Link href="/exhibitions">
                <Button variant="secondary">{t('browseEvents')}</Button>
              </Link>
            </div>
          </Card.Content>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
          {t('title')}
        </h1>
        <p className="mt-2" style={{ color: 'var(--color-text-secondary)' }}>
          {t('subtitle')}
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Event Information */}
        <Card>
          <Card.Header>
            <Card.Title>{t('eventInfo')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <Input
              label={t('eventTitle')}
              value={formData.event_title}
              onChange={(e) => updateField('event_title', e.target.value)}
              required
              placeholder={t('eventTitlePlaceholder')}
            />

            <Textarea
              label={t('eventDescription')}
              value={formData.event_description || ''}
              onChange={(e) => updateField('event_description', e.target.value)}
              rows={4}
              placeholder={t('eventDescriptionPlaceholder')}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                type="datetime-local"
                label={t('startDate')}
                value={formData.event_start_date}
                onChange={(e) => updateField('event_start_date', e.target.value)}
                required
              />
              <Input
                type="datetime-local"
                label={t('endDate')}
                value={formData.event_end_date}
                onChange={(e) => updateField('event_end_date', e.target.value)}
                required
              />
            </div>

            <Input
              label={t('locationName')}
              value={formData.event_location_name || ''}
              onChange={(e) => updateField('event_location_name', e.target.value)}
              placeholder={t('locationNamePlaceholder')}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label={t('city')}
                value={formData.event_city || ''}
                onChange={(e) => updateField('event_city', e.target.value)}
                placeholder={t('cityPlaceholder')}
              />
              <Select
                label={t('region')}
                value={formData.event_region || ''}
                onChange={(e) => updateField('event_region', e.target.value)}
                options={[
                  { value: '', label: t('selectRegion') },
                  ...REGION_OPTIONS,
                ]}
              />
            </div>

            <Select
              label={t('timezone')}
              value={formData.event_timezone}
              onChange={(e) => updateField('event_timezone', e.target.value)}
              options={TIMEZONE_OPTIONS}
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
              value={formData.organization_name}
              onChange={(e) => updateField('organization_name', e.target.value)}
              required
              placeholder={t('organizationNamePlaceholder')}
            />

            <Input
              type="email"
              label={t('contactEmail')}
              value={formData.organization_contact_email || ''}
              onChange={(e) => updateField('organization_contact_email', e.target.value)}
              placeholder={t('contactEmailPlaceholder')}
            />
          </Card.Content>
        </Card>

        {/* Message to Admins */}
        <Card>
          <Card.Header>
            <Card.Title>{t('messageToAdmins')}</Card.Title>
            <Card.Description>{t('messageToAdminsHelp')}</Card.Description>
          </Card.Header>
          <Card.Content>
            <Textarea
              value={formData.requester_message || ''}
              onChange={(e) => updateField('requester_message', e.target.value)}
              rows={4}
              placeholder={t('messagePlaceholder')}
              maxLength={2000}
            />
          </Card.Content>
        </Card>

        {/* Submit button */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="secondary" onClick={() => router.back()}>
            {t('cancel')}
          </Button>
          <Button type="submit" variant="primary" isLoading={isSubmitting}>
            {isSubmitting ? t('submitting') : t('submit')}
          </Button>
        </div>
      </form>
    </div>
  );
}
