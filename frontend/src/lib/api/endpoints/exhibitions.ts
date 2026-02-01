/**
 * Exhibition API endpoints.
 */

import { api } from '../client';
import {
  ApiResponse,
  Exhibition,
  ExhibitionUpdate,
  TimeSlot,
  TimeSlotCreate,
  TimeSlotUpdate,
  SafetyTool,
  ExhibitionRoleAssignment,
  ExhibitionRoleCreate,
  ExhibitionRoleUpdate,
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
  // Time Slots
  // ==========================================================================

  /**
   * Get time slots for an exhibition.
   */
  getTimeSlots: async (exhibitionId: string): Promise<ApiResponse<TimeSlot[]>> => {
    return api.get<TimeSlot[]>(`/api/v1/exhibitions/${exhibitionId}/slots`);
  },

  /**
   * Create a time slot.
   * Requires: Exhibition organizer or SUPER_ADMIN.
   */
  createTimeSlot: async (
    exhibitionId: string,
    data: TimeSlotCreate
  ): Promise<ApiResponse<TimeSlot>> => {
    return api.post<TimeSlot>(`/api/v1/exhibitions/${exhibitionId}/slots`, data);
  },

  /**
   * Update a time slot.
   * Requires: Exhibition organizer or SUPER_ADMIN.
   */
  updateTimeSlot: async (
    exhibitionId: string,
    slotId: string,
    data: TimeSlotUpdate
  ): Promise<ApiResponse<TimeSlot>> => {
    return api.put<TimeSlot>(
      `/api/v1/exhibitions/${exhibitionId}/slots/${slotId}`,
      data
    );
  },

  /**
   * Delete a time slot.
   * Requires: Exhibition organizer or SUPER_ADMIN.
   */
  deleteTimeSlot: async (
    exhibitionId: string,
    slotId: string
  ): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/api/v1/exhibitions/${exhibitionId}/slots/${slotId}`);
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
};
