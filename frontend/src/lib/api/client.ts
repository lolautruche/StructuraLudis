/**
 * Type-safe API client for Structura Ludis backend.
 *
 * Features:
 * - Automatic token handling
 * - Request/response interceptors
 * - Typed error handling
 */

import { ApiResponse } from './types';

// Client-side API calls use relative URLs (/api/*)
// Next.js rewrites proxy them to the backend (configured via API_URL env var)
const API_BASE_URL = '';

// Token storage (in-memory for SSR compatibility, localStorage for client)
let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (typeof window !== 'undefined' && token) {
    localStorage.setItem('access_token', token);
  } else if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
  }
}

export function getAccessToken(): string | null {
  if (accessToken) return accessToken;
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
}

/**
 * Get current locale from URL path (e.g., /fr/... -> fr)
 */
function getCurrentLocale(): string {
  if (typeof window === 'undefined') return 'en';
  const path = window.location.pathname;
  const match = path.match(/^\/([a-z]{2})(\/|$)/);
  return match ? match[1] : 'en';
}

/**
 * Base fetch wrapper with auth and error handling.
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;

  const locale = getCurrentLocale();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept-Language': locale,
    ...options.headers,
  };

  const token = getAccessToken();
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) {
      if (!response.ok) {
        return {
          data: null,
          error: {
            status: response.status,
            message: response.statusText,
            detail: await response.text(),
          },
        };
      }
      return { data: null as T, error: null };
    }

    const data = await response.json();

    if (!response.ok) {
      return {
        data: null,
        error: {
          status: response.status,
          message: data.detail || response.statusText,
          detail: data.detail,
          errors: data.errors,
        },
      };
    }

    return { data, error: null };
  } catch (error) {
    return {
      data: null,
      error: {
        status: 0,
        message: error instanceof Error ? error.message : 'Network error',
        detail: 'Failed to connect to server',
      },
    };
  }
}

/**
 * API client methods.
 */
export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    fetchApi<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestInit) =>
    fetchApi<T>(endpoint, { ...options, method: 'DELETE' }),
};