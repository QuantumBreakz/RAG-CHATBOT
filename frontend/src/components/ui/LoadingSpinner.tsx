import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  return (
    <div className={`${sizes[size]} ${className}`}>
      <div className="relative">
        <div className="w-full h-full border-2 border-gray-200 rounded-full"></div>
        <div className="absolute top-0 left-0 w-full h-full border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    </div>
  );
};