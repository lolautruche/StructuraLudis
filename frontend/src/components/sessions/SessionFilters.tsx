'use client';

import { useTranslations } from 'next-intl';
import { useCallback } from 'react';
import { Input, Button, Checkbox } from '@/components/ui';

export interface SessionFiltersState {
  query: string;
  hasSeats: boolean;
  language: string;
}

interface SessionFiltersProps {
  filters: SessionFiltersState;
  onFiltersChange: (filters: SessionFiltersState) => void;
  onReset: () => void;
  languages?: string[];
}

export function SessionFilters({
  filters,
  onFiltersChange,
  onReset,
  languages = ['fr', 'en'],
}: SessionFiltersProps) {
  const t = useTranslations('Discovery');

  const updateFilter = useCallback(
    <K extends keyof SessionFiltersState>(key: K, value: SessionFiltersState[K]) => {
      onFiltersChange({ ...filters, [key]: value });
    },
    [filters, onFiltersChange]
  );

  const hasActiveFilters = filters.query || filters.hasSeats || filters.language;

  return (
    <div className="space-y-4">
      {/* Search */}
      <Input
        type="search"
        placeholder={t('searchPlaceholder')}
        value={filters.query}
        onChange={(e) => updateFilter('query', e.target.value)}
        className="w-full"
      />

      {/* Filter row - responsive */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Has seats checkbox */}
        <Checkbox
          checked={filters.hasSeats}
          onChange={(e) => updateFilter('hasSeats', e.target.checked)}
          label={t('hasSeats')}
        />

        {/* Language filter */}
        <div className="flex items-center gap-2">
          <select
            value={filters.language}
            onChange={(e) => updateFilter('language', e.target.value)}
            className="bg-white dark:bg-ludis-card border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-ludis-primary"
          >
            <option value="">{t('allSessions')}</option>
            {languages.map((lang) => (
              <option key={lang} value={lang}>
                {lang.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Reset filters */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={onReset}>
            ✕ Reset
          </Button>
        )}
      </div>
    </div>
  );
}

export const defaultFilters: SessionFiltersState = {
  query: '',
  hasSeats: false,
  language: '',
};
