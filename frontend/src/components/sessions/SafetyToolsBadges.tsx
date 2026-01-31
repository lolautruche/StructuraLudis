'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui';

interface SafetyToolsBadgesProps {
  tools: string[];
  max?: number;
  size?: 'sm' | 'md';
}

export function SafetyToolsBadges({ tools, max = 3, size = 'sm' }: SafetyToolsBadgesProps) {
  const t = useTranslations('SafetyTools');

  if (!tools || tools.length === 0) return null;

  const displayTools = tools.slice(0, max);
  const remaining = tools.length - max;

  // Get translated label for a safety tool slug
  const getToolLabel = (slug: string): string => {
    // Normalize slug: "lines-veils" -> "linesVeils"
    const key = slug.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    // Try to get translation, fallback to slug
    try {
      return t(key);
    } catch {
      return slug;
    }
  };

  return (
    <div className="flex flex-wrap gap-1">
      {displayTools.map((tool) => (
        <Badge key={tool} variant="purple" size={size}>
          🛡️ {getToolLabel(tool)}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="default" size={size}>
          +{remaining}
        </Badge>
      )}
    </div>
  );
}
