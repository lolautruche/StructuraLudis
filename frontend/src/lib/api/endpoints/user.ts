/**
 * User API endpoints.
 */

import { api } from '../client';
import {
  ApiResponse,
  MySessionSummary,
  MyBookingSummary,
  UserAgenda,
  Booking,
} from '../types';

export const userApi = {
  /**
   * Get sessions I'm running (as GM).
   */
  getMySessions: async (
    exhibitionId?: string
  ): Promise<ApiResponse<MySessionSummary[]>> => {
    const query = exhibitionId ? `?exhibition_id=${exhibitionId}` : '';
    return api.get<MySessionSummary[]>(`/api/v1/users/me/sessions${query}`);
  },

  /**
   * Get my bookings (as player).
   */
  getMyBookings: async (
    exhibitionId?: string
  ): Promise<ApiResponse<MyBookingSummary[]>> => {
    const query = exhibitionId ? `?exhibition_id=${exhibitionId}` : '';
    return api.get<MyBookingSummary[]>(`/api/v1/users/me/bookings${query}`);
  },

  /**
   * Get my full agenda for an exhibition.
   */
  getMyAgenda: async (
    exhibitionId: string
  ): Promise<ApiResponse<UserAgenda>> => {
    return api.get<UserAgenda>(`/api/v1/users/me/agenda/${exhibitionId}`);
  },

  /**
   * Check in for a booking.
   */
  checkIn: async (bookingId: string): Promise<ApiResponse<Booking>> => {
    return api.post<Booking>(`/api/v1/bookings/${bookingId}/check-in`);
  },
};
