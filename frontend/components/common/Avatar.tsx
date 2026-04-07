import React from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils/cn';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeStyles: Record<NonNullable<AvatarProps['size']>, string> = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
};

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt, fallback, size = 'md', ...props }, ref) => {
    const { fill: _fill, ...restProps } = props as Record<string, unknown>;
    const initials = fallback
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);

    return (
      <div
        ref={ref}
        className={cn(
          'relative inline-flex items-center justify-center overflow-hidden rounded-full',
          sizeStyles[size],
          className
        )}
        role="img"
        aria-label={alt || `Avatar for ${fallback}`}
        {...restProps}
      >
        {src ? (
          <Image
            src={src}
            alt={alt || fallback}
            fill
            className="object-cover grayscale"
            sizes="(max-width: 768px) 32px, 40px"
          />
        ) : (
          <span
            className={cn(
              'flex items-center justify-center font-medium bg-surface-container-highest border border-outline-variant w-full h-full'
            )}
          >
            {initials}
          </span>
        )}
      </div>
    );
  }
);

Avatar.displayName = 'Avatar';

export default Avatar;
