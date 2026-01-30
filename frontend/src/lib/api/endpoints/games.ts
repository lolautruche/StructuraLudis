/**
 * Games API endpoints.
 */

import { api } from '../client';
import { ApiResponse, Game, GameCategory, GameCreateRequest } from '../types';

export interface GameSearchParams {
  q?: string;
  category_id?: string;
  limit?: number;
  offset?: number;
}

export const gamesApi = {
  /**
   * Search/list games.
   */
  search: async (params: GameSearchParams = {}): Promise<ApiResponse<Game[]>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return api.get<Game[]>(`/api/v1/games${query ? `?${query}` : ''}`);
  },

  /**
   * Get game by ID.
   */
  getById: async (gameId: string): Promise<ApiResponse<Game>> => {
    return api.get<Game>(`/api/v1/games/${gameId}`);
  },

  /**
   * Create a new game.
   */
  create: async (game: GameCreateRequest): Promise<ApiResponse<Game>> => {
    return api.post<Game>('/api/v1/games', game);
  },

  /**
   * List all game categories.
   */
  getCategories: async (): Promise<ApiResponse<GameCategory[]>> => {
    return api.get<GameCategory[]>('/api/v1/games/categories');
  },
};
