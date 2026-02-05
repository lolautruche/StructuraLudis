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
/**
 * Role types (Issue #99).
 * GlobalRole: Platform-wide roles (SUPER_ADMIN, ADMIN, USER)
 * ExhibitionRole: Event-scoped roles (ORGANIZER, PARTNER)
 */
export type GlobalRole = 'SUPER_ADMIN' | 'ADMIN' | 'USER';
export type ExhibitionRole = 'ORGANIZER' | 'PARTNER';

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  global_role: GlobalRole;
  timezone: string | null;
  locale: string;
  is_active: boolean;
  email_verified: boolean;
  birth_date: string | null;
  last_login: string | null;
  privacy_accepted_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface EmailVerificationResponse {
  success: boolean;
  message: string;
}

export interface ResendVerificationResponse {
  success: boolean;
  message: string;
  seconds_remaining: number;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
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

export interface UserProfileUpdate {
  full_name?: string | null;
  timezone?: string | null;
  locale?: string | null;
  birth_date?: string | null;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface EmailChangeRequest {
  new_email: string;
  password: string;
}

export interface EmailChangeResponse {
  message: string;
}

export interface EmailChangeConfirmResponse {
  success: boolean;
  message: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  success: boolean;
  message: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ResetPasswordResponse {
  success: boolean;
  message: string;
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
  user_name?: string | null;
  user_email?: string | null;
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
export type ExhibitionStatus = 'DRAFT' | 'PUBLISHED' | 'SUSPENDED' | 'ARCHIVED';

export interface Exhibition {
  id: string;
  organization_id: string;
  title: string;
  slug: string;
  description: string | null;
  start_date: string;
  end_date: string;
  timezone: string;
  location_name: string | null;
  city: string | null;
  country_code: string | null;
  region: string | null;
  address: string | null;
  status: ExhibitionStatus;
  settings: Record<string, unknown> | null;
  grace_period_minutes: number;
  is_registration_open: boolean;
  registration_opens_at: string | null;
  registration_closes_at: string | null;
  requires_registration: boolean;
  primary_language: string;
  secondary_languages: string[] | null;
  title_i18n: Record<string, string> | null;
  description_i18n: Record<string, string> | null;
  created_at: string;
  updated_at: string | null;
  // Permission flags (computed based on authenticated user)
  can_manage: boolean;
  user_exhibition_role: ExhibitionRole | null;
  // Registration status (Issue #77)
  is_user_registered: boolean;
  registration_count?: number;
}

export interface ExhibitionUpdate {
  title?: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  location_name?: string;
  city?: string;
  country_code?: string;
  region?: string;
  timezone?: string;
  grace_period_minutes?: number;
  status?: ExhibitionStatus;
  is_registration_open?: boolean;
  registration_opens_at?: string | null;
  registration_closes_at?: string | null;
  requires_registration?: boolean;
  primary_language?: string;
  secondary_languages?: string[];
  title_i18n?: Record<string, string>;
  description_i18n?: Record<string, string>;
}

/**
 * Exhibition registration types (Issue #77).
 */
export interface ExhibitionRegistration {
  id: string;
  user_id: string;
  exhibition_id: string;
  registered_at: string;
  cancelled_at: string | null;
}

/**
 * My exhibitions response (Issue #96 - JS.C11).
 */
export interface MyExhibitions {
  organized: Exhibition[];
  registered: Exhibition[];
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

export interface SessionConflict {
  session1_title: string;
  session1_role: 'gm' | 'player';
  session2_title: string;
  session2_role: 'gm' | 'player';
}

export interface UserAgenda {
  user_id: string;
  exhibition_id: string;
  exhibition_title: string;
  my_sessions: MySessionSummary[];
  my_bookings: MyBookingSummary[];
  conflicts: SessionConflict[];
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
 * Note: Time slots belong to zones, not exhibitions (Issue #105).
 */
export interface TimeSlot {
  id: string;
  zone_id: string;
  zone_name?: string;
  name: string;
  start_time: string;
  end_time: string;
  max_duration_minutes: number;
  buffer_time_minutes: number;
  created_at: string;
  updated_at: string | null;
}

export interface TimeSlotCreate {
  name: string;
  start_time: string;
  end_time: string;
  max_duration_minutes?: number;
  buffer_time_minutes?: number;
}

export interface TimeSlotUpdate {
  name?: string;
  start_time?: string;
  end_time?: string;
  max_duration_minutes?: number;
  buffer_time_minutes?: number;
}

/**
 * Zone types.
 */
export type ZoneType = 'RPG' | 'BOARD_GAME' | 'WARGAME' | 'TCG' | 'DEMO' | 'MIXED';

export interface Zone {
  id: string;
  exhibition_id: string;
  name: string;
  description: string | null;
  type: ZoneType;
  delegated_to_group_id: string | null;
  moderation_required: boolean;
  allow_public_proposals: boolean;
  table_prefix: string | null; // Issue #93 - Automatic table numbering prefix
  name_i18n: Record<string, string> | null;
  description_i18n: Record<string, string> | null;
  created_at: string;
  updated_at: string | null;
}

export interface ZoneCreate {
  exhibition_id: string;
  name: string;
  description?: string;
  type?: ZoneType;
  delegated_to_group_id?: string;
  allow_public_proposals?: boolean;
  table_prefix?: string; // Issue #93
}

export interface ZoneUpdate {
  name?: string;
  description?: string;
  type?: ZoneType;
  moderation_required?: boolean;
  allow_public_proposals?: boolean;
  table_prefix?: string; // Issue #93
}

/**
 * Physical table types.
 */
export type PhysicalTableStatus = 'AVAILABLE' | 'OCCUPIED' | 'RESERVED' | 'MAINTENANCE';

export interface PhysicalTable {
  id: string;
  zone_id: string;
  label: string;
  capacity: number;
  status: PhysicalTableStatus;
  created_at: string;
  updated_at: string | null;
}

export interface PhysicalTableUpdate {
  label?: string;
  capacity?: number;
  status?: PhysicalTableStatus;
}

export interface BatchTablesCreate {
  prefix?: string;
  count: number;
  starting_number?: number;
  capacity?: number;
  fill_gaps?: boolean; // Issue #93 - Fill gaps in existing numbering
}

export interface BatchTablesResponse {
  created_count: number;
  tables: PhysicalTable[];
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

export interface SessionModerateRequest {
  action: 'approve' | 'reject' | 'request_changes';
  rejection_reason?: string;
  comment?: string;
}

/**
 * Admin types (SuperAdmin portal).
 */
export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  global_role: GlobalRole;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  last_login: string | null;
}

/**
 * Exhibition role assignment (Issue #99).
 */
export interface ExhibitionRoleAssignment {
  id: string;
  user_id: string;
  user_email: string | null;
  user_full_name: string | null;
  exhibition_id: string;
  role: ExhibitionRole;
  zone_ids: string[] | null;
  is_main_organizer: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface ExhibitionRoleCreate {
  user_id: string;
  role: ExhibitionRole;
  zone_ids?: string[];
}

export interface ExhibitionRoleUpdate {
  role?: ExhibitionRole;
  zone_ids?: string[];
}

export interface UserSearchResult {
  id: string;
  email: string;
  full_name: string | null;
}

export interface PlatformStats {
  users: {
    total: number;
    by_role: Record<string, number>;
  };
  exhibitions: {
    total: number;
    by_status: Record<string, number>;
  };
}

export interface ExhibitionCreate {
  title: string;
  slug: string;
  description?: string;
  start_date: string;
  end_date: string;
  location_name?: string;
  city?: string;
  country_code?: string;
  region?: string;
  timezone: string;
  primary_language: string;
  grace_period_minutes?: number;
}

/**
 * Partner types (Issue #10).
 */
export interface PartnerZone {
  id: string;
  exhibition_id: string;
  name: string;
  description: string | null;
  type: ZoneType;
  moderation_required: boolean;
  allow_public_proposals: boolean;
  table_count: number;
  pending_sessions_count: number;
  validated_sessions_count: number;
}

export interface PartnerSession {
  id: string;
  exhibition_id: string;
  time_slot_id: string;
  game_id: string;
  physical_table_id: string;
  title: string;
  description: string | null;
  language: string;
  min_age: number | null;
  max_players_count: number;
  status: SessionStatus;
  scheduled_start: string;
  scheduled_end: string;
  created_at: string;
  game_title: string;
  zone_name: string;
  table_label: string;
  available_seats: number;
  confirmed_players_count: number;
}

export interface SeriesCreateRequest {
  exhibition_id: string;
  game_id: string;
  title: string;
  description?: string;
  language?: string;
  min_age?: number;
  max_players_count: number;
  safety_tools?: string[];
  is_accessible_disability?: boolean;
  provided_by_group_id?: string;
  time_slot_ids: string[];
  table_ids: string[];
  duration_minutes: number;
}

export interface SeriesCreateResponse {
  created_count: number;
  sessions: GameSession[];
  warnings: string[];
}

/**
 * Event request types (Issue #92).
 * Self-service event creation workflow.
 */
export type EventRequestStatus = 'PENDING' | 'CHANGES_REQUESTED' | 'APPROVED' | 'REJECTED' | 'CANCELLED';

export interface EventRequest {
  id: string;
  requester_id: string;
  status: EventRequestStatus;
  event_title: string;
  event_slug: string;
  event_description: string | null;
  event_start_date: string;
  event_end_date: string;
  event_location_name: string | null;
  event_city: string | null;
  event_country_code: string | null;
  event_region: string | null;
  event_timezone: string;
  organization_name: string;
  organization_slug: string;
  organization_contact_email: string | null;
  requester_message: string | null;
  requester_email: string | null;
  requester_name: string | null;
  admin_comment: string | null;
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  created_exhibition_id: string | null;
  created_organization_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface EventRequestCreate {
  event_title: string;
  event_description?: string;
  event_start_date: string;
  event_end_date: string;
  event_location_name?: string;
  event_city?: string;
  event_country_code?: string;
  event_region?: string;
  event_timezone?: string;
  organization_name: string;
  organization_contact_email?: string;
  requester_message?: string;
}

export interface EventRequestUpdate {
  event_title?: string;
  event_description?: string;
  event_start_date?: string;
  event_end_date?: string;
  event_location_name?: string;
  event_city?: string;
  event_country_code?: string;
  event_region?: string;
  event_timezone?: string;
  organization_name?: string;
  organization_contact_email?: string;
  requester_message?: string;
}

export interface EventRequestAdminUpdate extends EventRequestUpdate {
  event_slug?: string;
  organization_slug?: string;
}

export interface EventRequestReview {
  action: 'approve' | 'reject' | 'request_changes';
  admin_comment?: string;
}

export interface EventRequestListResponse {
  items: EventRequest[];
  total: number;
  pending_count: number;
}