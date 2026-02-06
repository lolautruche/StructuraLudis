import { render, screen } from '@testing-library/react';
import { AgendaTimeline } from '../AgendaTimeline';
import type { UserAgenda } from '@/lib/api/types';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string, params?: Record<string, string>) => {
    const translations: Record<string, string> = {
      noSessions: 'No sessions scheduled',
      noSessionsDescription: "You don't have any sessions yet.",
      findSessions: 'Find sessions',
      asGm: 'As GM',
      asPlayer: 'As Player',
      confirmed: 'Confirmed',
      viewDetails: 'View details',
      inProgress: 'In progress',
      conflicts: 'Conflicts detected',
      role_gm: 'GM',
      role_player: 'player',
      conflictMessage: `'${params?.session1}' (${params?.role1}) overlaps with '${params?.session2}' (${params?.role2})`,
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

// Mock utils
jest.mock('@/lib/utils', () => ({
  cn: (...classes: unknown[]) => classes.filter(Boolean).join(' '),
  formatDate: () => 'February 13, 2026',
  formatTime: (date: string) => {
    if (date.includes('10:00')) return '10:00';
    if (date.includes('14:00')) return '14:00';
    return '00:00';
  },
}));

const createMockAgenda = (overrides: Partial<UserAgenda> = {}): UserAgenda => ({
  user_id: 'user-1',
  exhibition_id: 'exhibition-1',
  exhibition_title: 'Festival du Jeu 2026',
  my_sessions: [],
  my_bookings: [],
  conflicts: [],
  ...overrides,
});

describe('AgendaTimeline', () => {
  const mockOnCheckIn = jest.fn();
  const mockOnCancelBooking = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows empty state when no sessions or bookings', () => {
    const agenda = createMockAgenda();

    render(
      <AgendaTimeline
        agenda={agenda}
        onCheckIn={mockOnCheckIn}
        onCancelBooking={mockOnCancelBooking}
      />
    );

    expect(screen.getByText('No sessions scheduled')).toBeInTheDocument();
    expect(screen.getByText("You don't have any sessions yet.")).toBeInTheDocument();
    expect(screen.getByText('Find sessions')).toBeInTheDocument();
  });

  it('renders GM sessions', () => {
    const agenda = createMockAgenda({
      my_sessions: [
        {
          id: 'session-1',
          title: 'My Campaign',
          exhibition_id: 'exhibition-1',
          exhibition_title: 'Festival du Jeu 2026',
          status: 'VALIDATED',
          scheduled_start: '2026-02-13T10:00:00Z',
          scheduled_end: '2026-02-13T14:00:00Z',
          zone_name: 'Zone A',
          table_label: 'Table 1',
          language: 'fr',
          max_players_count: 5,
          confirmed_players: 3,
          waitlist_count: 1,
          game_title: null,
          game_cover_image_url: null,
          game_external_provider: null,
        },
      ],
    });

    render(
      <AgendaTimeline
        agenda={agenda}
        onCheckIn={mockOnCheckIn}
        onCancelBooking={mockOnCancelBooking}
      />
    );

    expect(screen.getByText('My Campaign')).toBeInTheDocument();
    expect(screen.getByText('As GM')).toBeInTheDocument();
    expect(screen.getByText('10:00 - 14:00')).toBeInTheDocument();
  });

  it('renders player bookings', () => {
    const agenda = createMockAgenda({
      my_bookings: [
        {
          id: 'booking-1',
          game_session_id: 'session-1',
          session_title: 'Vampire Session',
          exhibition_id: 'exhibition-1',
          exhibition_title: 'Festival du Jeu 2026',
          status: 'CONFIRMED',
          role: 'PLAYER',
          scheduled_start: '2026-02-13T14:00:00Z',
          scheduled_end: '2026-02-13T18:00:00Z',
          zone_name: 'Zone B',
          table_label: 'Table 2',
          gm_name: 'John Doe',
          language: 'fr',
          max_players_count: 5,
          confirmed_players: 4,
          waitlist_count: 2,
          game_title: null,
          game_cover_image_url: null,
          game_external_provider: null,
        },
      ],
    });

    render(
      <AgendaTimeline
        agenda={agenda}
        onCheckIn={mockOnCheckIn}
        onCancelBooking={mockOnCancelBooking}
      />
    );

    expect(screen.getByText('Vampire Session')).toBeInTheDocument();
    expect(screen.getByText('As Player')).toBeInTheDocument();
    expect(screen.getByText('MJ: John Doe')).toBeInTheDocument();
  });

  it('shows conflict warning when conflicts exist', () => {
    const agenda = createMockAgenda({
      my_sessions: [
        {
          id: 'session-1',
          title: 'Session A',
          exhibition_id: 'exhibition-1',
          exhibition_title: 'Festival',
          status: 'VALIDATED',
          scheduled_start: '2026-02-13T10:00:00Z',
          scheduled_end: '2026-02-13T14:00:00Z',
          zone_name: null,
          table_label: null,
          language: 'fr',
          max_players_count: 5,
          confirmed_players: 0,
          waitlist_count: 0,
          game_title: null,
          game_cover_image_url: null,
          game_external_provider: null,
        },
      ],
      conflicts: [{ session1_title: 'Session A', session1_role: 'gm', session2_title: 'Session B', session2_role: 'player' }],
    });

    render(
      <AgendaTimeline
        agenda={agenda}
        onCheckIn={mockOnCheckIn}
        onCancelBooking={mockOnCancelBooking}
      />
    );

    expect(screen.getByText("'Session A' (GM) overlaps with 'Session B' (player)")).toBeInTheDocument();
  });

  it('groups items by date', () => {
    const agenda = createMockAgenda({
      my_sessions: [
        {
          id: 'session-1',
          title: 'Morning Session',
          exhibition_id: 'exhibition-1',
          exhibition_title: 'Festival',
          status: 'VALIDATED',
          scheduled_start: '2026-02-13T10:00:00Z',
          scheduled_end: '2026-02-13T13:00:00Z',
          zone_name: null,
          table_label: null,
          language: 'fr',
          max_players_count: 5,
          confirmed_players: 0,
          waitlist_count: 0,
          game_title: null,
          game_cover_image_url: null,
          game_external_provider: null,
        },
      ],
    });

    render(
      <AgendaTimeline
        agenda={agenda}
        onCheckIn={mockOnCheckIn}
        onCancelBooking={mockOnCancelBooking}
      />
    );

    expect(screen.getByText('February 13, 2026')).toBeInTheDocument();
  });
});
