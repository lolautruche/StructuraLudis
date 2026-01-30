/**
 * Exhibition API endpoints.
 */

import { api } from '../client';
import { ApiResponse, Exhibition, TimeSlot, SafetyTool } from '../types';

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
   * Get time slots for an exhibition.
   */
  getTimeSlots: async (exhibitionId: string): Promise<ApiResponse<TimeSlot[]>> => {
    return api.get<TimeSlot[]>(`/api/v1/exhibitions/${exhibitionId}/slots`);
  },

  /**
   * Get safety tools for an exhibition.
   */
  getSafetyTools: async (exhibitionId: string): Promise<ApiResponse<SafetyTool[]>> => {
    return api.get<SafetyTool[]>(`/api/v1/exhibitions/${exhibitionId}/safety-tools`);
  },
};
