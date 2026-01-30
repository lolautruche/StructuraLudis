import { render, screen } from '@testing-library/react';
import { AvailabilityBadge } from '../AvailabilityBadge';

describe('AvailabilityBadge', () => {
  it('shows cancelled status', () => {
    render(
      <AvailabilityBadge
        status="CANCELLED"
        availableSeats={0}
        totalSeats={5}
      />
    );
    expect(screen.getByText('cancelled')).toBeInTheDocument();
  });

  it('shows finished status', () => {
    render(
      <AvailabilityBadge
        status="FINISHED"
        availableSeats={0}
        totalSeats={5}
      />
    );
    expect(screen.getByText('finished')).toBeInTheDocument();
  });

  it('shows in progress status', () => {
    render(
      <AvailabilityBadge
        status="IN_PROGRESS"
        availableSeats={2}
        totalSeats={5}
      />
    );
    expect(screen.getByText('inProgress')).toBeInTheDocument();
  });

  it('shows available seats when session has seats', () => {
    render(
      <AvailabilityBadge
        status="VALIDATED"
        availableSeats={3}
        totalSeats={5}
      />
    );
    expect(screen.getByText('seats')).toBeInTheDocument();
  });

  it('shows waitlist position when full with waitlist', () => {
    render(
      <AvailabilityBadge
        status="VALIDATED"
        availableSeats={0}
        totalSeats={5}
        waitlistCount={3}
      />
    );
    expect(screen.getByText('waitlistPosition')).toBeInTheDocument();
  });

  it('shows zero seats when full without waitlist', () => {
    render(
      <AvailabilityBadge
        status="VALIDATED"
        availableSeats={0}
        totalSeats={5}
        waitlistCount={0}
      />
    );
    expect(screen.getByText('seats')).toBeInTheDocument();
  });
});
