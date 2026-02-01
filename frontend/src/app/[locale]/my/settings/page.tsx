'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from '@/i18n/routing';
import { Card } from '@/components/ui';
import { ProfileForm, PasswordForm, EmailChangeForm, PrivacySection } from '@/components/settings';

type TabId = 'profile' | 'security' | 'privacy';

export default function SettingsPage() {
  const t = useTranslations('Settings');
  const router = useRouter();
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>('profile');

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Not authenticated
  if (!isAuthenticated) {
    return null; // Will redirect
  }

  if (authLoading || !user) {
    return (
      <div className="max-w-2xl mx-auto mt-8">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-48 mb-6" />
          <div className="h-64 bg-slate-200 dark:bg-slate-700 rounded" />
        </div>
      </div>
    );
  }

  const tabs: { id: TabId; label: string }[] = [
    { id: 'profile', label: t('profile') },
    { id: 'security', label: t('security') },
    { id: 'privacy', label: t('privacy') },
  ];

  return (
    <div className="max-w-2xl mx-auto mt-8 px-4">
      <h1
        className="text-2xl font-bold mb-6"
        style={{ color: 'var(--color-text-primary)' }}
      >
        {t('title')}
      </h1>

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
          {activeTab === 'profile' && <ProfileForm />}
          {activeTab === 'security' && (
            <div className="space-y-8">
              {/* Email change section */}
              <div>
                <h3 className="text-lg font-medium mb-4" style={{ color: 'var(--color-text-primary)' }}>
                  {t('email')}
                </h3>
                <EmailChangeForm />
              </div>

              {/* Separator */}
              <hr style={{ borderColor: 'var(--color-border)' }} />

              {/* Password change section */}
              <div>
                <h3 className="text-lg font-medium mb-4" style={{ color: 'var(--color-text-primary)' }}>
                  {t('changePassword')}
                </h3>
                <PasswordForm />
              </div>
            </div>
          )}
          {activeTab === 'privacy' && <PrivacySection />}
        </Card.Content>
      </Card>
    </div>
  );
}
