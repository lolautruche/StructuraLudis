/**
 * Game Sessions API endpoints.
 */

import { api } from '../client';
import { ApiResponse, Booking, GameSession } from '../types';

export interface SessionSearchParams {
  q?: string;
  status?: string;
  has_available_seats?: boolean;
  language?: string;
  zone_id?: string;
  min_age_lte?: number;
  limit?: number;
  offset?: number;
}

export interface SessionSearchResult {
  items: GameSession[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const sessionsApi = {
  /**
   * Search sessions globally or within an exhibition.
   */
  search: async (
    params: SessionSearchParams & { exhibition_id?: string } = {}
  ): Promise<ApiResponse<SessionSearchResult>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return api.get<SessionSearchResult>(
      `/api/v1/sessions/search${query ? `?${query}` : ''}`
    );
  },

  /**
   * Search sessions within an exhibition.
   */
  searchInExhibition: async (
    exhibitionId: string,
    params: SessionSearchParams = {}
  ): Promise<ApiResponse<SessionSearchResult>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return api.get<SessionSearchResult>(
      `/api/v1/exhibitions/${exhibitionId}/sessions/search${query ? `?${query}` : ''}`
    );
  },

  /**
   * Get session by ID.
   */
  getById: async (sessionId: string): Promise<ApiResponse<GameSession>> => {
    return api.get<GameSession>(`/api/v1/sessions/${sessionId}`);
  },

  /**
   * Book a seat in a session.
   */
  book: async (sessionId: string): Promise<ApiResponse<Booking>> => {
    return api.post<Booking>(`/api/v1/sessions/${sessionId}/book`);
  },

  /**
   * Join waitlist for a session.
   */
  joinWaitlist: async (sessionId: string): Promise<ApiResponse<Booking>> => {
    return api.post<Booking>(`/api/v1/sessions/${sessionId}/waitlist`);
  },

  /**
   * Cancel a booking.
   */
  cancelBooking: async (bookingId: string): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/api/v1/bookings/${bookingId}`);
  },

  /**
   * Check in for a session.
   */
  checkIn: async (bookingId: string): Promise<ApiResponse<Booking>> => {
    return api.post<Booking>(`/api/v1/bookings/${bookingId}/check-in`);
  },
};