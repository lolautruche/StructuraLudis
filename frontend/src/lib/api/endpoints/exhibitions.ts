/**
 * Exhibition API endpoints.
 */

import { api } from '../client';
import {
  ApiResponse,
  Exhibition,
  ExhibitionUpdate,
  SafetyTool,
  ExhibitionRoleAssignment,
  ExhibitionRoleCreate,
  ExhibitionRoleUpdate,
  UserSearchResult,
  ExhibitionRegistration,
} from '../types';

export const exhibitionsApi = {
  /**
   * Get exhibition by ID.
   */
  getById: async (exhibitionId: string): Promise<ApiResponse<Exhibition>> => {
    return api.get<Exhibition>(`/api/v1/exhibitions/${exhibitionId}`);
  },

  /**
   * List all exhibitions.
   */
  list: async (): Promise<ApiResponse<Exhibition[]>> => {
    return api.get<Exhibition[]>('/api/v1/exhibitions/');
  },

  /**
   * Update an exhibition.
   * Requires: Exhibition organizer or SUPER_ADMIN.
   */
  update: async (
    exhibitionId: string,
    data: ExhibitionUpdate
  ): Promise<ApiResponse<Exhibition>> => {
    return api.put<Exhibition>(`/api/v1/exhibitions/${exhibitionId}`, data);
  },

  // ==========================================================================
  // Safety Tools
  // ==========================================================================

  /**
   * Get safety tools for an exhibition.
   */
  getSafetyTools: async (exhibitionId: string): Promise<ApiResponse<SafetyTool[]>> => {
    return api.get<SafetyTool[]>(`/api/v1/exhibitions/${exhibitionId}/safety-tools`);
  },

  // ==========================================================================
  // Exhibition Roles (Issue #99)
  // ==========================================================================

  /**
   * Search users for role assignment.
   * Returns users matching query who don't already have a role for this exhibition.
   * Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.
   */
  searchUsers: async (
    exhibitionId: string,
    query: string
  ): Promise<ApiResponse<UserSearchResult[]>> => {
    return api.get<UserSearchResult[]>(
      `/api/v1/exhibitions/${exhibitionId}/users/search?q=${encodeURIComponent(query)}`
    );
  },

  /**
   * List role assignments for an exhibition.
   * Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.
   */
  listRoles: async (exhibitionId: string): Promise<ApiResponse<ExhibitionRoleAssignment[]>> => {
    return api.get<ExhibitionRoleAssignment[]>(`/api/v1/exhibitions/${exhibitionId}/roles`);
  },

  /**
   * Assign a role to a user for an exhibition.
   * Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.
   */
  assignRole: async (
    exhibitionId: string,
    data: ExhibitionRoleCreate
  ): Promise<ApiResponse<ExhibitionRoleAssignment>> => {
    return api.post<ExhibitionRoleAssignment>(`/api/v1/exhibitions/${exhibitionId}/roles`, data);
  },

  /**
   * Update a role assignment.
   * Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.
   */
  updateRole: async (
    exhibitionId: string,
    roleId: string,
    data: ExhibitionRoleUpdate
  ): Promise<ApiResponse<ExhibitionRoleAssignment>> => {
    return api.patch<ExhibitionRoleAssignment>(
      `/api/v1/exhibitions/${exhibitionId}/roles/${roleId}`,
      data
    );
  },

  /**
   * Remove a role assignment.
   * Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.
   */
  removeRole: async (
    exhibitionId: string,
    roleId: string
  ): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/api/v1/exhibitions/${exhibitionId}/roles/${roleId}`);
  },

  // ==========================================================================
  // Exhibition Registration (Issue #77)
  // ==========================================================================

  /**
   * Register the current user to an exhibition.
   * Requires authenticated user with verified email.
   */
  register: async (exhibitionId: string): Promise<ApiResponse<ExhibitionRegistration>> => {
    return api.post<ExhibitionRegistration>(`/api/v1/exhibitions/${exhibitionId}/register`);
  },

  /**
   * Get the current user's registration for an exhibition.
   * Returns null if not registered.
   */
  getRegistration: async (exhibitionId: string): Promise<ApiResponse<ExhibitionRegistration | null>> => {
    return api.get<ExhibitionRegistration | null>(`/api/v1/exhibitions/${exhibitionId}/registration`);
  },

  /**
   * Cancel the current user's registration for an exhibition.
   * Cannot unregister if user has active bookings.
   */
  unregister: async (exhibitionId: string): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/api/v1/exhibitions/${exhibitionId}/registration`);
  },
};
