'use client';

import { useState, useEffect, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import {
  partnerApi,
  gamesApi,
  zonesApi,
  Game,
  TimeSlot,
  PhysicalTable,
  PartnerZone,
} from '@/lib/api';
import { Button, Input, Textarea, Select } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';

const DURATION_OPTIONS = [30, 45, 60, 90, 120, 180, 240];

const sessionSchema = z.object({
  game_id: z.string().min(1, 'Required'),
  title: z.string().min(1).max(200),
  description: z.string().max(2000).optional(),
  language: z.string().optional(),
  max_players_count: z.number().min(1).max(100),
  time_slot_id: z.string().min(1, 'Required'),
  table_id: z.string().min(1, 'Required'),
  duration_minutes: z.number().min(15).max(600),
});

type SessionFormData = z.infer<typeof sessionSchema>;

interface SingleSessionCreatorProps {
  exhibitionId: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function SingleSessionCreator({ exhibitionId, onSuccess, onCancel }: SingleSessionCreatorProps) {
  const t = useTranslations('Partner');
  const tCommon = useTranslations('Common');

  const { showSuccess, showError } = useToast();

  // Data loading states
  const [games, setGames] = useState<Game[]>([]);
  const [gameSearch, setGameSearch] = useState('');
  const [isSearchingGames, setIsSearchingGames] = useState(false);
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);

  const [zones, setZones] = useState<PartnerZone[]>([]);
  const [timeSlotsByZone, setTimeSlotsByZone] = useState<Record<string, TimeSlot[]>>({});
  const [tablesByZone, setTablesByZone] = useState<Record<string, PhysicalTable[]>>({});

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SessionFormData>({
    resolver: zodResolver(sessionSchema),
    defaultValues: {
      game_id: '',
      title: '',
      description: '',
      language: '',
      max_players_count: 4,
      time_slot_id: '',
      table_id: '',
      duration_minutes: 90,
    },
  });

  const _selectedTimeSlotId = watch('time_slot_id');

  // Load time slots and partner zones (#105 - time slots now per zone)
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);

      // Load partner zones
      const zonesResponse = await partnerApi.listZones(exhibitionId);
      if (zonesResponse.data) {
        setZones(zonesResponse.data);

        // Load time slots and tables for each zone
        const timeSlotsMap: Record<string, TimeSlot[]> = {};
        const tablesMap: Record<string, PhysicalTable[]> = {};

        for (const zone of zonesResponse.data) {
          // Load time slots for this zone (#105)
          const slotsResponse = await zonesApi.getTimeSlots(zone.id);
          if (slotsResponse.data) {
            timeSlotsMap[zone.id] = slotsResponse.data;
          }

          // Load tables for this zone
          const tablesResponse = await zonesApi.getTables(zone.id);
          if (tablesResponse.data) {
            tablesMap[zone.id] = tablesResponse.data;
          }
        }

        setTimeSlotsByZone(timeSlotsMap);
        setTablesByZone(tablesMap);
      }

      setIsLoading(false);
    }

    loadData();
  }, [exhibitionId]);

  // Search games with debounce
  const searchGames = useCallback(async (query: string) => {
    if (query.length < 2) {
      setGames([]);
      return;
    }

    setIsSearchingGames(true);
    const response = await gamesApi.search({ q: query, limit: 10 });
    if (response.data) {
      setGames(response.data);
    }
    setIsSearchingGames(false);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      searchGames(gameSearch);
    }, 300);

    return () => clearTimeout(timer);
  }, [gameSearch, searchGames]);

  const handleGameSelect = (game: Game) => {
    setSelectedGame(game);
    setValue('game_id', game.id);
    setValue('title', game.title);
    setValue('max_players_count', game.max_players);
    setGameSearch('');
    setGames([]);
  };

  const clearGame = () => {
    setSelectedGame(null);
    setValue('game_id', '');
    setValue('title', '');
  };

  // Get all tables flattened with zone info
  const getAllTables = () => {
    const allTables: { table: PhysicalTable; zoneName: string }[] = [];
    for (const zone of zones) {
      const tables = tablesByZone[zone.id] || [];
      for (const table of tables) {
        allTables.push({ table, zoneName: zone.name });
      }
    }
    return allTables;
  };

  const handleFormSubmit = async (data: SessionFormData) => {
    setIsSubmitting(true);

    // Use partner API which handles table assignment and auto-validation
    const response = await partnerApi.createSession({
      exhibition_id: exhibitionId,
      game_id: data.game_id,
      title: data.title,
      description: data.description,
      language: data.language || '',
      max_players_count: data.max_players_count,
      time_slot_id: data.time_slot_id,
      table_id: data.table_id,
      duration_minutes: data.duration_minutes,
    });

    if (response.error) {
      showError(response.error.message);
      setIsSubmitting(false);
      return;
    }

    showSuccess(t('sessionCreated'));
    onSuccess?.();

    setIsSubmitting(false);
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded" />
        <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded" />
        <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded" />
      </div>
    );
  }

  const allTables = getAllTables();

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Game Selection */}
      <div>
        <label
          className="block text-sm font-medium mb-2"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('selectGame')}
        </label>

        {selectedGame ? (
          <div
            className="flex items-center justify-between p-3 rounded-lg border"
            style={{
              borderColor: 'var(--color-border)',
              backgroundColor: 'var(--color-bg-secondary)',
            }}
          >
            <div>
              <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                {selectedGame.title}
              </div>
              {selectedGame.publisher && (
                <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  {selectedGame.publisher}
                </div>
              )}
            </div>
            <Button type="button" variant="ghost" size="sm" onClick={clearGame}>
              {tCommon('change')}
            </Button>
          </div>
        ) : (
          <div className="relative">
            <Input
              value={gameSearch}
              onChange={(e) => setGameSearch(e.target.value)}
              placeholder={t('searchGamePlaceholder')}
            />
            {isSearchingGames && (
              <div
                className="absolute right-3 top-1/2 -translate-y-1/2 text-sm"
                style={{ color: 'var(--color-text-muted)' }}
              >
                ...
              </div>
            )}
            {games.length > 0 && (
              <div
                className="absolute z-10 w-full mt-1 rounded-lg border shadow-lg max-h-60 overflow-auto"
                style={{
                  borderColor: 'var(--color-border)',
                  backgroundColor: 'var(--color-bg-primary)',
                }}
              >
                {games.map((game) => (
                  <button
                    key={game.id}
                    type="button"
                    onClick={() => handleGameSelect(game)}
                    className="w-full text-left px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                      {game.title}
                    </div>
                    {game.publisher && (
                      <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                        {game.publisher} • {game.min_players}-{game.max_players} {t('players')}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {errors.game_id && (
          <p className="mt-1 text-sm text-red-500">{errors.game_id.message}</p>
        )}
      </div>

      {/* Session Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          {...register('title')}
          label={t('sessionTitle')}
          placeholder={t('sessionTitlePlaceholder')}
          error={errors.title?.message}
        />

        <Controller
          name="max_players_count"
          control={control}
          render={({ field }) => (
            <Input
              type="number"
              label={t('maxPlayers')}
              value={field.value}
              onChange={(e) => field.onChange(parseInt(e.target.value) || 1)}
              min={1}
              max={100}
              error={errors.max_players_count?.message}
            />
          )}
        />
      </div>

      <Textarea
        {...register('description')}
        label={t('sessionDescription')}
        rows={3}
        error={errors.description?.message}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          {...register('language')}
          label={t('language')}
          placeholder={t('languagePlaceholder')}
        />

        <Controller
          name="duration_minutes"
          control={control}
          render={({ field }) => (
            <Select
              label={t('duration')}
              value={String(field.value)}
              onChange={(e) => field.onChange(parseInt(e.target.value))}
              options={DURATION_OPTIONS.map((d) => ({
                value: String(d),
                label: `${d} min`,
              }))}
              error={errors.duration_minutes?.message}
            />
          )}
        />
      </div>

      {/* Time Slot Selection (grouped by zone - #105) */}
      <Controller
        name="time_slot_id"
        control={control}
        render={({ field }) => (
          <Select
            label={t('selectTimeSlot')}
            value={field.value}
            onChange={field.onChange}
            options={[
              { value: '', label: t('selectTimeSlotPlaceholder') },
              ...zones.flatMap((zone) => {
                const slots = timeSlotsByZone[zone.id] || [];
                return slots.map((slot) => ({
                  value: slot.id,
                  label: `${zone.name} - ${slot.name} (${new Date(slot.start_time).toLocaleDateString()} ${new Date(slot.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`,
                }));
              }),
            ]}
            error={errors.time_slot_id?.message}
          />
        )}
      />

      {/* Table Selection */}
      <Controller
        name="table_id"
        control={control}
        render={({ field }) => (
          <Select
            label={t('selectTable')}
            value={field.value}
            onChange={field.onChange}
            options={[
              { value: '', label: t('selectTablePlaceholder') },
              ...allTables.map(({ table, zoneName }) => ({
                value: table.id,
                label: `${zoneName} - ${table.label} (${table.capacity} places)`,
              })),
            ]}
            error={errors.table_id?.message}
          />
        )}
      />

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            {tCommon('cancel')}
          </Button>
        )}
        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? t('creating') : t('createSessionButton')}
        </Button>
      </div>
    </form>
  );
}
