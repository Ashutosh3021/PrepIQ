import { cn } from '@/lib/utils/cn';

type SkeletonVariant = 'text' | 'circle' | 'rect';

interface SkeletonProps {
  variant?: SkeletonVariant;
  className?: string;
  lines?: number;
}

export function Skeleton({ variant = 'rect', className, lines = 1 }: SkeletonProps) {
  const base = 'animate-pulse bg-gray-200 dark:bg-gray-700';

  if (variant === 'circle') {
    return <div className={cn(base, 'rounded-full', className)} />;
  }

  if (variant === 'text') {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              base,
              'rounded',
              i === lines - 1 ? 'w-3/4' : 'w-full',
              className
            )}
          />
        ))}
      </div>
    );
  }

  return <div className={cn(base, 'rounded', className)} />;
}
