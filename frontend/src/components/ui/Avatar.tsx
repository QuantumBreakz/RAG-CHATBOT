import React from 'react';
import { User, Bot } from 'lucide-react';

interface AvatarProps {
  type: 'user' | 'ai';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({ type, size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10'
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  if (type === 'user') {
    return (
      <div className={`${sizes[size]} rounded-full bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg ${className}`}>
        <User className={`${iconSizes[size]} text-white`} />
      </div>
    );
  }

  return (
    <div className={`${sizes[size]} rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center shadow-lg ${className}`}>
      <Bot className={`${iconSizes[size]} text-white`} />
    </div>
  );
};