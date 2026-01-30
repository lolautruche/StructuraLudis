import { render, screen } from '@testing-library/react';
import { SafetyToolsBadges } from '../SafetyToolsBadges';

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

  it('renders unknown tools as-is', () => {
    render(<SafetyToolsBadges tools={['custom-tool']} />);
    expect(screen.getByText(/custom-tool/)).toBeInTheDocument();
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
