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
};
