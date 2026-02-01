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
 * Map of backend error messages to user-friendly translated messages.
 * Keys are patterns to match (can be partial), values are translations by locale.
 */
const ERROR_TRANSLATIONS: Record<string, Record<string, string>> = {
  // Authentication errors
  'account deactivated': {
    en: 'Your account has been deactivated. Contact the administrator.',
    fr: 'Votre compte a été désactivé. Contactez l\'administrateur.',
  },
  // Time slot validations
  'start_time must be before end_time': {
    en: 'Start time must be before end time',
    fr: 'L\'heure de début doit être avant l\'heure de fin',
  },
  'end_time must be after start_time': {
    en: 'End time must be after start time',
    fr: 'L\'heure de fin doit être après l\'heure de début',
  },
  // Zone/table validations
  'already exists in this zone': {
    en: 'A table with this label already exists in this zone',
    fr: 'Une table avec ce label existe déjà dans cette zone',
  },
  'physical table not found': {
    en: 'Table not found',
    fr: 'Table non trouvée',
  },
  'zone not found': {
    en: 'Zone not found',
    fr: 'Zone non trouvée',
  },
  // UUID/identifier validation errors (multiple patterns for different Pydantic/FastAPI versions)
  'string does not match regex': {
    en: 'Invalid identifier format',
    fr: 'Format d\'identifiant invalide',
  },
  'the string did not match the expected pattern': {
    en: 'Invalid identifier format',
    fr: 'Format d\'identifiant invalide',
  },
  'did not match the expected pattern': {
    en: 'Invalid identifier format',
    fr: 'Format d\'identifiant invalide',
  },
  'not a valid uuid': {
    en: 'Invalid identifier format',
    fr: 'Format d\'identifiant invalide',
  },
  'input should be a valid uuid': {
    en: 'Invalid identifier format',
    fr: 'Format d\'identifiant invalide',
  },
  'invalid character': {
    en: 'Invalid identifier format',
    fr: 'Format d\'identifiant invalide',
  },
  'uuid_parsing': {
    en: 'Invalid identifier format',
    fr: 'Format d\'identifiant invalide',
  },
};

/**
 * Translate a backend error message to a user-friendly message.
 */
function translateErrorMessage(message: string, locale: string): string {
  // Check for exact or partial matches in error translations
  for (const [pattern, translations] of Object.entries(ERROR_TRANSLATIONS)) {
    if (message.toLowerCase().includes(pattern.toLowerCase())) {
      return translations[locale] || translations['en'] || message;
    }
  }
  return message;
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

    // Handle 204 No Content responses (common for DELETE operations)
    if (response.status === 204) {
      return { data: null as T, error: null };
    }

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

    // Parse JSON response (handle empty body gracefully)
    const text = await response.text();
    const data = text ? JSON.parse(text) : null;

    if (!response.ok) {
      // Handle Pydantic validation errors (detail is an array of error objects)
      let message = response.statusText;
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          // Extract messages from validation error objects (Pydantic v2 format)
          // Also check for 'type' field which contains error type like 'uuid_parsing'
          const messages = data.detail.map((err: { msg?: string; message?: string; type?: string }) => {
            // First try to translate based on error type
            if (err.type) {
              const typeTranslation = translateErrorMessage(err.type, locale);
              if (typeTranslation !== err.type) {
                return typeTranslation;
              }
            }
            // Then try message
            return err.msg || err.message || JSON.stringify(err);
          });
          message = messages.join(', ');
        } else if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (typeof data.detail === 'object' && data.detail.msg) {
          message = data.detail.msg;
        }
      }

      // Translate known error messages to user-friendly versions
      message = translateErrorMessage(message, locale);

      return {
        data: null,
        error: {
          status: response.status,
          message,
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