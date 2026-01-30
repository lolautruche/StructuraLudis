'use client';

import { forwardRef, TextareaHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, rows = 4, ...props }, ref) => {
    const textareaId = id || props.name;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-slate-300 mb-1"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          rows={rows}
          className={cn(
            'w-full px-4 py-2 bg-ludis-card border rounded-lg text-white placeholder-slate-400',
            'focus:outline-none focus:ring-2 focus:ring-ludis-primary focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'resize-y min-h-[100px]',
            error
              ? 'border-red-500 focus:ring-red-500'
              : 'border-slate-600 hover:border-slate-500',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            error ? `${textareaId}-error` : helperText ? `${textareaId}-helper` : undefined
          }
          {...props}
        />
        {error && (
          <p id={`${textareaId}-error`} className="mt-1 text-sm text-red-500">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${textareaId}-helper`} className="mt-1 text-sm text-slate-400">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export { Textarea };
