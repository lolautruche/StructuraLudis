/**
 * Notifications API endpoints.
 */

import { api } from '../client';
import { ApiResponse, NotificationListResponse } from '../types';

export interface NotificationListParams {
  limit?: number;
  offset?: number;
  unread_only?: boolean;
}

export const notificationsApi = {
  /**
   * List user notifications.
   */
  list: async (
    params: NotificationListParams = {}
  ): Promise<ApiResponse<NotificationListResponse>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return api.get<NotificationListResponse>(
      `/api/v1/notifications/${query ? `?${query}` : ''}`
    );
  },

  /**
   * Get unread count.
   */
  getUnreadCount: async (): Promise<ApiResponse<{ unread_count: number }>> => {
    return api.get<{ unread_count: number }>(
      '/api/v1/notifications/unread-count'
    );
  },

  /**
   * Mark notifications as read.
   */
  markAsRead: async (
    notificationIds: string[]
  ): Promise<ApiResponse<{ updated_count: number }>> => {
    return api.post<{ updated_count: number }>(
      '/api/v1/notifications/mark-read',
      { notification_ids: notificationIds }
    );
  },

  /**
   * Mark all notifications as read.
   */
  markAllAsRead: async (): Promise<ApiResponse<{ updated_count: number }>> => {
    return api.post<{ updated_count: number }>(
      '/api/v1/notifications/mark-all-read'
    );
  },
};