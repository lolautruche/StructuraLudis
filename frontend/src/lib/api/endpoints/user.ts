/**
 * User API endpoints.
 */

import { api } from '../client';
import {
  ApiResponse,
  User,
  UserProfileUpdate,
  PasswordChangeRequest,
  EmailChangeRequest,
  EmailChangeResponse,
  EmailChangeConfirmResponse,
  MySessionSummary,
  MyBookingSummary,
  UserAgenda,
  Booking,
} from '../types';

export const userApi = {
  /**
   * Get current user's profile.
   */
  getProfile: async (): Promise<ApiResponse<User>> => {
    return api.get<User>('/api/v1/users/me');
  },

  /**
   * Update current user's profile.
   */
  updateProfile: async (data: UserProfileUpdate): Promise<ApiResponse<User>> => {
    return api.put<User>('/api/v1/users/me', data);
  },

  /**
   * Change current user's password.
   */
  changePassword: async (
    data: PasswordChangeRequest
  ): Promise<ApiResponse<{ message: string }>> => {
    return api.put<{ message: string }>('/api/v1/users/me/password', data);
  },

  /**
   * Request email change. Sends verification to new email.
   */
  requestEmailChange: async (
    data: EmailChangeRequest
  ): Promise<ApiResponse<EmailChangeResponse>> => {
    return api.put<EmailChangeResponse>('/api/v1/users/me/email', data);
  },

  /**
   * Verify and confirm email change.
   */
  verifyEmailChange: async (
    token: string
  ): Promise<ApiResponse<EmailChangeConfirmResponse>> => {
    return api.get<EmailChangeConfirmResponse>(
      `/api/v1/users/me/email/verify?token=${encodeURIComponent(token)}`
    );
  },

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
