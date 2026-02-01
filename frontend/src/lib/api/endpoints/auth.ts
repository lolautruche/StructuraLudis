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
  EmailVerificationResponse,
  ResendVerificationResponse,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
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

  /**
   * Verify email with token.
   */
  verifyEmail: async (token: string): Promise<ApiResponse<EmailVerificationResponse>> => {
    return api.get<EmailVerificationResponse>(`/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`);
  },

  /**
   * Resend verification email.
   */
  resendVerification: async (): Promise<ApiResponse<ResendVerificationResponse>> => {
    return api.post<ResendVerificationResponse>('/api/v1/auth/resend-verification', {});
  },

  /**
   * Request password reset.
   */
  forgotPassword: async (data: ForgotPasswordRequest): Promise<ApiResponse<ForgotPasswordResponse>> => {
    return api.post<ForgotPasswordResponse>('/api/v1/auth/forgot-password', data);
  },

  /**
   * Reset password with token.
   */
  resetPassword: async (data: ResetPasswordRequest): Promise<ApiResponse<ResetPasswordResponse>> => {
    return api.post<ResetPasswordResponse>('/api/v1/auth/reset-password', data);
  },
};