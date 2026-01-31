/**
 * API response and error types.
 */

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
  errors?: Record<string, string[]>;
}

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
}

/**
 * User types (from backend schemas).
 */
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  global_role: 'SUPER_ADMIN' | 'ORGANIZER' | 'PARTNER' | 'USER';
  timezone: string | null;
  locale: string;
  is_active: boolean;
  last_login: string | null;
  privacy_accepted_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  accept_privacy_policy: boolean;
}

/**
 * Session types.
 */
export type SessionStatus =
  | 'DRAFT'
  | 'PENDING_MODERATION'
  | 'CHANGES_REQUESTED'
  | 'VALIDATED'
  | 'REJECTED'
  | 'IN_PROGRESS'
  | 'FINISHED'
  | 'CANCELLED';

export type BookingStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'WAITING_LIST'
  | 'CHECKED_IN'
  | 'ATTENDED'
  | 'NO_SHOW'
  | 'CANCELLED';

export interface GameSession {
  id: string;
  title: string;
  description: string | null;
  exhibition_id: string;
  game_id: string | null;
  game_title: string | null;
  time_slot_id: string | null;
  physical_table_id: string | null;
  zone_name: string | null;
  table_label: string | null;
  language: string;
  min_age: number;
  max_players_count: number;
  safety_tools: string[];
  is_accessible_disability: boolean;
  status: SessionStatus;
  scheduled_start: string;
  scheduled_end: string;
  created_by_user_id: string;
  gm_name: string | null;
  provided_by_group_name: string | null;
  confirmed_players_count: number;
  waitlist_count: number;
  has_available_seats: boolean;
}

export interface Booking {
  id: string;
  game_session_id: string;
  user_id: string;
  role: 'GM' | 'PLAYER' | 'ASSISTANT' | 'SPECTATOR';
  status: BookingStatus;
  checked_in_at: string | null;
  registered_at: string;
}

/**
 * Notification types.
 */
export type NotificationType =
  | 'SESSION_CANCELLED'
  | 'BOOKING_CONFIRMED'
  | 'WAITLIST_PROMOTED'
  | 'SESSION_REMINDER'
  | 'MODERATION_COMMENT'
  | 'SESSION_APPROVED'
  | 'SESSION_REJECTED'
  | 'CHANGES_REQUESTED';

export interface Notification {
  id: string;
  notification_type: NotificationType;
  channel: 'EMAIL' | 'PUSH' | 'IN_APP';
  subject: string;
  body: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  context: Record<string, unknown> | null;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

/**
 * Exhibition types.
 */
export interface Exhibition {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  start_date: string;
  end_date: string;
  timezone: string;
  location_name: string | null;
  city: string | null;
  country_code: string | null;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  is_registration_open: boolean;
  primary_language: string;
}

/**
 * Pagination.
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/**
 * Agenda types (JS.B6).
 */
export interface MySessionSummary {
  id: string;
  title: string;
  exhibition_id: string;
  exhibition_title: string;
  status: SessionStatus;
  scheduled_start: string;
  scheduled_end: string;
  zone_name: string | null;
  table_label: string | null;
  max_players_count: number;
  confirmed_players: number;
  waitlist_count: number;
}

export interface MyBookingSummary {
  id: string;
  game_session_id: string;
  session_title: string;
  exhibition_id: string;
  exhibition_title: string;
  status: BookingStatus;
  role: 'GM' | 'PLAYER' | 'ASSISTANT' | 'SPECTATOR';
  scheduled_start: string;
  scheduled_end: string;
  zone_name: string | null;
  table_label: string | null;
  gm_name: string | null;
  max_players_count: number;
  confirmed_players: number;
  waitlist_count: number;
}

export interface UserAgenda {
  user_id: string;
  exhibition_id: string;
  exhibition_title: string;
  my_sessions: MySessionSummary[];
  my_bookings: MyBookingSummary[];
  conflicts: string[];
}

/**
 * Game types.
 */
export type GameComplexity = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'EXPERT';

export interface GameCategory {
  id: string;
  name: string;
  slug: string;
  name_i18n: Record<string, string> | null;
}

export interface Game {
  id: string;
  category_id: string;
  title: string;
  publisher: string | null;
  description: string | null;
  complexity: GameComplexity;
  min_players: number;
  max_players: number;
  external_provider_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface GameCreateRequest {
  category_id: string;
  title: string;
  publisher?: string;
  description?: string;
  complexity?: GameComplexity;
  min_players: number;
  max_players: number;
}

/**
 * Time slot types.
 */
export interface TimeSlot {
  id: string;
  exhibition_id: string;
  name: string;
  start_time: string;
  end_time: string;
  max_duration_minutes: number;
  buffer_time_minutes: number;
  created_at: string;
  updated_at: string | null;
}

/**
 * Safety tool types.
 */
export interface SafetyTool {
  id: string;
  exhibition_id: string;
  name: string;
  slug: string;
  description: string | null;
  url: string | null;
  is_required: boolean;
  display_order: number;
  name_i18n: Record<string, string> | null;
  description_i18n: Record<string, string> | null;
  created_at: string;
  updated_at: string | null;
}

/**
 * Session creation types.
 */
export interface SessionCreateRequest {
  exhibition_id: string;
  time_slot_id: string;
  game_id: string;
  title: string;
  description?: string;
  language: string;
  min_age?: number;
  max_players_count: number;
  safety_tools?: string[];
  is_accessible_disability?: boolean;
  scheduled_start: string;
  scheduled_end: string;
  provided_by_group_id?: string;
}

export interface SessionUpdateRequest {
  title?: string;
  description?: string;
  language?: string;
  min_age?: number;
  max_players_count?: number;
  safety_tools?: string[];
  is_accessible_disability?: boolean;
  scheduled_start?: string;
  scheduled_end?: string;
}