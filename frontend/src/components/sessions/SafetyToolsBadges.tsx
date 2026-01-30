'use client';

import { Badge } from '@/components/ui';

interface SafetyToolsBadgesProps {
  tools: string[];
  max?: number;
  size?: 'sm' | 'md';
}

// Map of known safety tools to display names
const SAFETY_TOOL_LABELS: Record<string, string> = {
  'x-card': 'X-Card',
  'lines-veils': 'Lines & Veils',
  'script-change': 'Script Change',
  'open-door': 'Open Door',
  'stars-wishes': 'Stars & Wishes',
  'consent-checklist': 'Consent Checklist',
};

export function SafetyToolsBadges({ tools, max = 3, size = 'sm' }: SafetyToolsBadgesProps) {
  if (!tools || tools.length === 0) return null;

  const displayTools = tools.slice(0, max);
  const remaining = tools.length - max;

  return (
    <div className="flex flex-wrap gap-1">
      {displayTools.map((tool) => (
        <Badge key={tool} variant="purple" size={size}>
          🛡️ {SAFETY_TOOL_LABELS[tool.toLowerCase()] || tool}
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
