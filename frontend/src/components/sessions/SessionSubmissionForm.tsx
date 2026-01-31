'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button, Input, Textarea, Select, Checkbox, Card } from '@/components/ui';
import { GameSelector } from './GameSelector';
import { TimeSlotSelector } from './TimeSlotSelector';
import { SafetyToolsSelector } from './SafetyToolsSelector';
import { exhibitionsApi, sessionsApi } from '@/lib/api';
import type { Game, TimeSlot, SafetyTool } from '@/lib/api/types';

// Form validation schema
const sessionFormSchema = z.object({
  game_id: z.string().uuid('Select a game'),
  time_slot_id: z.string().uuid('Select a time slot'),
  scheduled_start: z.string().min(1, 'Start time is required'),
  scheduled_end: z.string().min(1, 'End time is required'),
  title: z.string().min(1, 'Title is required').max(255, 'Title is too long'),
  description: z.string().max(5000, 'Description is too long').optional(),
  language: z.string().min(2).max(10),
  max_players_count: z.number().int().min(1, 'At least 1 player').max(100, 'Max 100 players'),
  min_age: z.number().int().min(0).max(99).optional().nullable(),
  is_accessible_disability: z.boolean(),
  safety_tools: z.array(z.string()),
}).refine((data) => {
  if (!data.scheduled_start || !data.scheduled_end) return true;
  return new Date(data.scheduled_end) > new Date(data.scheduled_start);
}, {
  message: 'End time must be after start time',
  path: ['scheduled_end'],
});

type SessionFormData = z.infer<typeof sessionFormSchema>;

interface SessionSubmissionFormProps {
  exhibitionId: string;
  onSuccess?: (sessionId: string, isDraft: boolean) => void;
  onCancel?: () => void;
}

export function SessionSubmissionForm({
  exhibitionId,
  onSuccess,
  onCancel,
}: SessionSubmissionFormProps) {
  const t = useTranslations('SessionForm');

  // Data loading states
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [safetyTools, setSafetyTools] = useState<SafetyTool[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Selected game (for display)
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);

  // Submission states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Form setup
  const {
    register,
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SessionFormData>({
    resolver: zodResolver(sessionFormSchema),
    defaultValues: {
      game_id: '',
      time_slot_id: '',
      scheduled_start: '',
      scheduled_end: '',
      title: '',
      description: '',
      language: 'en',
      max_players_count: 4,
      min_age: null,
      is_accessible_disability: false,
      safety_tools: [],
    },
  });

  // Watch form values
  const watchedTimeSlotId = watch('time_slot_id');
  const watchedScheduledStart = watch('scheduled_start');
  const watchedScheduledEnd = watch('scheduled_end');
  const watchedSafetyTools = watch('safety_tools');

  // Load exhibition data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setLoadError(null);

      try {
        const [exhibitionRes, slotsRes, toolsRes] = await Promise.all([
          exhibitionsApi.getById(exhibitionId),
          exhibitionsApi.getTimeSlots(exhibitionId),
          exhibitionsApi.getSafetyTools(exhibitionId),
        ]);

        if (exhibitionRes.error) {
          setLoadError(exhibitionRes.error.message);
          return;
        }

        setTimeSlots(slotsRes.data || []);
        setSafetyTools(toolsRes.data || []);

        // Set default language from exhibition
        if (exhibitionRes.data?.primary_language) {
          setValue('language', exhibitionRes.data.primary_language);
        }
      } catch (err) {
        setLoadError('Failed to load exhibition data');
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [exhibitionId, setValue]);

  // Handle game selection
  const handleGameSelect = useCallback((game: Game | null) => {
    setSelectedGame(game);
    setValue('game_id', game?.id || '');
    // Auto-fill title with game title if empty
    if (game && !watch('title')) {
      setValue('title', game.title);
    }
    // Set default max players from game
    if (game) {
      setValue('max_players_count', game.max_players);
    }
  }, [setValue, watch]);

  // Handle form submission
  const onSubmit = async (data: SessionFormData, submitForModeration: boolean) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Create session
      const createResponse = await sessionsApi.create({
        exhibition_id: exhibitionId,
        time_slot_id: data.time_slot_id,
        game_id: data.game_id,
        title: data.title,
        description: data.description || undefined,
        language: data.language,
        min_age: data.min_age || undefined,
        max_players_count: data.max_players_count,
        safety_tools: data.safety_tools.length > 0 ? data.safety_tools : undefined,
        is_accessible_disability: data.is_accessible_disability,
        scheduled_start: data.scheduled_start,
        scheduled_end: data.scheduled_end,
      });

      if (createResponse.error) {
        setSubmitError(createResponse.error.message);
        return;
      }

      const sessionId = createResponse.data!.id;

      // Submit for moderation if requested
      if (submitForModeration) {
        const submitResponse = await sessionsApi.submit(sessionId);
        if (submitResponse.error) {
          // Session created but submission failed
          setSubmitError(t('submitError'));
          return;
        }
      }

      onSuccess?.(sessionId, !submitForModeration);
    } catch (err) {
      setSubmitError(t('genericError'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Save as draft
  const handleSaveDraft = handleSubmit((data) => onSubmit(data, false));

  // Submit for review
  const handleSubmitForReview = handleSubmit((data) => onSubmit(data, true));

  // Language options
  const languageOptions = [
    { value: 'en', label: 'English' },
    { value: 'fr', label: 'Francais' },
    { value: 'de', label: 'Deutsch' },
    { value: 'es', label: 'Espanol' },
    { value: 'it', label: 'Italiano' },
  ];

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ludis-primary mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400">{t('loading')}</p>
        </div>
      </div>
    );
  }

  // Error state
  if (loadError) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 dark:text-red-400 mb-4">{loadError}</p>
        <Button variant="secondary" onClick={onCancel}>
          {t('goBack')}
        </Button>
      </div>
    );
  }

  return (
    <form className="space-y-8">
      {/* Section 1: Game Selection */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-700 pb-2">
          {t('sectionGame')}
        </h2>
        <GameSelector
          selectedGame={selectedGame}
          onGameSelect={handleGameSelect}
          error={errors.game_id?.message}
        />
      </section>

      {/* Section 2: Schedule */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-700 pb-2">
          {t('sectionSchedule')}
        </h2>
        <TimeSlotSelector
          timeSlots={timeSlots}
          selectedSlotId={watchedTimeSlotId}
          scheduledStart={watchedScheduledStart}
          scheduledEnd={watchedScheduledEnd}
          onSlotChange={(id) => setValue('time_slot_id', id)}
          onStartChange={(start) => setValue('scheduled_start', start)}
          onEndChange={(end) => setValue('scheduled_end', end)}
          slotError={errors.time_slot_id?.message}
          startError={errors.scheduled_start?.message}
          endError={errors.scheduled_end?.message}
        />
      </section>

      {/* Section 3: Session Details */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-700 pb-2">
          {t('sectionDetails')}
        </h2>

        <Input
          label={t('sessionTitle')}
          {...register('title')}
          error={errors.title?.message}
          placeholder={t('sessionTitlePlaceholder')}
        />

        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <Textarea
              label={t('description')}
              {...field}
              value={field.value || ''}
              error={errors.description?.message}
              placeholder={t('descriptionPlaceholder')}
              helperText={t('descriptionHelper')}
            />
          )}
        />

        <Select
          label={t('language')}
          {...register('language')}
          options={languageOptions}
          error={errors.language?.message}
        />
      </section>

      {/* Section 4: Player Settings */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-700 pb-2">
          {t('sectionPlayers')}
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Controller
            name="max_players_count"
            control={control}
            render={({ field }) => (
              <Input
                label={t('maxPlayers')}
                type="number"
                min={1}
                max={100}
                {...field}
                value={field.value}
                onChange={(e) => field.onChange(parseInt(e.target.value) || 1)}
                error={errors.max_players_count?.message}
              />
            )}
          />

          <Controller
            name="min_age"
            control={control}
            render={({ field }) => (
              <Input
                label={t('minAge')}
                type="number"
                min={0}
                max={99}
                {...field}
                value={field.value ?? ''}
                onChange={(e) => {
                  const val = e.target.value;
                  field.onChange(val ? parseInt(val) : null);
                }}
                error={errors.min_age?.message}
                helperText={t('minAgeHelper')}
              />
            )}
          />
        </div>

        <Controller
          name="is_accessible_disability"
          control={control}
          render={({ field }) => (
            <Checkbox
              label={t('accessibleSession')}
              checked={field.value}
              onChange={field.onChange}
            />
          )}
        />
      </section>

      {/* Section 5: Safety Tools */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-700 pb-2">
          {t('sectionSafetyTools')}
        </h2>
        <SafetyToolsSelector
          safetyTools={safetyTools}
          selectedToolIds={watchedSafetyTools}
          onToolsChange={(ids) => setValue('safety_tools', ids)}
          error={errors.safety_tools?.message}
        />
      </section>

      {/* Submit Error */}
      {submitError && (
        <Card className="p-4 border-red-500 bg-red-500/10">
          <p className="text-red-600 dark:text-red-400">{submitError}</p>
        </Card>
      )}

      {/* Actions */}
      <section className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-slate-200 dark:border-slate-700">
        {onCancel && (
          <Button
            type="button"
            variant="ghost"
            onClick={onCancel}
            disabled={isSubmitting}
            className="w-full sm:w-auto"
          >
            {t('cancel')}
          </Button>
        )}
        <div className="flex flex-col sm:flex-row gap-4 sm:ml-auto">
          <Button
            type="button"
            variant="secondary"
            onClick={handleSaveDraft}
            disabled={isSubmitting}
            className="w-full sm:w-auto"
          >
            {isSubmitting ? t('saving') : t('saveDraft')}
          </Button>
          <Button
            type="button"
            onClick={handleSubmitForReview}
            disabled={isSubmitting}
            className="w-full sm:w-auto"
          >
            {isSubmitting ? t('submitting') : t('submitForReview')}
          </Button>
        </div>
      </section>
    </form>
  );
}
