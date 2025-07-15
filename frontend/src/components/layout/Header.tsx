import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Moon, Sun, Zap } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home' },
    { path: '/chat', label: 'Chat' },
    { path: '/settings', label: 'Settings' },
    { path: '/about', label: 'About' }
  ];

  return (
    <header className="bg-surface/80 backdrop-blur-xl border-b border-border sticky top-0 z-50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="relative">
              <div className="absolute inset-0 bg-primary rounded-xl blur-lg opacity-30 group-hover:opacity-50 transition-all duration-500 animate-pulse-slow"></div>
              <div className="relative bg-gradient-to-br from-primary to-primary-dark p-2 rounded-xl shadow-neon-green group-hover:shadow-neon-green-intense transition-all duration-300">
                <Zap className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold bg-gradient-to-r from-primary via-primary-light to-primary bg-clip-text text-transparent">
                XOR RAG
              </span>
              <span className="text-xs text-muted-foreground font-medium">
                Secure AI Intelligence
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex space-x-1">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 group ${
                  location.pathname === item.path
                    ? 'text-primary bg-primary/10 shadow-inner'
                    : 'text-foreground/70 hover:text-primary hover:bg-primary/5'
                }`}
              >
                {location.pathname === item.path && (
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-primary/10 rounded-lg border border-primary/20"></div>
                )}
                <span className="relative z-10">{item.label}</span>
                {location.pathname === item.path && (
                  <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-primary rounded-full"></div>
                )}
              </Link>
            ))}
          </nav>

          <div className="flex items-center space-x-3">
            <button
              onClick={toggleTheme}
              className="relative p-2.5 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border hover:border-primary/30 transition-all duration-300 group"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-primary/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                {theme === 'dark' ? (
                  <Sun className="h-4 w-4 text-primary group-hover:text-primary-light transition-colors duration-300" />
                ) : (
                  <Moon className="h-4 w-4 text-primary group-hover:text-primary-light transition-colors duration-300" />
                )}
              </div>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;