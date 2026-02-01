'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from '@/i18n/routing';
import { exhibitionsApi, Exhibition } from '@/lib/api';
import { Card } from '@/components/ui';
import { ExhibitionSettingsForm, TimeSlotList } from '@/components/admin';

type TabId = 'settings' | 'slots' | 'zones';

export default function ManageExhibitionPage() {
  const t = useTranslations('Admin');
  const params = useParams();
  const router = useRouter();
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  const [exhibition, setExhibition] = useState<Exhibition | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('settings');

  const exhibitionId = params.id as string;

  // Check permissions
  const canManage =
    user?.global_role === 'SUPER_ADMIN' || user?.global_role === 'ORGANIZER';

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Redirect if no permission
  useEffect(() => {
    if (!authLoading && isAuthenticated && !canManage) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, canManage, router]);

  // Load exhibition
  useEffect(() => {
    async function loadExhibition() {
      if (!exhibitionId || !canManage) return;

      setIsLoading(true);
      setError(null);

      const response = await exhibitionsApi.getById(exhibitionId);

      if (response.error) {
        setError(response.error.message);
      } else if (response.data) {
        setExhibition(response.data);
      }

      setIsLoading(false);
    }

    if (!authLoading && isAuthenticated && canManage) {
      loadExhibition();
    }
  }, [exhibitionId, authLoading, isAuthenticated, canManage]);

  // Loading states
  if (authLoading || !isAuthenticated || !canManage) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-64 mb-6" />
          <div className="h-96 bg-slate-200 dark:bg-slate-700 rounded" />
        </div>
      </div>
    );
  }

  if (error || !exhibition) {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <Card>
          <Card.Content>
            <p style={{ color: 'var(--color-text-danger)' }}>
              {error || t('exhibitionNotFound')}
            </p>
          </Card.Content>
        </Card>
      </div>
    );
  }

  const tabs: { id: TabId; label: string }[] = [
    { id: 'settings', label: t('settings') },
    { id: 'slots', label: t('timeSlots') },
    { id: 'zones', label: t('zonesAndTables') },
  ];

  return (
    <div className="max-w-4xl mx-auto mt-8 px-4">
      <h1
        className="text-2xl font-bold mb-2"
        style={{ color: 'var(--color-text-primary)' }}
      >
        {t('title')}
      </h1>
      <p
        className="text-sm mb-6"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        {exhibition.title}
      </p>

      {/* Tab navigation */}
      <div
        className="flex border-b mb-6"
        style={{ borderColor: 'var(--color-border)' }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'border-ludis-primary text-ludis-primary'
                : 'border-transparent hover:border-slate-300 dark:hover:border-slate-600'
            }`}
            style={{
              color:
                activeTab === tab.id
                  ? 'var(--color-primary)'
                  : 'var(--color-text-secondary)',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <Card>
        <Card.Content>
          {activeTab === 'settings' && (
            <ExhibitionSettingsForm
              exhibition={exhibition}
              onUpdate={setExhibition}
            />
          )}
          {activeTab === 'slots' && (
            <TimeSlotList exhibitionId={exhibition.id} />
          )}
          {activeTab === 'zones' && (
            <div className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
              {t('comingSoon')}
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
