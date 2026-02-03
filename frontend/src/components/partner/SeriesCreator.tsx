'use client';

import { useState, useEffect, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslations } from 'next-intl';
import {
  partnerApi,
  exhibitionsApi,
  gamesApi,
  zonesApi,
  Game,
  TimeSlot,
  PhysicalTable,
  PartnerZone,
} from '@/lib/api';
import { Button, Input, Textarea, Select, Checkbox, Card } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';

const DURATION_OPTIONS = [30, 45, 60, 90, 120, 180, 240];

const seriesSchema = z.object({
  game_id: z.string().min(1, 'Required'),
  title: z.string().min(1).max(200),
  description: z.string().max(2000).optional(),
  language: z.string().optional(),
  max_players_count: z.number().min(1).max(100),
  duration_minutes: z.number().min(15).max(600),
  time_slot_ids: z.array(z.string()).min(1, 'Select at least one time slot'),
  table_ids: z.array(z.string()).min(1, 'Select at least one table'),
});

type SeriesFormData = z.infer<typeof seriesSchema>;

interface SeriesCreatorProps {
  exhibitionId: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function SeriesCreator({ exhibitionId, onSuccess, onCancel }: SeriesCreatorProps) {
  const t = useTranslations('Partner');
  const tCommon = useTranslations('Common');

  const { showSuccess, showError } = useToast();

  // Data loading states
  const [games, setGames] = useState<Game[]>([]);
  const [gameSearch, setGameSearch] = useState('');
  const [isSearchingGames, setIsSearchingGames] = useState(false);
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);

  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [zones, setZones] = useState<PartnerZone[]>([]);
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
  } = useForm<SeriesFormData>({
    resolver: zodResolver(seriesSchema),
    defaultValues: {
      game_id: '',
      title: '',
      description: '',
      language: '',
      max_players_count: 4,
      duration_minutes: 90,
      time_slot_ids: [],
      table_ids: [],
    },
  });

  const selectedTimeSlotIds = watch('time_slot_ids');
  const selectedTableIds = watch('table_ids');

  // Load time slots and partner zones
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);

      // Load time slots
      const slotsResponse = await exhibitionsApi.getTimeSlots(exhibitionId);
      if (slotsResponse.data) {
        setTimeSlots(slotsResponse.data);
      }

      // Load partner zones
      const zonesResponse = await partnerApi.listZones(exhibitionId);
      if (zonesResponse.data) {
        setZones(zonesResponse.data);

        // Load tables for each zone
        const tablesMap: Record<string, PhysicalTable[]> = {};
        for (const zone of zonesResponse.data) {
          const tablesResponse = await zonesApi.getTables(zone.id);
          if (tablesResponse.data) {
            tablesMap[zone.id] = tablesResponse.data;
          }
        }
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

  const toggleTimeSlot = (slotId: string) => {
    const current = selectedTimeSlotIds || [];
    if (current.includes(slotId)) {
      setValue(
        'time_slot_ids',
        current.filter((id) => id !== slotId)
      );
    } else {
      setValue('time_slot_ids', [...current, slotId]);
    }
  };

  const toggleTable = (tableId: string) => {
    const current = selectedTableIds || [];
    if (current.includes(tableId)) {
      setValue(
        'table_ids',
        current.filter((id) => id !== tableId)
      );
    } else {
      setValue('table_ids', [...current, tableId]);
    }
  };

  const handleFormSubmit = async (data: SeriesFormData) => {
    setIsSubmitting(true);

    const response = await partnerApi.createSeries({
      exhibition_id: exhibitionId,
      game_id: data.game_id,
      title: data.title,
      description: data.description,
      language: data.language,
      max_players_count: data.max_players_count,
      duration_minutes: data.duration_minutes,
      time_slot_ids: data.time_slot_ids,
      table_ids: data.table_ids,
    });

    if (response.error) {
      showError(response.error.message);
    } else if (response.data) {
      showSuccess(t('seriesCreated', { count: response.data.created_count }));
      onSuccess?.();
    }

    setIsSubmitting(false);
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded" />
        <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded" />
        <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded" />
      </div>
    );
  }

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
                        {game.publisher} • {game.min_players}-{game.max_players} players
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

      {/* Time Slots Selection */}
      <div>
        <label
          className="block text-sm font-medium mb-2"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('selectTimeSlots')}
        </label>
        <p className="text-sm mb-3" style={{ color: 'var(--color-text-secondary)' }}>
          {t('selectTimeSlotsHelp')}
        </p>

        {timeSlots.length === 0 ? (
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            {t('noTimeSlots')}
          </p>
        ) : (
          <div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 p-3 rounded-lg border"
            style={{
              borderColor: 'var(--color-border)',
              backgroundColor: 'var(--color-bg-secondary)',
            }}
          >
            {timeSlots.map((slot) => {
              const isSelected = selectedTimeSlotIds?.includes(slot.id);
              return (
                <button
                  key={slot.id}
                  type="button"
                  onClick={() => toggleTimeSlot(slot.id)}
                  className={`p-2 rounded border text-left transition-colors ${
                    isSelected
                      ? 'border-ludis-primary bg-ludis-primary/10'
                      : 'border-transparent hover:border-slate-300 dark:hover:border-slate-600'
                  }`}
                  style={{
                    backgroundColor: isSelected ? undefined : 'var(--color-bg-primary)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <Checkbox checked={isSelected} readOnly />
                    <div>
                      <div
                        className="text-sm font-medium"
                        style={{ color: 'var(--color-text-primary)' }}
                      >
                        {slot.name}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                        {formatDate(slot.start_time)} {formatTime(slot.start_time)} -{' '}
                        {formatTime(slot.end_time)}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
        {errors.time_slot_ids && (
          <p className="mt-1 text-sm text-red-500">{errors.time_slot_ids.message}</p>
        )}
      </div>

      {/* Tables Selection */}
      <div>
        <label
          className="block text-sm font-medium mb-2"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {t('selectTables')}
        </label>
        <p className="text-sm mb-3" style={{ color: 'var(--color-text-secondary)' }}>
          {t('selectTablesHelp')}
        </p>

        {zones.length === 0 ? (
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            {t('noZonesAssigned')}
          </p>
        ) : (
          <div className="space-y-3">
            {zones.map((zone) => {
              const tables = tablesByZone[zone.id] || [];
              if (tables.length === 0) return null;

              return (
                <Card key={zone.id}>
                  <Card.Content className="p-3">
                    <div
                      className="text-sm font-medium mb-2"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {zone.name}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {tables.map((table) => {
                        const isSelected = selectedTableIds?.includes(table.id);
                        return (
                          <button
                            key={table.id}
                            type="button"
                            onClick={() => toggleTable(table.id)}
                            className={`px-3 py-1.5 rounded border text-sm transition-colors ${
                              isSelected
                                ? 'border-ludis-primary bg-ludis-primary/10 text-ludis-primary'
                                : 'border-slate-300 dark:border-slate-600 hover:border-ludis-primary'
                            }`}
                          >
                            {table.label}
                          </button>
                        );
                      })}
                    </div>
                  </Card.Content>
                </Card>
              );
            })}
          </div>
        )}
        {errors.table_ids && (
          <p className="mt-1 text-sm text-red-500">{errors.table_ids.message}</p>
        )}
      </div>

      {/* Summary */}
      {selectedTimeSlotIds?.length > 0 && selectedTableIds?.length > 0 && (
        <div
          className="p-3 rounded-lg border"
          style={{
            borderColor: 'var(--color-primary)',
            backgroundColor: 'var(--color-primary-light)',
          }}
        >
          <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>
            {t('seriesSummary', {
              sessions: selectedTimeSlotIds.length * selectedTableIds.length,
              slots: selectedTimeSlotIds.length,
              tables: selectedTableIds.length,
            })}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            {tCommon('cancel')}
          </Button>
        )}
        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? t('creating') : t('createSeries')}
        </Button>
      </div>
    </form>
  );
}
