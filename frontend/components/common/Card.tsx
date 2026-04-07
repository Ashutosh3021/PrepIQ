import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'bordered';
}

const variantStyles: Record<NonNullable<CardProps['variant']>, string> = {
  default: 'bg-surface-container border border-outline-variant/20',
  elevated: 'bg-surface-container border border-outline-variant/20 shadow-md',
  bordered: 'bg-surface-container border border-outline-variant/20 border-t-4 border-t-primary',
};

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(variantStyles[variant], 'p-4', className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export default Card;
