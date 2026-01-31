'use client';

import { forwardRef, InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string | React.ReactNode;
  error?: string;
}

const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id || props.name;

    return (
      <div className="space-y-1">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              ref={ref}
              id={inputId}
              type="checkbox"
              className={cn(
                'h-4 w-4 rounded border-slate-300 dark:border-slate-600 bg-white dark:bg-ludis-card text-ludis-primary',
                'focus:ring-2 focus:ring-ludis-primary focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-ludis-dark',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                error && 'border-red-500',
                className
              )}
              aria-invalid={error ? 'true' : 'false'}
              aria-describedby={error ? `${inputId}-error` : undefined}
              {...props}
            />
          </div>
          {label && (
            <div className="ml-3">
              <label
                htmlFor={inputId}
                className="text-sm text-slate-600 dark:text-slate-300 cursor-pointer"
              >
                {label}
              </label>
            </div>
          )}
        </div>
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-red-500">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';

export { Checkbox };
