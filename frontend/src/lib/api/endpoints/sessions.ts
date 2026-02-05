/**
 * Game Sessions API endpoints.
 */

import { api } from '../client';
import { ApiResponse, Booking, GameSession, SessionCreateRequest, SessionUpdateRequest, SessionModerateRequest } from '../types';

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

export const sessionsApi = {
  /**
   * Search sessions globally or within an exhibition.
   * Returns an array of sessions with availability info.
   */
  search: async (
    params: SessionSearchParams & { exhibition_id?: string } = {}
  ): Promise<ApiResponse<GameSession[]>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return api.get<GameSession[]>(
      `/api/v1/sessions/search${query ? `?${query}` : ''}`
    );
  },

  /**
   * Search sessions within an exhibition.
   * Returns an array of sessions with availability info.
   */
  searchInExhibition: async (
    exhibitionId: string,
    params: SessionSearchParams = {}
  ): Promise<ApiResponse<GameSession[]>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return api.get<GameSession[]>(
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
    return api.post<Booking>(`/api/v1/sessions/${sessionId}/bookings`, { role: 'PLAYER' });
  },

  /**
   * Join waitlist for a session (same endpoint, backend handles waitlist automatically when full).
   */
  joinWaitlist: async (sessionId: string): Promise<ApiResponse<Booking>> => {
    return api.post<Booking>(`/api/v1/sessions/${sessionId}/bookings`, { role: 'PLAYER' });
  },

  /**
   * Cancel a booking.
   */
  cancelBooking: async (bookingId: string): Promise<ApiResponse<Booking>> => {
    return api.delete<Booking>(`/api/v1/sessions/bookings/${bookingId}`);
  },

  /**
   * Check in for a session.
   */
  checkIn: async (bookingId: string): Promise<ApiResponse<Booking>> => {
    return api.post<Booking>(`/api/v1/sessions/bookings/${bookingId}/check-in`);
  },

  /**
   * Create a new session.
   */
  create: async (session: SessionCreateRequest): Promise<ApiResponse<GameSession>> => {
    return api.post<GameSession>('/api/v1/sessions/', session);
  },

  /**
   * Update a session.
   */
  update: async (sessionId: string, session: SessionUpdateRequest): Promise<ApiResponse<GameSession>> => {
    return api.put<GameSession>(`/api/v1/sessions/${sessionId}`, session);
  },

  /**
   * Submit a session for moderation.
   */
  submit: async (sessionId: string): Promise<ApiResponse<GameSession>> => {
    return api.post<GameSession>(`/api/v1/sessions/${sessionId}/submit`);
  },

  /**
   * Get current user's booking for a session.
   */
  getMyBooking: async (sessionId: string): Promise<ApiResponse<Booking | null>> => {
    return api.get<Booking | null>(`/api/v1/sessions/${sessionId}/my-booking`);
  },

  /**
   * Assign a physical table to a session.
   */
  assignTable: async (sessionId: string, tableId: string): Promise<ApiResponse<GameSession>> => {
    return api.post<GameSession>(`/api/v1/sessions/${sessionId}/assign-table?table_id=${tableId}`);
  },

  /**
   * Moderate a session (approve, reject, or request changes).
   */
  moderate: async (sessionId: string, moderation: SessionModerateRequest): Promise<ApiResponse<GameSession>> => {
    return api.post<GameSession>(`/api/v1/sessions/${sessionId}/moderate`, moderation);
  },

  /**
   * Get all bookings for a session (for GMs/organizers).
   */
  getBookings: async (sessionId: string): Promise<ApiResponse<Booking[]>> => {
    return api.get<Booking[]>(`/api/v1/sessions/${sessionId}/bookings`);
  },

  /**
   * Cancel a session (GM/organizer only).
   */
  cancel: async (sessionId: string, reason: string): Promise<ApiResponse<GameSession>> => {
    return api.post<GameSession>(`/api/v1/sessions/${sessionId}/cancel`, { reason });
  },

  /**
   * Start a session (GM/organizer only).
   */
  start: async (sessionId: string): Promise<ApiResponse<GameSession>> => {
    return api.post<GameSession>(`/api/v1/sessions/${sessionId}/start`);
  },

  /**
   * End a session (GM/organizer only).
   */
  end: async (sessionId: string): Promise<ApiResponse<GameSession>> => {
    return api.post<GameSession>(`/api/v1/sessions/${sessionId}/end`);
  },
};