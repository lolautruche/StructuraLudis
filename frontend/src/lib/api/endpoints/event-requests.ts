/**
 * Event Request API endpoints (Issue #92).
 *
 * Self-service event creation workflow.
 */

import { api } from '../client';
import {
  ApiResponse,
  EventRequest,
  EventRequestCreate,
  EventRequestUpdate,
  EventRequestAdminUpdate,
  EventRequestReview,
  EventRequestListResponse,
  EventRequestStatus,
} from '../types';

interface ListEventRequestsParams {
  status?: EventRequestStatus;
  skip?: number;
  limit?: number;
}

export const eventRequestsApi = {
  /**
   * Submit a new event request.
   * Requires: Authenticated user with verified email
   */
  create: async (data: EventRequestCreate): Promise<ApiResponse<EventRequest>> => {
    return api.post<EventRequest>('/api/v1/event-requests/', data);
  },

  /**
   * List my event requests.
   * Returns all requests submitted by the current user.
   */
  listMy: async (): Promise<ApiResponse<EventRequest[]>> => {
    return api.get<EventRequest[]>('/api/v1/event-requests/my');
  },

  /**
   * Get an event request by ID.
   * Accessible by owner or admins.
   */
  getById: async (id: string): Promise<ApiResponse<EventRequest>> => {
    return api.get<EventRequest>(`/api/v1/event-requests/${id}`);
  },

  /**
   * Update an event request.
   * Only owner can update, and only if status is CHANGES_REQUESTED.
   */
  update: async (
    id: string,
    data: EventRequestUpdate
  ): Promise<ApiResponse<EventRequest>> => {
    return api.put<EventRequest>(`/api/v1/event-requests/${id}`, data);
  },

  /**
   * Resubmit an event request after making changes.
   * Changes status back to PENDING.
   */
  resubmit: async (id: string): Promise<ApiResponse<EventRequest>> => {
    return api.post<EventRequest>(`/api/v1/event-requests/${id}/resubmit`);
  },

  // =========================================================================
  // Admin endpoints
  // =========================================================================

  /**
   * List all event requests (admin view).
   * Requires: ADMIN or SUPER_ADMIN
   */
  list: async (
    params?: ListEventRequestsParams
  ): Promise<ApiResponse<EventRequestListResponse>> => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return api.get<EventRequestListResponse>(
      `/api/v1/event-requests/${query ? `?${query}` : ''}`
    );
  },

  /**
   * Admin update of an event request (can modify slugs).
   * Requires: ADMIN or SUPER_ADMIN
   */
  adminUpdate: async (
    id: string,
    data: EventRequestAdminUpdate
  ): Promise<ApiResponse<EventRequest>> => {
    return api.patch<EventRequest>(`/api/v1/event-requests/${id}`, data);
  },

  /**
   * Review an event request.
   * Actions: approve, reject, request_changes
   * Requires: ADMIN or SUPER_ADMIN
   */
  review: async (
    id: string,
    data: EventRequestReview
  ): Promise<ApiResponse<EventRequest>> => {
    return api.post<EventRequest>(`/api/v1/event-requests/${id}/review`, data);
  },
};
