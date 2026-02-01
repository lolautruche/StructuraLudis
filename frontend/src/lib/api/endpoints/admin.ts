/**
 * Admin API endpoints.
 *
 * SuperAdmin operations for user and platform management.
 */

import { api } from '../client';
import {
  ApiResponse,
  AdminUser,
  GlobalRole,
  PlatformStats,
  Exhibition,
  ExhibitionCreate,
} from '../types';

interface ListUsersParams {
  role?: GlobalRole;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

interface ListExhibitionsParams {
  status?: string;
  skip?: number;
  limit?: number;
}

export const adminApi = {
  /**
   * List all users with optional filters.
   * Requires: SUPER_ADMIN
   */
  listUsers: async (params?: ListUsersParams): Promise<ApiResponse<AdminUser[]>> => {
    const searchParams = new URLSearchParams();
    if (params?.role) searchParams.set('role', params.role);
    if (params?.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
    if (params?.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return api.get<AdminUser[]>(`/api/v1/admin/users${query ? `?${query}` : ''}`);
  },

  /**
   * Get a specific user by ID.
   * Requires: SUPER_ADMIN
   */
  getUser: async (userId: string): Promise<ApiResponse<AdminUser>> => {
    return api.get<AdminUser>(`/api/v1/admin/users/${userId}`);
  },

  /**
   * Update a user's global role.
   * Requires: SUPER_ADMIN
   */
  updateUserRole: async (
    userId: string,
    globalRole: GlobalRole
  ): Promise<ApiResponse<AdminUser>> => {
    return api.patch<AdminUser>(`/api/v1/admin/users/${userId}/role`, {
      global_role: globalRole,
    });
  },

  /**
   * Activate or deactivate a user.
   * Requires: SUPER_ADMIN
   */
  updateUserStatus: async (
    userId: string,
    isActive: boolean
  ): Promise<ApiResponse<AdminUser>> => {
    return api.patch<AdminUser>(`/api/v1/admin/users/${userId}/status`, {
      is_active: isActive,
    });
  },

  /**
   * List all exhibitions across all organizations.
   * Requires: SUPER_ADMIN
   */
  listExhibitions: async (
    params?: ListExhibitionsParams
  ): Promise<ApiResponse<Exhibition[]>> => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return api.get<Exhibition[]>(`/api/v1/admin/exhibitions${query ? `?${query}` : ''}`);
  },

  /**
   * Get platform-wide statistics.
   * Requires: SUPER_ADMIN
   */
  getStats: async (): Promise<ApiResponse<PlatformStats>> => {
    return api.get<PlatformStats>('/api/v1/admin/stats');
  },

  /**
   * Create a new exhibition.
   * Requires: ORGANIZER or SUPER_ADMIN
   */
  createExhibition: async (data: ExhibitionCreate): Promise<ApiResponse<Exhibition>> => {
    return api.post<Exhibition>('/api/v1/exhibitions/', data);
  },
};
