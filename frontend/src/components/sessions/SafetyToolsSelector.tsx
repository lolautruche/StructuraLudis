'use client';

import { useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Checkbox } from '@/components/ui';
import type { SafetyTool } from '@/lib/api/types';

interface SafetyToolsSelectorProps {
  safetyTools: SafetyTool[];
  selectedToolIds: string[];
  onToolsChange: (toolIds: string[]) => void;
  error?: string;
}

export function SafetyToolsSelector({
  safetyTools,
  selectedToolIds,
  onToolsChange,
  error,
}: SafetyToolsSelectorProps) {
  const t = useTranslations('SessionForm');
  const locale = useLocale();

  // Auto-select required tools on mount
  useEffect(() => {
    const requiredIds = safetyTools
      .filter((tool) => tool.is_required)
      .map((tool) => tool.id);

    const currentSet = new Set(selectedToolIds);
    const missingRequired = requiredIds.filter((id) => !currentSet.has(id));

    if (missingRequired.length > 0) {
      onToolsChange([...selectedToolIds, ...missingRequired]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [safetyTools]); // Only run when safety tools load, not on every selection change

  // Toggle a tool selection
  const handleToggle = (toolId: string, isRequired: boolean) => {
    // Cannot uncheck required tools
    if (isRequired && selectedToolIds.includes(toolId)) {
      return;
    }

    if (selectedToolIds.includes(toolId)) {
      onToolsChange(selectedToolIds.filter((id) => id !== toolId));
    } else {
      onToolsChange([...selectedToolIds, toolId]);
    }
  };

  // Get localized name
  const getToolName = (tool: SafetyTool) => {
    if (tool.name_i18n && tool.name_i18n[locale]) {
      return tool.name_i18n[locale];
    }
    return tool.name;
  };

  // Get localized description
  const getToolDescription = (tool: SafetyTool) => {
    if (tool.description_i18n && tool.description_i18n[locale]) {
      return tool.description_i18n[locale];
    }
    return tool.description;
  };

  if (safetyTools.length === 0) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-300">
          {t('safetyTools')}
        </label>
        <p className="text-sm text-slate-400">{t('noSafetyToolsAvailable')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-slate-300">
        {t('safetyTools')}
      </label>
      <p className="text-sm text-slate-400">{t('safetyToolsDescription')}</p>

      <div className="space-y-3">
        {safetyTools.map((tool) => {
          const isChecked = selectedToolIds.includes(tool.id);
          const description = getToolDescription(tool);

          return (
            <div
              key={tool.id}
              className="flex items-start p-3 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors"
            >
              <Checkbox
                id={`safety-tool-${tool.id}`}
                checked={isChecked}
                onChange={() => handleToggle(tool.id, tool.is_required)}
                disabled={tool.is_required && isChecked}
                label={
                  <div className="ml-1">
                    <span className="text-white font-medium">
                      {getToolName(tool)}
                      {tool.is_required && (
                        <span className="ml-2 text-xs text-ludis-primary">
                          ({t('required')})
                        </span>
                      )}
                    </span>
                    {description && (
                      <p className="text-sm text-slate-400 mt-1">
                        {description}
                      </p>
                    )}
                    {tool.url && (
                      <a
                        href={tool.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-ludis-primary hover:underline mt-1 inline-block"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {t('learnMore')}
                      </a>
                    )}
                  </div>
                }
              />
            </div>
          );
        })}
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
