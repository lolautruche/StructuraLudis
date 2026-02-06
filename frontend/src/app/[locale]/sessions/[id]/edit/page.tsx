'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useRouter, Link } from '@/i18n/routing';
import { Button, Card, Input, Textarea, ConfirmDialog } from '@/components/ui';
import { SafetyToolsSelector } from '@/components/sessions/SafetyToolsSelector';
import { sessionsApi, exhibitionsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import type { GameSession, SessionUpdateRequest, Exhibition, SafetyTool } from '@/lib/api/types';

export default function SessionEditPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const t = useTranslations('Session');
  const tCommon = useTranslations('Common');
  const router = useRouter();
  const { isAuthenticated, user, isLoading: authLoading } = useAuth();
  const { showSuccess, showError } = useToast();

  const [session, setSession] = useState<GameSession | null>(null);
  const [exhibition, setExhibition] = useState<Exhibition | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [cancelReason, setCancelReason] = useState('');

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('fr');
  const [minAge, setMinAge] = useState(0);
  const [maxPlayers, setMaxPlayers] = useState(5);
  const [isAccessible, setIsAccessible] = useState(false);
  const [availableSafetyTools, setAvailableSafetyTools] = useState<SafetyTool[]>([]);
  const [selectedSafetyToolIds, setSelectedSafetyToolIds] = useState<string[]>([]);

  // Fetch session details
  const fetchSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const response = await sessionsApi.getById(sessionId);
    if (response.data) {
      const s = response.data;
      setSession(s);
      setTitle(s.title);
      setDescription(s.description || '');
      setLanguage(s.language);
      setMinAge(s.min_age);
      setMaxPlayers(s.max_players_count);
      setIsAccessible(s.is_accessible_disability);

      // Fetch exhibition and safety tools
      const [exhibitionResponse, toolsResponse] = await Promise.all([
        exhibitionsApi.getById(s.exhibition_id),
        exhibitionsApi.getSafetyTools(s.exhibition_id),
      ]);
      if (exhibitionResponse.data) {
        setExhibition(exhibitionResponse.data);
      }
      if (toolsResponse.data) {
        const tools = toolsResponse.data;
        setAvailableSafetyTools(tools);
        // Map session's stored safety_tools (could be IDs or slugs) to tool IDs
        if (s.safety_tools && s.safety_tools.length > 0) {
          const mappedIds = s.safety_tools.map((value) => {
            // Try matching by ID first, then by slug
            const byId = tools.find((t) => t.id === value);
            if (byId) return byId.id;
            const bySlug = tools.find((t) => t.slug === value);
            if (bySlug) return bySlug.id;
            return value; // fallback: keep original value
          });
          setSelectedSafetyToolIds(mappedIds);
        }
      }
    } else {
      setError(response.error?.message || t('sessionNotFound'));
    }

    setIsLoading(false);
  }, [sessionId, t]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
      return;
    }
    if (isAuthenticated) {
      fetchSession();
    }
  }, [authLoading, isAuthenticated, fetchSession, router]);

  // Check permissions
  const canEdit = session && user && (
    // GM can edit their own sessions
    session.created_by_user_id === user.id ||
    // Admin can edit any session
    user.global_role === 'ADMIN' ||
    user.global_role === 'SUPER_ADMIN' ||
    // Organizer can edit sessions in their exhibition
    exhibition?.can_manage
  );

  // Sessions can be edited unless they are finished, cancelled, or in progress
  const isEditable = session && !['FINISHED', 'CANCELLED', 'IN_PROGRESS'].includes(session.status);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session || !canEdit) return;

    setIsSaving(true);
    const updateData: SessionUpdateRequest = {
      title,
      description: description || undefined,
      language,
      min_age: minAge,
      max_players_count: maxPlayers,
      is_accessible_disability: isAccessible,
      safety_tools: selectedSafetyToolIds.length > 0 ? selectedSafetyToolIds : [],
    };

    const response = await sessionsApi.update(session.id, updateData);
    if (response.data) {
      showSuccess(t('sessionUpdated'));
      router.push(`/sessions/${session.id}`);
    } else {
      showError(response.error?.message || t('updateError'));
    }
    setIsSaving(false);
  };

  const handleCancelSession = async () => {
    if (!session || !cancelReason.trim()) return;
    setIsCancelling(true);
    const response = await sessionsApi.cancel(session.id, cancelReason);
    if (response.data) {
      showSuccess(t('sessionCancelled'));
      router.push(`/sessions/${session.id}`);
    } else {
      showError(response.error?.message || t('cancelError'));
    }
    setIsCancelling(false);
    setShowCancelDialog(false);
  };

  // Check if session can be cancelled (not already finished, cancelled, or in progress)
  const canCancelSession = session && !['FINISHED', 'CANCELLED', 'IN_PROGRESS'].includes(session.status);

  if (authLoading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400">{tCommon('loading')}</p>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
          {t('sessionNotFound')}
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">{error}</p>
        <Link href="/exhibitions">
          <Button variant="primary">{t('backToSessions')}</Button>
        </Link>
      </div>
    );
  }

  if (!canEdit) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
          {t('noEditPermission')}
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          {t('noEditPermissionDescription')}
        </p>
        <Link href={`/sessions/${session.id}`}>
          <Button variant="primary">{t('backToSession')}</Button>
        </Link>
      </div>
    );
  }

  if (!isEditable) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
          {t('sessionNotEditable')}
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          {t('sessionNotEditableDescription')}
        </p>
        <Link href={`/sessions/${session.id}`}>
          <Button variant="primary">{t('backToSession')}</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back link */}
      <Link
        href={`/sessions/${session.id}`}
        className="inline-flex items-center text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
      >
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        {t('backToSession')}
      </Link>

      <Card>
        <Card.Header>
          <Card.Title>{t('editSession')}</Card.Title>
        </Card.Header>
        <Card.Content>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t('sessionTitle')} *
              </label>
              <Input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={255}
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t('description')}
              </label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
              />
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t('language')}
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-ludis-primary"
              >
                <option value="fr">Français</option>
                <option value="en">English</option>
              </select>
            </div>

            {/* Min Age */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t('minAge')}
              </label>
              <Input
                type="number"
                value={minAge}
                onChange={(e) => setMinAge(parseInt(e.target.value) || 0)}
                min={0}
                max={99}
              />
            </div>

            {/* Max Players */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t('maxPlayers')}
              </label>
              <Input
                type="number"
                value={maxPlayers}
                onChange={(e) => setMaxPlayers(parseInt(e.target.value) || 1)}
                min={1}
                max={100}
              />
            </div>

            {/* Accessibility */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="accessible"
                checked={isAccessible}
                onChange={(e) => setIsAccessible(e.target.checked)}
                className="rounded border-gray-300 text-ludis-primary focus:ring-ludis-primary"
              />
              <label htmlFor="accessible" className="text-sm text-slate-700 dark:text-slate-300">
                {t('accessibleSession')}
              </label>
            </div>

            {/* Safety Tools */}
            {availableSafetyTools.length > 0 && (
              <SafetyToolsSelector
                safetyTools={availableSafetyTools}
                selectedToolIds={selectedSafetyToolIds}
                onToolsChange={setSelectedSafetyToolIds}
              />
            )}

            {/* Actions */}
            <div className="flex gap-4 pt-4 border-t border-slate-200 dark:border-slate-700">
              <Button
                type="submit"
                variant="primary"
                isLoading={isSaving}
                disabled={isSaving}
              >
                {tCommon('save')}
              </Button>
              <Link href={`/sessions/${session.id}`}>
                <Button type="button" variant="secondary">
                  {tCommon('cancel')}
                </Button>
              </Link>
            </div>
          </form>
        </Card.Content>
      </Card>

      {/* Session Actions Card */}
      {canCancelSession && (
        <Card>
          <Card.Header>
            <Card.Title>{t('sessionActions')}</Card.Title>
          </Card.Header>
          <Card.Content>
            {/* Cancel Session Button */}
            <div className="flex items-center justify-between p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <div>
                <h4 className="font-medium text-red-800 dark:text-red-200">
                  {t('cancelSessionTitle')}
                </h4>
                <p className="text-sm text-red-600 dark:text-red-400">
                  {t('cancelSessionWarning')}
                </p>
              </div>
              <Button
                variant="danger"
                onClick={() => setShowCancelDialog(true)}
                isLoading={isCancelling}
              >
                {t('cancelSession')}
              </Button>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Cancel Session Dialog */}
      <ConfirmDialog
        isOpen={showCancelDialog}
        onClose={() => {
          setShowCancelDialog(false);
          setCancelReason('');
        }}
        onConfirm={handleCancelSession}
        title={t('confirmCancelTitle')}
        message={
          <div className="space-y-4">
            <p className="text-red-600 dark:text-red-400 font-medium">
              {t('confirmCancelWarning')}
            </p>
            <p>{t('confirmCancelMessage')}</p>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t('cancelReason')} *
              </label>
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-red-500"
                rows={3}
                placeholder={t('cancelReasonPlaceholder')}
                required
              />
            </div>
          </div>
        }
        confirmLabel={t('confirmCancel')}
        cancelLabel={tCommon('cancel')}
        variant="danger"
        isLoading={isCancelling}
        confirmDisabled={!cancelReason.trim()}
      />
    </div>
  );
}
