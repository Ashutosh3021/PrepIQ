import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  message?: string;
}

export const LoadingSpinner = ({ 
  size = 'md', 
  className = '',
  message 
}: LoadingSpinnerProps) => {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  };

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className={`animate-spin rounded-full border-b-2 border-indigo-600 ${sizeClasses[size]}`}></div>
      {message && (
        <p className={`mt-4 text-${size === 'sm' ? 'sm' : 'lg'} text-gray-600`}>
          {message}
        </p>
      )}
    </div>
  );
};

export const FullPageLoader = ({ message = 'Loading...' }: { message?: string }) => {
  return (
    <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
      <LoadingSpinner size="lg" message={message} />
    </div>
  );
};

export const InlineLoader = ({ message = 'Loading...' }: { message?: string }) => {
  return (
    <div className="flex items-center justify-center py-8">
      <LoadingSpinner size="sm" message={message} />
    </div>
  );
};

export default LoadingSpinner;