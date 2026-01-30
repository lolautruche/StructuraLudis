import '@testing-library/jest-dom';

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key) => key,
  useLocale: () => 'fr',
}));

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/sessions',
}));

// Mock @/i18n/routing
jest.mock('@/i18n/routing', () => ({
  Link: ({ children, href }) => <a href={href}>{children}</a>,
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
  usePathname: () => '/sessions',
}));
