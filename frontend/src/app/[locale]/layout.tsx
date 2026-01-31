import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Inter } from 'next/font/google';
import { routing } from '@/i18n/routing';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { Header } from '@/components/layout';
import { EmailVerificationBanner } from '@/components/auth';
import '../globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  // Validate that the incoming locale is supported
  if (!routing.locales.includes(locale as typeof routing.locales[number])) {
    notFound();
  }

  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        {/* Prevent flash of wrong theme */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('structura-ludis-theme');
                  var resolved = theme;
                  if (!theme || theme === 'system') {
                    resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  document.documentElement.classList.add(resolved);
                } catch (e) {
                  document.documentElement.classList.add('dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${inter.variable} font-sans antialiased min-h-screen transition-colors`}
      >
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            <AuthProvider>
              <div className="flex flex-col min-h-screen">
                <Header />
                <main className="flex-1 container mx-auto px-4 py-8">
                  <EmailVerificationBanner />
                  {children}
                </main>
                <footer
                  className="border-t py-6 transition-colors"
                  style={{ borderColor: 'var(--color-border)' }}
                >
                  <div
                    className="container mx-auto px-4 text-center text-sm"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    Structura Ludis &copy; {new Date().getFullYear()}
                  </div>
                </footer>
              </div>
            </AuthProvider>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
