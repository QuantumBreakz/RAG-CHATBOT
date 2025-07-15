import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  variant?: 'default' | 'elevated' | 'glass' | 'bordered';
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  hover = false, 
  glow = false,
  variant = 'default',
  onClick
}) => {
  const baseClasses = 'rounded-2xl transition-all duration-500 relative overflow-hidden';
  
  const variantClasses = {
    default: 'bg-surface border border-border/50',
    elevated: 'bg-surface-elevated border border-border/30 shadow-lg',
    glass: 'bg-surface/60 backdrop-blur-xl border border-border/30',
    bordered: 'bg-surface border-2 border-primary/20'
  };

  const hoverClasses = hover 
    ? 'hover:border-primary/30 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 cursor-pointer' 
    : '';

  const glowClasses = glow 
    ? 'shadow-neon-green hover:shadow-neon-green-intense' 
    : '';

  return (
    <div
      className={`
        ${baseClasses} 
        ${variantClasses[variant]} 
        ${hoverClasses} 
        ${glowClasses}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      style={onClick ? { cursor: 'pointer' } : undefined}
      onKeyDown={onClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      {glow && (
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5 opacity-50"></div>
      )}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default Card;