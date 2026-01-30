import { render, screen } from '@testing-library/react';
import { ConflictWarning } from '../ConflictWarning';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string) => {
    const translations: Record<string, string> = {
      conflicts: 'Conflicts detected',
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
    const conflicts = [
      "Conflict: 'Session A' (gm) overlaps with 'Session B' (player)",
      "Conflict: 'Session C' (player) overlaps with 'Session D' (player)",
    ];

    render(<ConflictWarning conflicts={conflicts} />);

    expect(screen.getByText('Conflicts detected')).toBeInTheDocument();
    expect(screen.getByText(conflicts[0])).toBeInTheDocument();
    expect(screen.getByText(conflicts[1])).toBeInTheDocument();
  });

  it('has warning styling', () => {
    render(<ConflictWarning conflicts={['Some conflict']} />);

    // The bg-amber-900/30 class is on the outermost div (3 levels up from h4)
    const heading = screen.getByText('Conflicts detected');
    const outerContainer = heading.closest('.bg-amber-900\\/30');
    expect(outerContainer).toBeInTheDocument();
  });
});
