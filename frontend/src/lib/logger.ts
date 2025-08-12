// Simple logging utility for frontend
export class Logger {
  private static instance: Logger;
  private logs: string[] = [];
  private maxLogs = 1000;

  private constructor() {
    // Load existing logs from localStorage
    try {
      const saved = localStorage.getItem('xor-rag-logs');
      if (saved) {
        this.logs = JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Failed to load logs from localStorage');
    }
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private log(level: string, message: string, data?: any) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data: data ? JSON.stringify(data) : undefined
    };
    
    this.logs.push(JSON.stringify(logEntry));
    
    // Keep only the last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }
    
    // Save to localStorage
    try {
      localStorage.setItem('xor-rag-logs', JSON.stringify(this.logs));
    } catch (e) {
      console.warn('Failed to save logs to localStorage');
    }
    
    // Also log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[${level}] ${message}`, data);
    }
  }

  info(message: string, data?: any) {
    this.log('INFO', message, data);
  }

  warn(message: string, data?: any) {
    this.log('WARN', message, data);
  }

  error(message: string, data?: any) {
    this.log('ERROR', message, data);
  }

  debug(message: string, data?: any) {
    this.log('DEBUG', message, data);
  }

  getLogs(): string[] {
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
    localStorage.removeItem('xor-rag-logs');
  }

  downloadLogs() {
    const logText = this.logs.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `xor-rag-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

export const logger = Logger.getInstance();
