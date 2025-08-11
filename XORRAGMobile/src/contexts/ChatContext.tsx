import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  sources?: any[];
  metadata?: any;
}

export interface Session {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

interface ChatContextType {
  sessions: Session[];
  currentSession: Session | null;
  createSession: (title?: string) => string;
  selectSession: (sessionId: string) => void;
  addMessage: (sessionId: string, message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearHistory: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  renameSession: (sessionId: string, newTitle: string) => void;
  beginStreamingMessage: (sessionId: string) => void;
  appendStreamingContent: (sessionId: string, content: string) => void;
  finalizeStreamingMessage: (sessionId: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const STORAGE_KEY = 'xor_rag_chat_sessions';

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    saveSessions();
  }, [sessions]);

  const loadSessions = async () => {
    try {
      const savedSessions = await AsyncStorage.getItem(STORAGE_KEY);
      if (savedSessions) {
        const parsedSessions = JSON.parse(savedSessions);
        setSessions(parsedSessions);
        if (parsedSessions.length > 0) {
          setCurrentSession(parsedSessions[0]);
        }
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const saveSessions = async () => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error('Error saving sessions:', error);
    }
  };

  const createSession = (title?: string): string => {
    const newSession: Session = {
      id: Date.now().toString(),
      title: title || `Conversation ${sessions.length + 1}`,
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession);
    return newSession.id;
  };

  const selectSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSession(session);
    }
  };

  const addMessage = (sessionId: string, message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
    };

    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        return {
          ...session,
          messages: [...session.messages, newMessage],
          updatedAt: new Date().toISOString(),
        };
      }
      return session;
    }));

    if (currentSession?.id === sessionId) {
      setCurrentSession(prev => prev ? {
        ...prev,
        messages: [...prev.messages, newMessage],
        updatedAt: new Date().toISOString(),
      } : null);
    }
  };

  const clearHistory = (sessionId: string) => {
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        return {
          ...session,
          messages: [],
          updatedAt: new Date().toISOString(),
        };
      }
      return session;
    }));

    if (currentSession?.id === sessionId) {
      setCurrentSession(prev => prev ? {
        ...prev,
        messages: [],
        updatedAt: new Date().toISOString(),
      } : null);
    }
  };

  const deleteSession = (sessionId: string) => {
    setSessions(prev => prev.filter(session => session.id !== sessionId));
    
    if (currentSession?.id === sessionId) {
      const remainingSessions = sessions.filter(session => session.id !== sessionId);
      setCurrentSession(remainingSessions.length > 0 ? remainingSessions[0] : null);
    }
  };

  const renameSession = (sessionId: string, newTitle: string) => {
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        return {
          ...session,
          title: newTitle,
          updatedAt: new Date().toISOString(),
        };
      }
      return session;
    }));

    if (currentSession?.id === sessionId) {
      setCurrentSession(prev => prev ? {
        ...prev,
        title: newTitle,
        updatedAt: new Date().toISOString(),
      } : null);
    }
  };

  const beginStreamingMessage = (sessionId: string) => {
    const streamingMessage: Message = {
      id: 'streaming',
      content: '',
      role: 'assistant',
      timestamp: new Date().toISOString(),
    };

    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        return {
          ...session,
          messages: [...session.messages, streamingMessage],
        };
      }
      return session;
    }));
  };

  const appendStreamingContent = (sessionId: string, content: string) => {
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        const updatedMessages = session.messages.map(message => {
          if (message.id === 'streaming') {
            return {
              ...message,
              content: message.content + content,
            };
          }
          return message;
        });
        return {
          ...session,
          messages: updatedMessages,
        };
      }
      return session;
    }));
  };

  const finalizeStreamingMessage = (sessionId: string) => {
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        const updatedMessages = session.messages.map(message => {
          if (message.id === 'streaming') {
            return {
              ...message,
              id: Date.now().toString(),
            };
          }
          return message;
        });
        return {
          ...session,
          messages: updatedMessages,
          updatedAt: new Date().toISOString(),
        };
      }
      return session;
    }));
  };

  return (
    <ChatContext.Provider value={{
      sessions,
      currentSession,
      createSession,
      selectSession,
      addMessage,
      clearHistory,
      deleteSession,
      renameSession,
      beginStreamingMessage,
      appendStreamingContent,
      finalizeStreamingMessage,
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
