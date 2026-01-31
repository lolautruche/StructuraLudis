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
    // Build URL with trailing slash to satisfy FastAPI's redirect_slashes=False
    const url = new URL('/api/v1/games/', window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.append(key, String(value));
      }
    });
    const path = url.pathname + url.search;
    return api.get<Game[]>(path);
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
    return api.post<Game>('/api/v1/games/', game);
  },

  /**
   * List all game categories.
   */
  getCategories: async (): Promise<ApiResponse<GameCategory[]>> => {
    // No trailing slash - backend route is /categories not /categories/
    return api.get<GameCategory[]>('/api/v1/games/categories');
  },
};
