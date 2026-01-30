import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CheckInButton } from '../CheckInButton';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string, values?: Record<string, unknown>) => {
    const translations: Record<string, string> = {
      checkedIn: 'Checked in',
      checkInAvailable: 'Check-in available',
      checkInCountdown: `Check-in in ${values?.minutes} min`,
    };
    return translations[key] || key;
  },
}));

describe('CheckInButton', () => {
  const mockOnCheckIn = jest.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows checked in status when already checked in', () => {
    render(
      <CheckInButton
        bookingId="booking-1"
        status="CHECKED_IN"
        scheduledStart="2026-02-13T10:00:00Z"
        onCheckIn={mockOnCheckIn}
      />
    );

    expect(screen.getByText('Checked in')).toBeInTheDocument();
  });

  it('shows check-in button when in check-in window', () => {
    // Set current time to 15 minutes before session start
    const sessionStart = new Date('2026-02-13T10:00:00Z');
    const currentTime = new Date(sessionStart.getTime() - 10 * 60 * 1000); // 10 min before
    jest.setSystemTime(currentTime);

    render(
      <CheckInButton
        bookingId="booking-1"
        status="CONFIRMED"
        scheduledStart={sessionStart.toISOString()}
        onCheckIn={mockOnCheckIn}
        gracePeriodMinutes={15}
      />
    );

    expect(screen.getByText('Check-in available')).toBeInTheDocument();
  });

  it('shows countdown when check-in window not yet open', () => {
    // Set current time to 30 minutes before session start
    const sessionStart = new Date('2026-02-13T10:00:00Z');
    const currentTime = new Date(sessionStart.getTime() - 30 * 60 * 1000);
    jest.setSystemTime(currentTime);

    render(
      <CheckInButton
        bookingId="booking-1"
        status="CONFIRMED"
        scheduledStart={sessionStart.toISOString()}
        onCheckIn={mockOnCheckIn}
        gracePeriodMinutes={15}
      />
    );

    // Should show countdown (30 - 15 = 15 minutes until check-in window)
    expect(screen.getByText('Check-in in 15 min')).toBeInTheDocument();
  });

  it('calls onCheckIn when button is clicked', async () => {
    const sessionStart = new Date('2026-02-13T10:00:00Z');
    const currentTime = new Date(sessionStart.getTime() - 10 * 60 * 1000);
    jest.setSystemTime(currentTime);

    render(
      <CheckInButton
        bookingId="booking-1"
        status="CONFIRMED"
        scheduledStart={sessionStart.toISOString()}
        onCheckIn={mockOnCheckIn}
        gracePeriodMinutes={15}
      />
    );

    const button = screen.getByText('Check-in available');
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockOnCheckIn).toHaveBeenCalledWith('booking-1');
    });
  });

  it('renders nothing when outside check-in window and no countdown needed', () => {
    // Set current time to 2 hours before session start
    const sessionStart = new Date('2026-02-13T10:00:00Z');
    const currentTime = new Date(sessionStart.getTime() - 2 * 60 * 60 * 1000);
    jest.setSystemTime(currentTime);

    const { container } = render(
      <CheckInButton
        bookingId="booking-1"
        status="CONFIRMED"
        scheduledStart={sessionStart.toISOString()}
        onCheckIn={mockOnCheckIn}
        gracePeriodMinutes={15}
      />
    );

    expect(container.firstChild).toBeNull();
  });
});
