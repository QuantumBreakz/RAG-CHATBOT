import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  theme: {
    colors: {
      primary: string;
      background: string;
      surface: string;
      text: string;
      textSecondary: string;
      border: string;
      error: string;
      success: string;
      warning: string;
    };
  };
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const lightTheme = {
  colors: {
    primary: '#007AFF',
    background: '#FFFFFF',
    surface: '#F8F9FA',
    text: '#000000',
    textSecondary: '#6C757D',
    border: '#E9ECEF',
    error: '#DC3545',
    success: '#28A745',
    warning: '#FFC107',
  },
};

const darkTheme = {
  colors: {
    primary: '#0A84FF',
    background: '#000000',
    surface: '#1C1C1E',
    text: '#FFFFFF',
    textSecondary: '#8E8E93',
    border: '#38383A',
    error: '#FF453A',
    success: '#32D74B',
    warning: '#FFD60A',
  },
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    loadThemePreference();
  }, []);

  const loadThemePreference = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem('theme-preference');
      if (savedTheme) {
        setIsDarkMode(savedTheme === 'dark');
      }
    } catch (error) {
      console.error('Error loading theme preference:', error);
    }
  };

  const toggleTheme = async () => {
    try {
      const newTheme = !isDarkMode;
      setIsDarkMode(newTheme);
      await AsyncStorage.setItem('theme-preference', newTheme ? 'dark' : 'light');
    } catch (error) {
      console.error('Error saving theme preference:', error);
    }
  };

  const theme = isDarkMode ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme, theme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
