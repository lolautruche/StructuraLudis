/**
 * Authentication API endpoints.
 */

import { api, setAccessToken } from '../client';
import {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from '../types';

export const authApi = {
  /**
   * Login with email and password.
   */
  login: async (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
    const response = await api.post<LoginResponse>('/api/v1/auth/login', data);
    if (response.data?.access_token) {
      setAccessToken(response.data.access_token);
    }
    return response;
  },

  /**
   * Register a new user account.
   */
  register: async (data: RegisterRequest): Promise<ApiResponse<User>> => {
    return api.post<User>('/api/v1/auth/register', data);
  },

  /**
   * Logout (clear token).
   */
  logout: (): void => {
    setAccessToken(null);
  },

  /**
   * Get current authenticated user.
   */
  getCurrentUser: async (): Promise<ApiResponse<User>> => {
    return api.get<User>('/api/v1/users/me');
  },
};