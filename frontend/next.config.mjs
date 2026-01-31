import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable strict mode for better development experience
  reactStrictMode: true,

  // Preserve trailing slashes in URLs (required for FastAPI with redirect_slashes=False)
  skipTrailingSlashRedirect: true,

  // API proxy to backend
  // Uses server-side API_URL (not NEXT_PUBLIC_*) so the browser doesn't try to resolve Docker hostnames
  async rewrites() {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    return {
      beforeFiles: [
        // Match paths with trailing slash (e.g., /api/v1/games/)
        {
          source: '/api/:path*/',
          destination: `${apiUrl}/api/:path*/`,
        },
        // Match paths without trailing slash
        {
          source: '/api/:path*',
          destination: `${apiUrl}/api/:path*`,
        },
      ],
    };
  },
};

export default withNextIntl(nextConfig);