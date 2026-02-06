'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Input, Button, Select, Card } from '@/components/ui';
import { gamesApi } from '@/lib/api';
import { ProviderBadge } from '@/components/games/ProviderBadge';
import type { Game, GameCategory, GameComplexity } from '@/lib/api/types';

interface GameSelectorProps {
  selectedGame: Game | null;
  onGameSelect: (game: Game) => void;
  error?: string;
}

interface InlineGameForm {
  title: string;
  category_id: string;
  publisher: string;
  min_players: number;
  max_players: number;
  complexity: GameComplexity;
}

const defaultInlineForm: InlineGameForm = {
  title: '',
  category_id: '',
  publisher: '',
  min_players: 2,
  max_players: 6,
  complexity: 'INTERMEDIATE',
};

export function GameSelector({ selectedGame, onGameSelect, error }: GameSelectorProps) {
  const t = useTranslations('SessionForm');

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Game[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Category filter
  const [categories, setCategories] = useState<GameCategory[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');

  // Inline creation state
  const [showInlineForm, setShowInlineForm] = useState(false);
  const [inlineForm, setInlineForm] = useState<InlineGameForm>(defaultInlineForm);
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Load categories
  useEffect(() => {
    async function loadCategories() {
      const response = await gamesApi.getCategories();
      if (response.data) {
        setCategories(response.data);
      }
    }
    loadCategories();
  }, []);

  // Search games
  const searchGames = useCallback(async () => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    const response = await gamesApi.search({
      q: searchQuery,
      category_id: selectedCategoryId || undefined,
      limit: 10,
    });

    if (response.data) {
      setSearchResults(response.data);
    }
    setIsSearching(false);
  }, [searchQuery, selectedCategoryId]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(searchGames, 300);
    return () => clearTimeout(timer);
  }, [searchGames]);

  // Close results on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle game selection
  const handleSelectGame = (game: Game) => {
    onGameSelect(game);
    setShowResults(false);
    setSearchQuery('');
  };

  // Handle inline game creation
  const handleCreateGame = async () => {
    setCreateError(null);

    if (!inlineForm.title.trim()) {
      setCreateError(t('gameRequired'));
      return;
    }
    if (!inlineForm.category_id) {
      setCreateError(t('categoryRequired'));
      return;
    }
    if (inlineForm.min_players > inlineForm.max_players) {
      setCreateError(t('invalidPlayerRange'));
      return;
    }

    setIsCreating(true);
    const response = await gamesApi.create({
      title: inlineForm.title.trim(),
      category_id: inlineForm.category_id,
      publisher: inlineForm.publisher.trim() || undefined,
      min_players: inlineForm.min_players,
      max_players: inlineForm.max_players,
      complexity: inlineForm.complexity,
    });

    if (response.data) {
      onGameSelect(response.data);
      setShowInlineForm(false);
      setInlineForm(defaultInlineForm);
    } else {
      setCreateError(response.error?.message || t('createGameError'));
    }
    setIsCreating(false);
  };

  // Complexity options
  const complexityOptions = [
    { value: 'BEGINNER', label: t('complexityBeginner') },
    { value: 'INTERMEDIATE', label: t('complexityIntermediate') },
    { value: 'ADVANCED', label: t('complexityAdvanced') },
    { value: 'EXPERT', label: t('complexityExpert') },
  ];

  // If a game is selected, show it
  if (selectedGame) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-600 dark:text-slate-300">
          {t('game')}
        </label>
        <Card className="p-3">
          <div className="flex gap-3">
            {/* Cover image */}
            {selectedGame.cover_image_url && (
              <img
                src={selectedGame.cover_image_url}
                alt={selectedGame.title}
                className="w-20 h-28 object-cover rounded flex-shrink-0"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-slate-900 dark:text-white">{selectedGame.title}</p>
                  {selectedGame.external_provider && (
                    <ProviderBadge provider={selectedGame.external_provider} />
                  )}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => onGameSelect(null as unknown as Game)}
                >
                  {t('change')}
                </Button>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {selectedGame.publisher && `${selectedGame.publisher} - `}
                {selectedGame.min_players}-{selectedGame.max_players} {t('players')}
              </p>
              {/* Themes */}
              {selectedGame.themes && selectedGame.themes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedGame.themes.map((theme) => (
                    <span
                      key={theme}
                      className="inline-block px-1.5 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                    >
                      {theme}
                    </span>
                  ))}
                </div>
              )}
              {/* External link */}
              {selectedGame.external_url && selectedGame.external_provider && (
                <a
                  href={selectedGame.external_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-1.5 text-xs text-ludis-primary hover:underline"
                >
                  {t('viewOnProvider', { provider: selectedGame.external_provider.toUpperCase() })}
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
            </div>
          </div>
        </Card>
        {error && <p className="text-sm text-red-500">{error}</p>}
      </div>
    );
  }

  // Inline creation form
  if (showInlineForm) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-slate-600 dark:text-slate-300">
            {t('createNewGame')}
          </label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowInlineForm(false)}
          >
            {t('cancel')}
          </Button>
        </div>

        <Card className="p-4 space-y-4">
          <Input
            label={t('gameTitle')}
            value={inlineForm.title}
            onChange={(e) => setInlineForm((f) => ({ ...f, title: e.target.value }))}
            placeholder={t('gameTitlePlaceholder')}
          />

          <Select
            label={t('category')}
            value={inlineForm.category_id}
            onChange={(e) => setInlineForm((f) => ({ ...f, category_id: e.target.value }))}
            options={categories.map((c) => ({ value: c.id, label: c.name }))}
            placeholder={t('selectCategory')}
          />

          <Input
            label={t('publisher')}
            value={inlineForm.publisher}
            onChange={(e) => setInlineForm((f) => ({ ...f, publisher: e.target.value }))}
            placeholder={t('publisherPlaceholder')}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label={t('minPlayers')}
              type="number"
              min={1}
              max={100}
              value={inlineForm.min_players}
              onChange={(e) => setInlineForm((f) => ({ ...f, min_players: parseInt(e.target.value) || 1 }))}
            />
            <Input
              label={t('maxPlayers')}
              type="number"
              min={1}
              max={100}
              value={inlineForm.max_players}
              onChange={(e) => setInlineForm((f) => ({ ...f, max_players: parseInt(e.target.value) || 1 }))}
            />
          </div>

          <Select
            label={t('complexity')}
            value={inlineForm.complexity}
            onChange={(e) => setInlineForm((f) => ({ ...f, complexity: e.target.value as GameComplexity }))}
            options={complexityOptions}
          />

          {createError && <p className="text-sm text-red-500">{createError}</p>}

          <Button
            type="button"
            onClick={handleCreateGame}
            disabled={isCreating}
            className="w-full"
          >
            {isCreating ? t('creating') : t('createGame')}
          </Button>
        </Card>
      </div>
    );
  }

  // Search mode
  return (
    <div className="space-y-2" ref={searchRef}>
      <label className="block text-sm font-medium text-slate-600 dark:text-slate-300">
        {t('game')}
      </label>

      {/* Category filter */}
      <Select
        value={selectedCategoryId}
        onChange={(e) => setSelectedCategoryId(e.target.value)}
        options={[
          { value: '', label: t('allCategories') },
          ...categories.map((c) => ({ value: c.id, label: c.name })),
        ]}
      />

      {/* Search input */}
      <div className="relative">
        <Input
          type="search"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setShowResults(true);
          }}
          onFocus={() => setShowResults(true)}
          placeholder={t('searchGames')}
          error={error}
        />

        {/* Search results dropdown */}
        {showResults && searchQuery.length >= 2 && (
          <div className="absolute z-10 w-full mt-1 bg-white dark:bg-ludis-card border border-slate-300 dark:border-slate-600 rounded-lg shadow-lg max-h-80 overflow-y-auto">
            {isSearching ? (
              <div className="p-4 text-center text-slate-600 dark:text-slate-400">
                {t('searching')}
              </div>
            ) : searchResults.length > 0 ? (
              <ul>
                {searchResults.map((game) => (
                  <li key={game.id}>
                    <button
                      type="button"
                      className="w-full px-4 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700 focus:bg-slate-100 dark:focus:bg-slate-700 focus:outline-none min-h-[44px] flex items-center gap-3"
                      onClick={() => handleSelectGame(game)}
                    >
                      {game.cover_image_url && (
                        <img
                          src={game.cover_image_url}
                          alt=""
                          className="w-10 h-14 object-cover rounded flex-shrink-0"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                      )}
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-slate-900 dark:text-white">{game.title}</p>
                          {game.external_provider && (
                            <ProviderBadge provider={game.external_provider} />
                          )}
                        </div>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          {game.publisher && `${game.publisher} - `}
                          {game.min_players}-{game.max_players} {t('players')}
                        </p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-4 text-center">
                <p className="text-slate-600 dark:text-slate-400 mb-2">{t('noGamesFound')}</p>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setShowInlineForm(true);
                    setShowResults(false);
                    setInlineForm((f) => ({ ...f, title: searchQuery }));
                  }}
                >
                  {t('createNewGameButton')}
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create new game link */}
      <p className="text-sm text-slate-600 dark:text-slate-400">
        {t('cantFindGame')}{' '}
        <button
          type="button"
          className="text-ludis-primary hover:underline"
          onClick={() => setShowInlineForm(true)}
        >
          {t('createNewGameButton')}
        </button>
      </p>
    </div>
  );
}
