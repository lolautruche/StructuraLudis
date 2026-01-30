'use client';

import { useLocale } from 'next-intl';
import { usePathname, useRouter } from '@/i18n/routing';
import { routing } from '@/i18n/routing';

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const handleChange = (newLocale: string) => {
    router.replace(pathname, { locale: newLocale });
  };

  return (
    <div className="flex items-center space-x-1 bg-ludis-card rounded-lg p-1">
      {routing.locales.map((l) => (
        <button
          key={l}
          onClick={() => handleChange(l)}
          className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
            locale === l
              ? 'bg-ludis-primary text-white'
              : 'text-slate-400 hover:text-white'
          }`}
          aria-label={`Switch to ${l === 'fr' ? 'French' : 'English'}`}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
