'use client';

interface ProviderBadgeProps {
  provider: string;
  className?: string;
}

const providerStyles: Record<string, { label: string; bg: string; text: string }> = {
  grog: {
    label: 'GROG',
    bg: 'bg-violet-100 dark:bg-violet-900/30',
    text: 'text-violet-700 dark:text-violet-300',
  },
  bgg: {
    label: 'BGG',
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    text: 'text-orange-700 dark:text-orange-300',
  },
};

export function ProviderBadge({ provider, className = '' }: ProviderBadgeProps) {
  const style = providerStyles[provider.toLowerCase()] || {
    label: provider.toUpperCase(),
    bg: 'bg-slate-100 dark:bg-slate-800',
    text: 'text-slate-700 dark:text-slate-300',
  };

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${style.bg} ${style.text} ${className}`}
    >
      {style.label}
    </span>
  );
}
