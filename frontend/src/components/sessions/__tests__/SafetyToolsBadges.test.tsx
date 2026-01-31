import { render, screen } from '@testing-library/react';
import { SafetyToolsBadges } from '../SafetyToolsBadges';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string) => {
    const translations: Record<string, string> = {
      xCard: 'X-Card',
      linesVeils: 'Lines & Veils',
      scriptChange: 'Script Change',
      openDoor: 'Open Door',
      starsWishes: 'Stars & Wishes',
      consentChecklist: 'Consent Checklist',
    };
    return translations[key] || key;
  },
}));

describe('SafetyToolsBadges', () => {
  it('renders nothing when tools array is empty', () => {
    const { container } = render(<SafetyToolsBadges tools={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when tools is undefined', () => {
    const { container } = render(<SafetyToolsBadges tools={undefined as unknown as string[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders known safety tools with labels', () => {
    render(<SafetyToolsBadges tools={['x-card', 'lines-veils']} />);
    expect(screen.getByText(/X-Card/)).toBeInTheDocument();
    expect(screen.getByText(/Lines & Veils/)).toBeInTheDocument();
  });

  it('renders unknown tools with camelCase key as fallback', () => {
    render(<SafetyToolsBadges tools={['custom-tool']} />);
    // Unknown tools fall back to the camelCase translation key
    expect(screen.getByText(/customTool/)).toBeInTheDocument();
  });

  it('limits displayed tools based on max prop', () => {
    render(
      <SafetyToolsBadges
        tools={['x-card', 'lines-veils', 'script-change', 'open-door']}
        max={2}
      />
    );
    expect(screen.getByText(/X-Card/)).toBeInTheDocument();
    expect(screen.getByText(/Lines & Veils/)).toBeInTheDocument();
    expect(screen.queryByText(/Script Change/)).not.toBeInTheDocument();
    expect(screen.getByText('+2')).toBeInTheDocument();
  });

  it('does not show +N badge when all tools fit', () => {
    render(<SafetyToolsBadges tools={['x-card', 'lines-veils']} max={3} />);
    expect(screen.queryByText(/\+/)).not.toBeInTheDocument();
  });
});
