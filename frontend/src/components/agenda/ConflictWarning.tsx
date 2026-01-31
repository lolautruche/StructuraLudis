'use client';

import { useTranslations } from 'next-intl';
import { SessionConflict } from '@/lib/api/types';

interface ConflictWarningProps {
  conflicts: SessionConflict[];
}

export function ConflictWarning({ conflicts }: ConflictWarningProps) {
  const t = useTranslations('Agenda');

  if (conflicts.length === 0) {
    return null;
  }

  const formatConflict = (conflict: SessionConflict): string => {
    const role1 = t(`role_${conflict.session1_role}`);
    const role2 = t(`role_${conflict.session2_role}`);
    return t('conflictMessage', {
      session1: conflict.session1_title,
      role1,
      session2: conflict.session2_title,
      role2,
    });
  };

  return (
    <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <svg
          className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
        <div className="flex-1">
          <h4 className="text-amber-700 dark:text-amber-400 font-medium">{t('conflicts')}</h4>
          <ul className="mt-2 space-y-1">
            {conflicts.map((conflict, index) => (
              <li key={index} className="text-sm text-amber-600 dark:text-amber-300/80">
                {formatConflict(conflict)}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
