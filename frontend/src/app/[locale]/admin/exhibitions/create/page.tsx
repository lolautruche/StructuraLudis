'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { adminApi, ExhibitionCreate } from '@/lib/api';
import { Card, Input, Textarea, Button, Select } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';

const LANGUAGES = [
  { value: 'fr', label: 'Français' },
  { value: 'en', label: 'English' },
];

const TIMEZONES = [
  { value: 'Europe/Paris', label: 'Europe/Paris' },
  { value: 'Europe/London', label: 'Europe/London' },
  { value: 'America/New_York', label: 'America/New_York' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo' },
];

function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove accents
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export default function CreateExhibitionPage() {
  const t = useTranslations('SuperAdmin.createExhibition');
  const tCommon = useTranslations('Common');
  const router = useRouter();
  const { showSuccess, showError } = useToast();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<ExhibitionCreate>({
    title: '',
    slug: '',
    description: '',
    start_date: '',
    end_date: '',
    location_name: '',
    city: '',
    country_code: 'FR',
    timezone: 'Europe/Paris',
    primary_language: 'fr',
    grace_period_minutes: 15,
  });

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const title = e.target.value;
    setFormData((prev) => ({
      ...prev,
      title,
      slug: generateSlug(title),
    }));
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'grace_period_minutes' ? parseInt(value, 10) || 0 : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    const response = await adminApi.createExhibition(formData);

    if (response.error) {
      showError(response.error.message);
      setIsSubmitting(false);
      return;
    }

    if (response.data) {
      showSuccess(t('createSuccess'));
      router.push(`/exhibitions/${response.data.id}/manage`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h2
        className="text-xl font-semibold mb-6"
        style={{ color: 'var(--color-text-primary)' }}
      >
        {t('title')}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <Card>
          <Card.Header>
            <Card.Title>{t('basicInfo')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <div>
              <label
                htmlFor="title"
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('titleLabel')}
              </label>
              <Input
                id="title"
                name="title"
                value={formData.title}
                onChange={handleTitleChange}
                required
              />
            </div>

            <div>
              <label
                htmlFor="slug"
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('slugLabel')}
              </label>
              <Input
                id="slug"
                name="slug"
                value={formData.slug}
                onChange={handleChange}
                required
              />
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--color-text-muted)' }}
              >
                {t('slugHelper')}
              </p>
            </div>

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('descriptionLabel')}
              </label>
              <Textarea
                id="description"
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="start_date"
                  className="block text-sm font-medium mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {t('startDate')}
                </label>
                <Input
                  id="start_date"
                  name="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={handleChange}
                  required
                />
              </div>
              <div>
                <label
                  htmlFor="end_date"
                  className="block text-sm font-medium mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {t('endDate')}
                </label>
                <Input
                  id="end_date"
                  name="end_date"
                  type="date"
                  value={formData.end_date}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Location */}
        <Card>
          <Card.Header>
            <Card.Title>{t('location')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <div>
              <label
                htmlFor="location_name"
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('locationName')}
              </label>
              <Input
                id="location_name"
                name="location_name"
                value={formData.location_name || ''}
                onChange={handleChange}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="city"
                  className="block text-sm font-medium mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {t('city')}
                </label>
                <Input
                  id="city"
                  name="city"
                  value={formData.city || ''}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label
                  htmlFor="country_code"
                  className="block text-sm font-medium mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {t('country')}
                </label>
                <Input
                  id="country_code"
                  name="country_code"
                  value={formData.country_code || ''}
                  onChange={handleChange}
                  maxLength={2}
                  placeholder="FR"
                />
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Settings */}
        <Card>
          <Card.Header>
            <Card.Title>{t('settings')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="timezone"
                  className="block text-sm font-medium mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {t('timezone')}
                </label>
                <Select
                  id="timezone"
                  name="timezone"
                  options={TIMEZONES}
                  value={formData.timezone}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label
                  htmlFor="primary_language"
                  className="block text-sm font-medium mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {t('language')}
                </label>
                <Select
                  id="primary_language"
                  name="primary_language"
                  options={LANGUAGES}
                  value={formData.primary_language}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="grace_period_minutes"
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('gracePeriod')}
              </label>
              <Input
                id="grace_period_minutes"
                name="grace_period_minutes"
                type="number"
                min="0"
                max="60"
                value={formData.grace_period_minutes || 15}
                onChange={handleChange}
              />
            </div>
          </Card.Content>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.push('/admin/exhibitions')}
          >
            {tCommon('cancel')}
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {t('create')}
          </Button>
        </div>
      </form>
    </div>
  );
}
