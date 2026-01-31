import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeToggle } from '../ThemeToggle';
import { ThemeProvider } from '@/contexts/ThemeContext';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

const matchMediaMock = (matches: boolean) => ({
  matches,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
});

describe('ThemeToggle', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', { value: localStorageMock });
    localStorageMock.clear();

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(() => matchMediaMock(true)),
    });

    document.documentElement.classList.remove('light', 'dark');
  });

  const renderWithProvider = () => {
    return render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );
  };

  it('renders toggle button', () => {
    renderWithProvider();

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('displays System label when theme is system', () => {
    renderWithProvider();

    expect(screen.getByText('System')).toBeInTheDocument();
  });

  it('cycles through themes on click: system -> light -> dark -> system', () => {
    renderWithProvider();

    const button = screen.getByRole('button');

    // Initial state: system
    expect(screen.getByText('System')).toBeInTheDocument();

    // Click 1: system -> light
    fireEvent.click(button);
    expect(screen.getByText('Light')).toBeInTheDocument();

    // Click 2: light -> dark
    fireEvent.click(button);
    expect(screen.getByText('Dark')).toBeInTheDocument();

    // Click 3: dark -> system
    fireEvent.click(button);
    expect(screen.getByText('System')).toBeInTheDocument();
  });

  it('has accessible aria-label', () => {
    renderWithProvider();

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('System'));
  });

  it('updates aria-label when theme changes', () => {
    renderWithProvider();

    const button = screen.getByRole('button');

    fireEvent.click(button); // -> light
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Light'));

    fireEvent.click(button); // -> dark
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Dark'));
  });

  it('displays correct icon for each theme', () => {
    renderWithProvider();

    const button = screen.getByRole('button');

    // System theme - should have computer/monitor icon (check SVG exists)
    expect(button.querySelector('svg')).toBeInTheDocument();

    // Light theme - sun icon
    fireEvent.click(button);
    expect(button.querySelector('svg')).toBeInTheDocument();

    // Dark theme - moon icon
    fireEvent.click(button);
    expect(button.querySelector('svg')).toBeInTheDocument();
  });

  it('persists theme preference to localStorage', () => {
    renderWithProvider();

    const button = screen.getByRole('button');

    fireEvent.click(button); // -> light
    expect(localStorageMock.getItem('structura-ludis-theme')).toBe('light');

    fireEvent.click(button); // -> dark
    expect(localStorageMock.getItem('structura-ludis-theme')).toBe('dark');
  });
});
