import { render, screen, fireEvent } from '@testing-library/react';
import { BookingButton } from '../BookingButton';
import type { GameSession, Booking } from '@/lib/api/types';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string, values?: Record<string, unknown>) => {
    const translations: Record<string, string> = {
      book: 'Book',
      joinWaitlist: 'Join waitlist',
      cancelBooking: 'Cancel booking',
      loginToBook: 'Log in to book',
      inProgress: 'In progress',
      finished: 'Finished',
      cancelled: 'Cancelled',
      full: 'Full',
      waitlistSuccess: 'You are on the waitlist',
      waitlistPosition: `Position ${values?.position} on waitlist`,
    };
    return translations[key] || key;
  },
}));

// Mock routing
jest.mock('@/i18n/routing', () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const createMockSession = (overrides: Partial<GameSession> = {}): GameSession => ({
  id: 'session-1',
  title: 'Test Session',
  description: 'A test session',
  exhibition_id: 'exhibition-1',
  game_id: 'game-1',
  game_title: 'Test Game',
  time_slot_id: 'slot-1',
  physical_table_id: 'table-1',
  zone_name: 'Zone A',
  table_label: 'Table 1',
  language: 'fr',
  min_age: 12,
  max_players_count: 5,
  safety_tools: ['x-card'],
  is_accessible_disability: false,
  status: 'VALIDATED',
  scheduled_start: '2026-02-13T10:00:00Z',
  scheduled_end: '2026-02-13T13:00:00Z',
  created_by_user_id: 'user-1',
  gm_name: 'Test GM',
  provided_by_group_name: 'Test Club',
  confirmed_players_count: 3,
  waitlist_count: 0,
  has_available_seats: true,
  ...overrides,
});

const createMockBooking = (overrides: Partial<Booking> = {}): Booking => ({
  id: 'booking-1',
  game_session_id: 'session-1',
  user_id: 'user-1',
  role: 'PLAYER',
  status: 'CONFIRMED',
  checked_in_at: null,
  registered_at: '2026-01-15T10:00:00Z',
  ...overrides,
});

describe('BookingButton', () => {
  it('shows login button when not authenticated', () => {
    const session = createMockSession();

    render(
      <BookingButton
        session={session}
        isAuthenticated={false}
      />
    );

    expect(screen.getByText('Log in to book')).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute('href', '/auth/login');
  });

  it('shows book button when authenticated and seats available', () => {
    const session = createMockSession();
    const onBook = jest.fn();

    render(
      <BookingButton
        session={session}
        isAuthenticated={true}
        onBook={onBook}
      />
    );

    const button = screen.getByText('Book');
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(onBook).toHaveBeenCalled();
  });

  it('shows join waitlist button when session is full', () => {
    const session = createMockSession({
      confirmed_players_count: 5,
      max_players_count: 5,
      has_available_seats: false,
      waitlist_count: 2,
    });
    const onJoinWaitlist = jest.fn();

    render(
      <BookingButton
        session={session}
        isAuthenticated={true}
        onJoinWaitlist={onJoinWaitlist}
      />
    );

    const button = screen.getByText('Join waitlist');
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(onJoinWaitlist).toHaveBeenCalled();
  });

  it('shows cancel button when user has confirmed booking', () => {
    const session = createMockSession();
    const booking = createMockBooking({ status: 'CONFIRMED' });
    const onCancelBooking = jest.fn();

    render(
      <BookingButton
        session={session}
        userBooking={booking}
        isAuthenticated={true}
        onCancelBooking={onCancelBooking}
      />
    );

    const button = screen.getByText('Cancel booking');
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(onCancelBooking).toHaveBeenCalled();
  });

  it('shows waitlist status when user is on waitlist', () => {
    const session = createMockSession({
      confirmed_players_count: 5,
      max_players_count: 5,
      has_available_seats: false,
      waitlist_count: 3,
    });
    const booking = createMockBooking({ status: 'WAITING_LIST' });

    render(
      <BookingButton
        session={session}
        userBooking={booking}
        isAuthenticated={true}
      />
    );

    expect(screen.getByText('You are on the waitlist')).toBeInTheDocument();
    expect(screen.getByText('Cancel booking')).toBeInTheDocument();
  });

  it('shows disabled button for finished session', () => {
    const session = createMockSession({ status: 'FINISHED' });

    render(
      <BookingButton
        session={session}
        isAuthenticated={true}
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText('Finished')).toBeInTheDocument();
  });

  it('shows disabled button for cancelled session', () => {
    const session = createMockSession({ status: 'CANCELLED' });

    render(
      <BookingButton
        session={session}
        isAuthenticated={true}
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText('Cancelled')).toBeInTheDocument();
  });

  it('shows disabled button for in progress session', () => {
    const session = createMockSession({ status: 'IN_PROGRESS' });

    render(
      <BookingButton
        session={session}
        isAuthenticated={true}
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText('In progress')).toBeInTheDocument();
  });

  it('shows loading state when isLoading is true', () => {
    const session = createMockSession();

    render(
      <BookingButton
        session={session}
        isAuthenticated={true}
        isLoading={true}
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
