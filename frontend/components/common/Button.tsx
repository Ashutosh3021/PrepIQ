import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  asChild?: boolean;
}

const variantStyles: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'bg-primary text-on-primary font-bold hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
  secondary: 'border border-primary text-primary bg-transparent hover:bg-primary/10 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
  ghost: 'bg-transparent text-on-surface hover:bg-surface-container-high focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
  danger: 'bg-error text-on-error font-bold hover:bg-error/90 focus-visible:ring-2 focus-visible:ring-error focus-visible:ring-offset-2',
};

const sizeStyles: Record<NonNullable<ButtonProps['size']>, string> = {
  sm: 'py-2 px-4 text-xs',
  md: 'py-3 px-6 text-xs',
  lg: 'py-4 px-10 text-sm',
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center uppercase tracking-widest transition-colors duration-fast disabled:opacity-50 disabled:cursor-not-allowed rounded-md';

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
