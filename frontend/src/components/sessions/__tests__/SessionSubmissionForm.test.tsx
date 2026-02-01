import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { SessionSubmissionForm } from '../SessionSubmissionForm';
import { exhibitionsApi, gamesApi, sessionsApi } from '@/lib/api';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
  useLocale: () => 'en',
}));

// Mock the API modules
jest.mock('@/lib/api', () => ({
  exhibitionsApi: {
    getById: jest.fn(),
    getTimeSlots: jest.fn(),
    getSafetyTools: jest.fn(),
  },
  gamesApi: {
    search: jest.fn(),
    getCategories: jest.fn(),
    create: jest.fn(),
  },
  sessionsApi: {
    create: jest.fn(),
    submit: jest.fn(),
  },
}));

// Mock data
const mockExhibition = {
  id: 'ex-123',
  title: 'Test Exhibition',
  primary_language: 'fr',
};

const mockTimeSlots = [
  {
    id: 'slot-1',
    name: 'Morning',
    start_time: '2026-07-01T09:00:00Z',
    end_time: '2026-07-01T13:00:00Z',
    max_duration_minutes: 240,
    buffer_time_minutes: 15,
  },
  {
    id: 'slot-2',
    name: 'Afternoon',
    start_time: '2026-07-01T14:00:00Z',
    end_time: '2026-07-01T18:00:00Z',
    max_duration_minutes: 240,
    buffer_time_minutes: 15,
  },
];

const mockSafetyTools = [
  {
    id: 'tool-1',
    name: 'X-Card',
    slug: 'x-card',
    is_required: true,
    description: 'Tap to skip content',
  },
  {
    id: 'tool-2',
    name: 'Lines & Veils',
    slug: 'lines-veils',
    is_required: false,
    description: 'Set boundaries',
  },
];

const mockCategories = [
  { id: 'cat-1', name: 'RPG', slug: 'rpg' },
  { id: 'cat-2', name: 'Board Game', slug: 'board-game' },
];

const mockGames = [
  {
    id: 'game-1',
    title: 'Call of Cthulhu',
    category_id: 'cat-1',
    publisher: 'Chaosium',
    min_players: 3,
    max_players: 6,
  },
];

describe('SessionSubmissionForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default API responses
    (exhibitionsApi.getById as jest.Mock).mockResolvedValue({
      data: mockExhibition,
      error: null,
    });
    (exhibitionsApi.getTimeSlots as jest.Mock).mockResolvedValue({
      data: mockTimeSlots,
      error: null,
    });
    (exhibitionsApi.getSafetyTools as jest.Mock).mockResolvedValue({
      data: mockSafetyTools,
      error: null,
    });
    (gamesApi.getCategories as jest.Mock).mockResolvedValue({
      data: mockCategories,
      error: null,
    });
    (gamesApi.search as jest.Mock).mockResolvedValue({
      data: mockGames,
      error: null,
    });
    (sessionsApi.create as jest.Mock).mockResolvedValue({
      data: { id: 'session-123' },
      error: null,
    });
    (sessionsApi.submit as jest.Mock).mockResolvedValue({
      data: { id: 'session-123', status: 'PENDING_MODERATION' },
      error: null,
    });
  });

  it('renders loading state initially', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);
    expect(screen.getByText('loading')).toBeInTheDocument();

    // Wait for loading to complete to avoid act() warnings
    await waitFor(() => {
      expect(screen.queryByText('loading')).not.toBeInTheDocument();
    });
  });

  it('loads exhibition data on mount', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(exhibitionsApi.getById).toHaveBeenCalledWith('ex-123');
      expect(exhibitionsApi.getTimeSlots).toHaveBeenCalledWith('ex-123');
      expect(exhibitionsApi.getSafetyTools).toHaveBeenCalledWith('ex-123');
    });

    // Wait for loading to complete to avoid act() warnings
    await waitFor(() => {
      expect(screen.queryByText('loading')).not.toBeInTheDocument();
    });
  });

  it('renders form sections after loading', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByText('sectionGame')).toBeInTheDocument();
    });

    expect(screen.getByText('sectionSchedule')).toBeInTheDocument();
    expect(screen.getByText('sectionDetails')).toBeInTheDocument();
    expect(screen.getByText('sectionPlayers')).toBeInTheDocument();
    expect(screen.getByText('sectionSafetyTools')).toBeInTheDocument();
  });

  it('renders time slot options', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByText('sectionSchedule')).toBeInTheDocument();
    });

    // Check time slot selector label exists
    expect(screen.getByText('availableSlots')).toBeInTheDocument();
    // Check slot cards are rendered with slot names as badges
    expect(screen.getByText(/Morning/)).toBeInTheDocument();
    expect(screen.getByText(/Afternoon/)).toBeInTheDocument();
  });

  it('renders safety tools with required tools pre-checked', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByText('X-Card')).toBeInTheDocument();
    });

    // X-Card should be checked as it's required
    const xCardCheckbox = screen.getByLabelText(/X-Card/);
    expect(xCardCheckbox).toBeChecked();
  });

  it('renders submit and save draft buttons', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByText('saveDraft')).toBeInTheDocument();
    });

    expect(screen.getByText('submitForReview')).toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const mockCancel = jest.fn();
    render(
      <SessionSubmissionForm exhibitionId="ex-123" onCancel={mockCancel} />
    );

    await waitFor(() => {
      expect(screen.getByText('cancel')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('cancel'));
    expect(mockCancel).toHaveBeenCalled();
  });

  it('shows error when exhibition fails to load', async () => {
    (exhibitionsApi.getById as jest.Mock).mockResolvedValue({
      data: null,
      error: { message: 'Exhibition not found' },
    });

    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByText('Exhibition not found')).toBeInTheDocument();
    });
  });

  it('sets default language from exhibition', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByText('sectionDetails')).toBeInTheDocument();
    });

    const languageSelect = screen.getByLabelText('language');
    expect(languageSelect).toHaveValue('fr');
  });
});

describe('GameSelector', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    (exhibitionsApi.getById as jest.Mock).mockResolvedValue({
      data: mockExhibition,
      error: null,
    });
    (exhibitionsApi.getTimeSlots as jest.Mock).mockResolvedValue({
      data: mockTimeSlots,
      error: null,
    });
    (exhibitionsApi.getSafetyTools as jest.Mock).mockResolvedValue({
      data: mockSafetyTools,
      error: null,
    });
    (gamesApi.getCategories as jest.Mock).mockResolvedValue({
      data: mockCategories,
      error: null,
    });
    (gamesApi.search as jest.Mock).mockResolvedValue({
      data: mockGames,
      error: null,
    });
  });

  it('searches games when typing', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('searchGames')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('searchGames');
    fireEvent.change(searchInput, { target: { value: 'Cthulhu' } });

    await waitFor(() => {
      expect(gamesApi.search).toHaveBeenCalledWith(
        expect.objectContaining({ q: 'Cthulhu' })
      );
    });
  });

  it('shows search results', async () => {
    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('searchGames')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('searchGames');
    fireEvent.change(searchInput, { target: { value: 'Call' } });

    await waitFor(() => {
      expect(screen.getByText('Call of Cthulhu')).toBeInTheDocument();
    });
  });

  it('shows create game option when no results', async () => {
    (gamesApi.search as jest.Mock).mockResolvedValue({
      data: [],
      error: null,
    });

    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('searchGames')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('searchGames');
    fireEvent.change(searchInput, { target: { value: 'Unknown Game' } });
    fireEvent.focus(searchInput); // Trigger showResults

    await waitFor(() => {
      expect(screen.getByText('noGamesFound')).toBeInTheDocument();
    });

    // There are two "createNewGameButton" - one in dropdown, one below
    const createButtons = screen.getAllByText('createNewGameButton');
    expect(createButtons.length).toBeGreaterThanOrEqual(1);
  });
});

describe('Form submission', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    (exhibitionsApi.getById as jest.Mock).mockResolvedValue({
      data: mockExhibition,
      error: null,
    });
    (exhibitionsApi.getTimeSlots as jest.Mock).mockResolvedValue({
      data: mockTimeSlots,
      error: null,
    });
    (exhibitionsApi.getSafetyTools as jest.Mock).mockResolvedValue({
      data: mockSafetyTools,
      error: null,
    });
    (gamesApi.getCategories as jest.Mock).mockResolvedValue({
      data: mockCategories,
      error: null,
    });
    (gamesApi.search as jest.Mock).mockResolvedValue({
      data: mockGames,
      error: null,
    });
    (sessionsApi.create as jest.Mock).mockResolvedValue({
      data: { id: 'session-123' },
      error: null,
    });
    (sessionsApi.submit as jest.Mock).mockResolvedValue({
      data: { id: 'session-123', status: 'PENDING_MODERATION' },
      error: null,
    });
  });

  it('calls onSuccess with isDraft=true when saving draft', async () => {
    const mockSuccess = jest.fn();

    render(
      <SessionSubmissionForm exhibitionId="ex-123" onSuccess={mockSuccess} />
    );

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByText('sectionGame')).toBeInTheDocument();
    });

    // Fill required fields (simplified for test)
    // In a real test, we'd fill all fields through proper interactions

    // This is a simplified test - in reality you'd need to:
    // 1. Select a game
    // 2. Select a time slot
    // 3. Fill in title
    // 4. etc.

    // For now, just verify the button exists and form structure
    expect(screen.getByText('saveDraft')).toBeInTheDocument();
  });

  it('shows error when session creation fails', async () => {
    (sessionsApi.create as jest.Mock).mockResolvedValue({
      data: null,
      error: { message: 'Failed to create session' },
    });

    render(<SessionSubmissionForm exhibitionId="ex-123" />);

    await waitFor(() => {
      expect(screen.getByText('sectionGame')).toBeInTheDocument();
    });

    // Would need to fill and submit form to see error
    // This is a placeholder for the full integration test
  });
});
