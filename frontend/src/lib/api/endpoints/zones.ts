/**
 * Zone API endpoints.
 */

import { api } from '../client';
import {
  ApiResponse,
  Zone,
  ZoneCreate,
  ZoneUpdate,
  PhysicalTable,
  PhysicalTableUpdate,
  BatchTablesCreate,
  BatchTablesResponse,
  TimeSlot,
  TimeSlotCreate,
  TimeSlotUpdate,
} from '../types';

export const zonesApi = {
  /**
   * List zones for an exhibition.
   */
  list: async (exhibitionId: string): Promise<ApiResponse<Zone[]>> => {
    return api.get<Zone[]>(`/api/v1/zones/?exhibition_id=${exhibitionId}`);
  },

  /**
   * Get a zone by ID.
   */
  getById: async (zoneId: string): Promise<ApiResponse<Zone>> => {
    return api.get<Zone>(`/api/v1/zones/${zoneId}`);
  },

  /**
   * Create a zone.
   * Requires: Exhibition organizer or SUPER_ADMIN.
   */
  create: async (data: ZoneCreate): Promise<ApiResponse<Zone>> => {
    return api.post<Zone>('/api/v1/zones/', data);
  },

  /**
   * Update a zone.
   * Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
   */
  update: async (zoneId: string, data: ZoneUpdate): Promise<ApiResponse<Zone>> => {
    return api.put<Zone>(`/api/v1/zones/${zoneId}`, data);
  },

  /**
   * Delete a zone.
   * Requires: Exhibition organizer or SUPER_ADMIN.
   */
  delete: async (zoneId: string): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/api/v1/zones/${zoneId}`);
  },

  // ==========================================================================
  // Physical Tables
  // ==========================================================================

  /**
   * List tables in a zone.
   */
  getTables: async (zoneId: string): Promise<ApiResponse<PhysicalTable[]>> => {
    return api.get<PhysicalTable[]>(`/api/v1/zones/${zoneId}/tables`);
  },

  /**
   * Batch create tables in a zone.
   * Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
   */
  createTablesBatch: async (
    zoneId: string,
    data: BatchTablesCreate
  ): Promise<ApiResponse<BatchTablesResponse>> => {
    return api.post<BatchTablesResponse>(
      `/api/v1/zones/${zoneId}/batch-tables`,
      data
    );
  },

  /**
   * Update a table.
   * Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
   */
  updateTable: async (
    zoneId: string,
    tableId: string,
    data: PhysicalTableUpdate
  ): Promise<ApiResponse<PhysicalTable>> => {
    return api.put<PhysicalTable>(
      `/api/v1/zones/${zoneId}/tables/${tableId}`,
      data
    );
  },

  /**
   * Delete a table.
   * Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
   */
  deleteTable: async (
    zoneId: string,
    tableId: string
  ): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/api/v1/zones/${zoneId}/tables/${tableId}`);
  },

  // ==========================================================================
  // Time Slots (Issue #105 - moved from exhibition level to zone level)
  // ==========================================================================

  /**
   * List time slots in a zone.
   */
  getTimeSlots: async (zoneId: string): Promise<ApiResponse<TimeSlot[]>> => {
    return api.get<TimeSlot[]>(`/api/v1/zones/${zoneId}/slots`);
  },

  /**
   * Create a time slot in a zone.
   * Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
   */
  createTimeSlot: async (
    zoneId: string,
    data: TimeSlotCreate
  ): Promise<ApiResponse<TimeSlot>> => {
    return api.post<TimeSlot>(`/api/v1/zones/${zoneId}/slots`, data);
  },

  /**
   * Update a time slot.
   * Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
   */
  updateTimeSlot: async (
    zoneId: string,
    slotId: string,
    data: TimeSlotUpdate
  ): Promise<ApiResponse<TimeSlot>> => {
    return api.put<TimeSlot>(
      `/api/v1/zones/${zoneId}/slots/${slotId}`,
      data
    );
  },

  /**
   * Delete a time slot.
   * Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
   */
  deleteTimeSlot: async (
    zoneId: string,
    slotId: string
  ): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/api/v1/zones/${zoneId}/slots/${slotId}`);
  },
};
