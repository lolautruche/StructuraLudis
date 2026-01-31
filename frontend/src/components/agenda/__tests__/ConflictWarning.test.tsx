import { render, screen } from '@testing-library/react';
import { ConflictWarning } from '../ConflictWarning';
import { SessionConflict } from '@/lib/api/types';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string, params?: Record<string, string>) => {
    const translations: Record<string, string> = {
      conflicts: 'Conflicts detected',
      role_gm: 'GM',
      role_player: 'player',
      conflictMessage: `'${params?.session1}' (${params?.role1}) overlaps with '${params?.session2}' (${params?.role2})`,
    };
    return translations[key] || key;
  },
}));

describe('ConflictWarning', () => {
  it('renders nothing when there are no conflicts', () => {
    const { container } = render(<ConflictWarning conflicts={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders conflicts when present', () => {
    const conflicts: SessionConflict[] = [
      { session1_title: 'Session A', session1_role: 'gm', session2_title: 'Session B', session2_role: 'player' },
      { session1_title: 'Session C', session1_role: 'player', session2_title: 'Session D', session2_role: 'player' },
    ];

    render(<ConflictWarning conflicts={conflicts} />);

    expect(screen.getByText('Conflicts detected')).toBeInTheDocument();
    expect(screen.getByText("'Session A' (GM) overlaps with 'Session B' (player)")).toBeInTheDocument();
    expect(screen.getByText("'Session C' (player) overlaps with 'Session D' (player)")).toBeInTheDocument();
  });

  it('has warning styling', () => {
    const conflicts: SessionConflict[] = [
      { session1_title: 'Session A', session1_role: 'gm', session2_title: 'Session B', session2_role: 'player' },
    ];

    render(<ConflictWarning conflicts={conflicts} />);

    // The bg-amber-50 class is on the outermost div
    const heading = screen.getByText('Conflicts detected');
    const outerContainer = heading.closest('.bg-amber-50');
    expect(outerContainer).toBeInTheDocument();
  });
});
