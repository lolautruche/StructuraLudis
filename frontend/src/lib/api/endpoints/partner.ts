/**
 * Partner API endpoints (Issue #10).
 *
 * Dedicated endpoints for partners to manage their delegated zones.
 */

import { api } from '../client';
import {
  ApiResponse,
  PartnerZone,
  PartnerSession,
  SeriesCreateRequest,
  SeriesCreateResponse,
  SessionStatus,
} from '../types';

export const partnerApi = {
  /**
   * List zones that the current user can manage as a partner.
   * Returns zones with stats (table count, pending sessions count).
   */
  listZones: async (exhibitionId: string): Promise<ApiResponse<PartnerZone[]>> => {
    return api.get<PartnerZone[]>(`/api/v1/partner/exhibitions/${exhibitionId}/zones`);
  },

  /**
   * List sessions in zones the current partner can manage.
   * Returns sessions with computed fields (seats, game title, etc.).
   */
  listSessions: async (
    exhibitionId: string,
    options?: {
      zoneId?: string;
      status?: SessionStatus;
    }
  ): Promise<ApiResponse<PartnerSession[]>> => {
    const params = new URLSearchParams();
    if (options?.zoneId) {
      params.append('zone_id', options.zoneId);
    }
    if (options?.status) {
      params.append('status', options.status);
    }
    const queryString = params.toString();
    const url = `/api/v1/partner/exhibitions/${exhibitionId}/sessions${queryString ? `?${queryString}` : ''}`;
    return api.get<PartnerSession[]>(url);
  },

  /**
   * Create a series of sessions (batch creation).
   * Creates multiple sessions with the same game/settings across
   * the specified time slots, rotating through the provided tables.
   */
  createSeries: async (
    data: SeriesCreateRequest
  ): Promise<ApiResponse<SeriesCreateResponse>> => {
    return api.post<SeriesCreateResponse>('/api/v1/partner/sessions/batch', data);
  },
};
