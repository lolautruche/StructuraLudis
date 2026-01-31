'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { useAuth } from '@/contexts/AuthContext';
import { SessionSubmissionForm } from '@/components/sessions';
import { Button } from '@/components/ui';

export default function NewSessionPage() {
  const t = useTranslations('SessionForm');
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const exhibitionId = searchParams.get('exhibition');
  const [showMissingExhibition, setShowMissingExhibition] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Check for exhibition ID
  useEffect(() => {
    if (!authLoading && isAuthenticated && !exhibitionId) {
      setShowMissingExhibition(true);
    }
  }, [authLoading, isAuthenticated, exhibitionId]);

  // Handle successful submission
  const handleSuccess = (sessionId: string, isDraft: boolean) => {
    if (isDraft) {
      // Navigate to session edit page or agenda
      router.push('/my/agenda');
    } else {
      // Navigate to session detail page
      router.push(`/sessions/${sessionId}`);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    router.back();
  };

  // Loading state
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400">{t('loading')}</p>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return null; // Will redirect
  }

  // Missing exhibition ID
  if (showMissingExhibition) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">{t('missingExhibition')}</h1>
          <p className="text-slate-600 dark:text-slate-400 mb-6">{t('missingExhibitionDescription')}</p>
          <Button onClick={() => router.push('/my/agenda')}>
            {t('goToAgenda')}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{t('pageTitle')}</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">{t('pageDescription')}</p>
      </div>

      {/* Form */}
      {exhibitionId && (
        <SessionSubmissionForm
          exhibitionId={exhibitionId}
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
}
