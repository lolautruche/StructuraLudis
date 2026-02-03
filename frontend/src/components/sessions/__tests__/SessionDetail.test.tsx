import { render, screen } from '@testing-library/react';
import { SessionDetail } from '../SessionDetail';
import type { GameSession } from '@/lib/api/types';

// Mock ToastContext
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    showSuccess: jest.fn(),
    showError: jest.fn(),
    showInfo: jest.fn(),
    showWarning: jest.fn(),
    showToast: jest.fn(),
  }),
}));

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: (namespace: string) => (key: string, values?: Record<string, unknown>) => {
    const translations: Record<string, Record<string, string>> = {
      Session: {
        schedule: 'Schedule',
        from: 'From',
        to: 'to',
        zone: 'Zone',
        table: 'Table',
        players: 'Players',
        spotsLeft: `${values?.count} spot(s) available`,
        waitlistInfo: `${values?.count} person(s) on waitlist`,
        full: 'Full',
        details: 'Details',
        accessibleSession: 'Accessible session',
        loginToBook: 'Log in to book',
        book: 'Book',
      },
      GameTable: {
        gm: 'GM',
        organizedBy: `Organized by ${values?.name}`,
        language: 'Table language',
        minAge: `${values?.age}+ years`,
        safetyTools: 'Safety tools',
      },
    };
    return translations[namespace]?.[key] || key;
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
    if (date.includes('13:00')) return '13:00';
    return '00:00';
  },
}));

const createMockSession = (overrides: Partial<GameSession> = {}): GameSession => ({
  id: 'session-1',
  title: 'Les Masques de Nyarlathotep',
  description: 'Une aventure horrifique dans les années 20',
  exhibition_id: 'exhibition-1',
  game_id: 'game-1',
  game_title: "L'Appel de Cthulhu",
  time_slot_id: 'slot-1',
  physical_table_id: 'table-1',
  zone_name: 'Espace JDR',
  table_label: 'JDR-1',
  language: 'fr',
  min_age: 16,
  max_players_count: 5,
  safety_tools: ['x-card', 'lines-veils'],
  is_accessible_disability: false,
  status: 'VALIDATED',
  scheduled_start: '2026-02-13T10:00:00Z',
  scheduled_end: '2026-02-13T13:00:00Z',
  created_by_user_id: 'user-1',
  gm_name: 'Jean-Pierre Martin',
  provided_by_group_name: 'Club JDR Lyon',
  confirmed_players_count: 3,
  waitlist_count: 0,
  has_available_seats: true,
  ...overrides,
});

describe('SessionDetail', () => {
  it('renders session title and game', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Les Masques de Nyarlathotep')).toBeInTheDocument();
    expect(screen.getByText("L'Appel de Cthulhu")).toBeInTheDocument();
  });

  it('renders session description', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Une aventure horrifique dans les années 20')).toBeInTheDocument();
  });

  it('renders schedule information', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('February 13, 2026')).toBeInTheDocument();
    expect(screen.getByText(/10:00/)).toBeInTheDocument();
    expect(screen.getByText(/13:00/)).toBeInTheDocument();
  });

  it('renders zone and table information', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Zone: Espace JDR')).toBeInTheDocument();
    expect(screen.getByText('Table: JDR-1')).toBeInTheDocument();
  });

  it('renders GM name', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Jean-Pierre Martin')).toBeInTheDocument();
  });

  it('renders organized by group', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Organized by Club JDR Lyon')).toBeInTheDocument();
  });

  it('renders available spots when not full', () => {
    const session = createMockSession({
      confirmed_players_count: 3,
      max_players_count: 5,
    });

    render(<SessionDetail session={session} />);

    expect(screen.getByText('2 spot(s) available')).toBeInTheDocument();
    expect(screen.getByText('3/5 players')).toBeInTheDocument();
  });

  it('renders full status when session is full', () => {
    const session = createMockSession({
      confirmed_players_count: 5,
      max_players_count: 5,
      has_available_seats: false,
    });

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Full')).toBeInTheDocument();
  });

  it('renders waitlist info when there is a waitlist', () => {
    const session = createMockSession({
      confirmed_players_count: 5,
      max_players_count: 5,
      waitlist_count: 3,
    });

    render(<SessionDetail session={session} />);

    expect(screen.getByText('3 person(s) on waitlist')).toBeInTheDocument();
  });

  it('renders language badge', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Table language: FR')).toBeInTheDocument();
  });

  it('renders min age badge', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('16+ years')).toBeInTheDocument();
  });

  it('renders accessibility badge when accessible', () => {
    const session = createMockSession({ is_accessible_disability: true });

    render(<SessionDetail session={session} />);

    expect(screen.getByText(/Accessible session/)).toBeInTheDocument();
  });

  it('does not render accessibility badge when not accessible', () => {
    const session = createMockSession({ is_accessible_disability: false });

    render(<SessionDetail session={session} />);

    expect(screen.queryByText(/Accessible session/)).not.toBeInTheDocument();
  });

  it('renders safety tools', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} />);

    expect(screen.getByText('Safety tools')).toBeInTheDocument();
    // Safety tools are rendered via SafetyToolsBadges component
  });

  it('shows login button when not authenticated', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} isAuthenticated={false} />);

    expect(screen.getByText('Log in to book')).toBeInTheDocument();
  });

  it('shows book button when authenticated and seats available', () => {
    const session = createMockSession();

    render(<SessionDetail session={session} isAuthenticated={true} />);

    expect(screen.getByText('Book')).toBeInTheDocument();
  });
});
