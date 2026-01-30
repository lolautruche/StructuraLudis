import { render, screen } from '@testing-library/react';
import { SessionCard } from '../SessionCard';
import type { GameSession } from '@/lib/api/types';

const mockSession: GameSession = {
  id: '123',
  title: 'Test Session',
  description: 'A test session',
  exhibition_id: 'ex-1',
  game_id: 'game-1',
  game_title: 'Call of Cthulhu',
  time_slot_id: 'ts-1',
  physical_table_id: 'pt-1',
  zone_name: 'Zone A',
  table_label: 'Table 1',
  language: 'fr',
  min_age: 16,
  max_players_count: 5,
  safety_tools: ['x-card', 'lines-veils'],
  is_accessible_disability: true,
  status: 'VALIDATED',
  scheduled_start: '2026-01-30T14:00:00Z',
  scheduled_end: '2026-01-30T18:00:00Z',
  created_by_user_id: 'user-1',
  gm_name: 'John Doe',
  provided_by_group_name: 'Club RPG',
  confirmed_players_count: 3,
  waitlist_count: 0,
  has_available_seats: true,
};

describe('SessionCard', () => {
  it('renders session title', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText('Test Session')).toBeInTheDocument();
  });

  it('renders game title', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText('Call of Cthulhu')).toBeInTheDocument();
  });

  it('renders GM name', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText(/John Doe/)).toBeInTheDocument();
  });

  it('renders zone and table', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText('Zone A - Table 1')).toBeInTheDocument();
  });

  it('renders language badge', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText('FR')).toBeInTheDocument();
  });

  it('renders min age badge', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText('minAge')).toBeInTheDocument();
  });

  it('renders accessibility badge when accessible', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText('♿')).toBeInTheDocument();
  });

  it('does not render accessibility badge when not accessible', () => {
    render(
      <SessionCard
        session={{ ...mockSession, is_accessible_disability: false }}
      />
    );
    expect(screen.queryByText('♿')).not.toBeInTheDocument();
  });

  it('renders safety tools', () => {
    render(<SessionCard session={mockSession} />);
    expect(screen.getByText(/X-Card/)).toBeInTheDocument();
  });

  it('renders as a link to session detail', () => {
    render(<SessionCard session={mockSession} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/sessions/123');
  });
});
