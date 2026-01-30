import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md';
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', children, ...props }, ref) => {
    const variants = {
      default: 'bg-slate-700 text-slate-200',
      secondary: 'bg-slate-600 text-slate-300 border-slate-500',
      success: 'bg-emerald-900/50 text-emerald-400 border-emerald-700',
      warning: 'bg-amber-900/50 text-amber-400 border-amber-700',
      danger: 'bg-red-900/50 text-red-400 border-red-700',
      info: 'bg-blue-900/50 text-blue-400 border-blue-700',
      purple: 'bg-violet-900/50 text-violet-400 border-violet-700',
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
