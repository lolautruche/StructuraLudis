import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md';
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', children, ...props }, ref) => {
    const variants = {
      default: 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200',
      secondary: 'bg-slate-100 dark:bg-slate-600 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-500',
      success: 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-700',
      warning: 'bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-700',
      danger: 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-400 border-red-300 dark:border-red-700',
      info: 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-400 border-blue-300 dark:border-blue-700',
      purple: 'bg-violet-100 dark:bg-violet-900/50 text-violet-700 dark:text-violet-400 border-violet-300 dark:border-violet-700',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center font-medium rounded-full border',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

export { Badge };
