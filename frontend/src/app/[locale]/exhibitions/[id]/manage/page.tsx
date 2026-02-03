'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from '@/i18n/routing';
import { exhibitionsApi, Exhibition } from '@/lib/api';
import { Card } from '@/components/ui';
import { ExhibitionSettingsForm, ZoneList, RolesList } from '@/components/admin';
import { PartnerSessionList } from '@/components/partner';

type TabId = 'settings' | 'zones' | 'roles' | 'sessions';

export default function ManageExhibitionPage() {
  const t = useTranslations('Admin');
  const tPartner = useTranslations('Partner');
  const params = useParams();
  const router = useRouter();
  const { isLoading: authLoading, isAuthenticated } = useAuth();

  const [exhibition, setExhibition] = useState<Exhibition | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId | null>(null);

  const exhibitionId = params.id as string;

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Load exhibition and check permissions
  useEffect(() => {
    async function loadExhibition() {
      if (!exhibitionId) return;

      setIsLoading(true);
      setError(null);

      const response = await exhibitionsApi.getById(exhibitionId);

      if (response.error) {
        setError(response.error.message);
      } else if (response.data) {
        // Check if user can manage this exhibition
        if (!response.data.can_manage) {
          setError(t('noPermission'));
        } else {
          setExhibition(response.data);
        }
      }

      setIsLoading(false);
    }

    if (!authLoading && isAuthenticated) {
      loadExhibition();
    }
  }, [exhibitionId, authLoading, isAuthenticated, t]);

  // Loading states
  if (authLoading || !isAuthenticated) {
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

  // Determine user role for this exhibition
  const isOrganizer = exhibition.user_exhibition_role === 'ORGANIZER';
  const isPartner = exhibition.user_exhibition_role === 'PARTNER';

  // Build tabs based on role (Issue #10, #105)
  // ORGANIZER: settings, zones (includes time slots), sessions, roles
  // PARTNER: zones (filtered, includes time slots), sessions
  const tabs: { id: TabId; label: string }[] = isOrganizer
    ? [
        { id: 'settings', label: t('settings') },
        { id: 'zones', label: t('zonesAndTables') },
        { id: 'sessions', label: tPartner('sessions') },
        { id: 'roles', label: t('roles.tab') },
      ]
    : [
        { id: 'zones', label: t('zonesAndTables') },
        { id: 'sessions', label: tPartner('sessions') },
      ];

  // Set default active tab if not set
  const currentTab = activeTab || tabs[0].id;

  // Title based on role
  const pageTitle = isOrganizer ? t('title') : tPartner('dashboard');

  return (
    <div className="max-w-4xl mx-auto mt-8 px-4">
      <h1
        className="text-2xl font-bold mb-2"
        style={{ color: 'var(--color-text-primary)' }}
      >
        {pageTitle}
      </h1>
      <p
        className="text-sm mb-6"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        {exhibition.title}
        {isPartner && (
          <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700">
            {tPartner('partnerRole')}
          </span>
        )}
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
              currentTab === tab.id
                ? 'border-ludis-primary text-ludis-primary'
                : 'border-transparent hover:border-slate-300 dark:hover:border-slate-600'
            }`}
            style={{
              color:
                currentTab === tab.id
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
          {currentTab === 'settings' && isOrganizer && (
            <ExhibitionSettingsForm
              exhibition={exhibition}
              onUpdate={setExhibition}
            />
          )}
          {currentTab === 'zones' && (
            <ZoneList
              exhibitionId={exhibition.id}
              partnerMode={isPartner}
            />
          )}
          {currentTab === 'roles' && isOrganizer && (
            <RolesList exhibitionId={exhibition.id} />
          )}
          {currentTab === 'sessions' && (isOrganizer || isPartner) && (
            <PartnerSessionList exhibitionId={exhibition.id} />
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
