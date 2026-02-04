'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { Card, Select, Checkbox } from '@/components/ui';
import { ExhibitionCard } from '@/components/exhibitions';
import { exhibitionsApi, ExhibitionFilters } from '@/lib/api';
import { REGIONS } from '@/components/admin/ExhibitionSettingsForm';
import type { Exhibition } from '@/lib/api/types';

// Generate year options (current year - 1 to current year + 2)
function getYearOptions() {
  const currentYear = new Date().getFullYear();
  const years = [];
  for (let y = currentYear - 1; y <= currentYear + 2; y++) {
    years.push({ value: y.toString(), label: y.toString() });
  }
  return years;
}

// Generate month options (1-12)
function getMonthOptions(t: (key: string) => string) {
  return [
    { value: '1', label: t('months.january') },
    { value: '2', label: t('months.february') },
    { value: '3', label: t('months.march') },
    { value: '4', label: t('months.april') },
    { value: '5', label: t('months.may') },
    { value: '6', label: t('months.june') },
    { value: '7', label: t('months.july') },
    { value: '8', label: t('months.august') },
    { value: '9', label: t('months.september') },
    { value: '10', label: t('months.october') },
    { value: '11', label: t('months.november') },
    { value: '12', label: t('months.december') },
  ];
}

export default function ExhibitionsPage() {
  const t = useTranslations('Exhibition');
  const tAdmin = useTranslations('Admin');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [exhibitions, setExhibitions] = useState<Exhibition[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Read filters from URL
  const filters: ExhibitionFilters = useMemo(() => ({
    region: searchParams.get('region') || undefined,
    year: searchParams.get('year') ? parseInt(searchParams.get('year')!) : undefined,
    month: searchParams.get('month') ? parseInt(searchParams.get('month')!) : undefined,
    registration_open: searchParams.get('registration_open') === 'true' ? true : undefined,
  }), [searchParams]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.region) count++;
    if (filters.year) count++;
    if (filters.month) count++;
    if (filters.registration_open) count++;
    return count;
  }, [filters]);

  // Update URL with new filters
  const updateFilters = useCallback((newFilters: Partial<ExhibitionFilters>) => {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(newFilters).forEach(([key, value]) => {
      if (value === undefined || value === '' || value === false) {
        params.delete(key);
      } else {
        params.set(key, value.toString());
      }
    });

    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  }, [searchParams, router, pathname]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    router.push(pathname);
  }, [router, pathname]);

  useEffect(() => {
    async function fetchExhibitions() {
      setIsLoading(true);
      const response = await exhibitionsApi.list(filters);
      if (response.data) {
        // Sort by start_date
        const sorted = response.data.sort((a, b) =>
          new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
        );
        setExhibitions(sorted);
      }
      setIsLoading(false);
    }
    fetchExhibitions();
  }, [filters]);

  // Separate current/upcoming from past exhibitions
  const { currentAndUpcoming, past } = useMemo(() => {
    const now = new Date();
    const current: Exhibition[] = [];
    const pastExhibitions: Exhibition[] = [];

    exhibitions.forEach((exhibition) => {
      const endDate = new Date(exhibition.end_date);
      if (endDate < now) {
        pastExhibitions.push(exhibition);
      } else {
        current.push(exhibition);
      }
    });

    return {
      currentAndUpcoming: current,
      past: pastExhibitions.reverse(), // Most recent past first
    };
  }, [exhibitions]);

  const yearOptions = getYearOptions();
  const monthOptions = getMonthOptions(t);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">{t('selectEvent')}</p>
      </div>

      {/* Filters (Issue #95) */}
      <Card>
        <Card.Content className="py-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Region filter */}
            <div className="min-w-[180px]">
              <Select
                value={filters.region || ''}
                onChange={(e) => updateFilters({ region: e.target.value || undefined })}
                options={[
                  { value: '', label: t('filters.allRegions') },
                  ...REGIONS.map((r) => ({ value: r.value, label: tAdmin(r.labelKey) })),
                ]}
                aria-label={t('filters.region')}
              />
            </div>

            {/* Year filter */}
            <div className="min-w-[100px]">
              <Select
                value={filters.year?.toString() || ''}
                onChange={(e) => updateFilters({
                  year: e.target.value ? parseInt(e.target.value) : undefined,
                  // Clear month if year is cleared
                  ...(e.target.value ? {} : { month: undefined }),
                })}
                options={[
                  { value: '', label: t('filters.allYears') },
                  ...yearOptions,
                ]}
                aria-label={t('filters.year')}
              />
            </div>

            {/* Month filter (only if year is selected) */}
            {filters.year && (
              <div className="min-w-[120px]">
                <Select
                  value={filters.month?.toString() || ''}
                  onChange={(e) => updateFilters({ month: e.target.value ? parseInt(e.target.value) : undefined })}
                  options={[
                    { value: '', label: t('filters.allMonths') },
                    ...monthOptions,
                  ]}
                  aria-label={t('filters.month')}
                />
              </div>
            )}

            {/* Registration open filter */}
            <div className="flex items-center">
              <Checkbox
                checked={filters.registration_open || false}
                onChange={(e) => updateFilters({ registration_open: e.target.checked || undefined })}
                label={t('filters.registrationOpen')}
              />
            </div>

            {/* Active filter count & clear */}
            {activeFilterCount > 0 && (
              <div className="flex items-center gap-2 ml-auto">
                <span className="text-sm text-slate-500">
                  {t('filters.activeFilters', { count: activeFilterCount })}
                </span>
                <button
                  onClick={clearFilters}
                  className="text-sm text-ludis-primary hover:text-ludis-primary-dark underline"
                >
                  {t('filters.clearAll')}
                </button>
              </div>
            )}
          </div>
        </Card.Content>
      </Card>

      {/* Results count */}
      {!isLoading && (
        <p className="text-sm text-slate-500">
          {t('filters.resultsCount', { count: exhibitions.length })}
        </p>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <Card.Content className="space-y-4">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
              </Card.Content>
            </Card>
          ))}
        </div>
      ) : exhibitions.length === 0 ? (
        <Card>
          <Card.Content className="text-center py-12">
            <div className="text-4xl mb-4">📅</div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              {activeFilterCount > 0 ? t('noEventsWithFilters') : t('noEvents')}
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              {activeFilterCount > 0 ? t('noEventsWithFiltersDescription') : t('noEventsDescription')}
            </p>
            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className="mt-4 text-ludis-primary hover:text-ludis-primary-dark underline"
              >
                {t('filters.clearAll')}
              </button>
            )}
          </Card.Content>
        </Card>
      ) : (
        <>
          {/* Current & Upcoming Events */}
          {currentAndUpcoming.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-4">{t('upcomingAndCurrent')}</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {currentAndUpcoming.map((exhibition) => (
                  <ExhibitionCard
                    key={exhibition.id}
                    exhibition={exhibition}
                    locale={locale}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Past Events */}
          {past.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-4 text-slate-500 dark:text-slate-400">{t('pastEvents')}</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 opacity-75">
                {past.map((exhibition) => (
                  <ExhibitionCard
                    key={exhibition.id}
                    exhibition={exhibition}
                    locale={locale}
                  />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
