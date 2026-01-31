import { render, screen, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../ThemeContext';

// Test component to access theme context
function TestComponent() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button onClick={() => setTheme('light')}>Set Light</button>
      <button onClick={() => setTheme('dark')}>Set Dark</button>
      <button onClick={() => setTheme('system')}>Set System</button>
    </div>
  );
}

describe('ThemeContext', () => {
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

  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', { value: localStorageMock });
    localStorageMock.clear();

    // Default to dark system preference
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(() => matchMediaMock(true)),
    });

    // Clear document classes
    document.documentElement.classList.remove('light', 'dark');
  });

  it('defaults to system theme when no preference stored', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme')).toHaveTextContent('system');
  });

  it('resolves to dark when system prefers dark', () => {
    window.matchMedia = jest.fn().mockImplementation(() => matchMediaMock(true));

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('resolved')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('resolves to light when system prefers light', () => {
    window.matchMedia = jest.fn().mockImplementation(() => matchMediaMock(false));

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('resolved')).toHaveTextContent('light');
    expect(document.documentElement.classList.contains('light')).toBe(true);
  });

  it('loads theme from localStorage', () => {
    localStorageMock.setItem('structura-ludis-theme', 'light');

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme')).toHaveTextContent('light');
    expect(screen.getByTestId('resolved')).toHaveTextContent('light');
  });

  it('persists theme to localStorage when changed', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    act(() => {
      screen.getByText('Set Dark').click();
    });

    expect(localStorageMock.getItem('structura-ludis-theme')).toBe('dark');
    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
  });

  it('applies dark class to document when dark theme selected', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    act(() => {
      screen.getByText('Set Dark').click();
    });

    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.classList.contains('light')).toBe(false);
  });

  it('applies light class to document when light theme selected', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    act(() => {
      screen.getByText('Set Light').click();
    });

    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('throws error when useTheme is used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useTheme must be used within a ThemeProvider');

    consoleSpy.mockRestore();
  });
});
