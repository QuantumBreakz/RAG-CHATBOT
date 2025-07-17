import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  documents: string[];
}

interface ChatContextType {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  createSession: () => void;
  selectSession: (sessionId: string) => void;
  addMessage: (content: string, role: 'user' | 'assistant') => void;
  updateStreamingMessage: (content: string) => void;
  clearHistory: () => void;
  uploadedDocuments: string[];
  addDocument: (document: string) => void;
  removeDocument: (document: string) => void;
  setCurrentSessionFromBackend: (conv: any) => void;
  renameSession: (sessionId: string, newTitle: string) => void;
  createSessionFromPrevious: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const STORAGE_KEY = 'xor_rag_chat_state';

// Helper functions
const parseDate = (date: any): Date => date instanceof Date ? date : new Date(date || Date.now());

const serializeSession = (session: ChatSession): any => ({
  ...session,
  createdAt: session.createdAt.toISOString(),
  messages: session.messages.map(m => ({
    ...m,
    timestamp: m.timestamp.toISOString()
  }))
});

const deserializeSession = (session: any): ChatSession => ({
  ...session,
  createdAt: parseDate(session.createdAt),
  messages: (session.messages || []).map((m: any) => ({
    ...m,
    timestamp: parseDate(m.timestamp)
  }))
});

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [uploadedDocuments, setUploadedDocuments] = useState<string[]>([]);

  // Load state from localStorage
  const loadState = useCallback(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (!saved) return;

      const parsed = JSON.parse(saved);
      const restoredSessions = (parsed.sessions || []).map(deserializeSession);
      
      setSessions(restoredSessions);
      
      if (parsed.currentSession) {
        setCurrentSession(deserializeSession(parsed.currentSession));
      } else if (restoredSessions.length > 0) {
        setCurrentSession(restoredSessions[0]);
      }
    } catch (error) {
      console.warn('Failed to load chat state:', error);
    }
  }, []);

  // Save state to localStorage
  const saveState = useCallback(() => {
    try {
      const state = {
        sessions: sessions.map(serializeSession),
        currentSession: currentSession ? serializeSession(currentSession) : null
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        alert('Local chat history is too large to save. Please delete old conversations.');
      }
      console.error('Failed to save chat state:', error);
    }
  }, [sessions, currentSession]);

  // Update current session and sync with sessions array
  const updateCurrentSession = useCallback((updater: (session: ChatSession) => ChatSession) => {
    if (!currentSession) return;
    
    const updated = updater(currentSession);
    setCurrentSession(updated);
    setSessions(prev => prev.map(s => s.id === currentSession.id ? updated : s));
  }, [currentSession]);

  // Load on mount and storage events
  useEffect(() => {
    loadState();
    window.addEventListener('storage', loadState);
    return () => window.removeEventListener('storage', loadState);
  }, [loadState]);

  // Save on state changes
  useEffect(() => {
    saveState();
  }, [saveState]);

  const createSession = useCallback(() => {
    const newSession: ChatSession = {
      id: uuidv4(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date(),
      documents: [...uploadedDocuments]
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession);
  }, [uploadedDocuments]);

  const selectSession = useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) setCurrentSession(session);
  }, [sessions]);

  const addMessage = useCallback((content: string, role: 'user' | 'assistant') => {
    if (!currentSession) return;

    // Skip if trying to add assistant message when last message is already streaming
    if (role === 'assistant') {
      const lastMsg = currentSession.messages[currentSession.messages.length - 1];
      if (lastMsg?.role === 'assistant' && lastMsg.isStreaming) return;
    }

    const newMessage: Message = {
      id: uuidv4(),
      content,
      role,
      timestamp: new Date(),
      isStreaming: role === 'assistant'
    };

    updateCurrentSession(session => ({
      ...session,
      messages: [...session.messages, newMessage],
      title: session.messages.length === 0 && role === 'user' 
        ? content.substring(0, 50) 
        : session.title
    }));
  }, [currentSession, updateCurrentSession]);

  const updateStreamingMessage = useCallback((content: string) => {
    if (!currentSession) return;

    const messages = [...currentSession.messages];
    const lastStreamingIndex = messages.findLastIndex(
      msg => msg.role === 'assistant' && msg.isStreaming
    );
    
    if (lastStreamingIndex === -1) return;

    messages[lastStreamingIndex] = {
      ...messages[lastStreamingIndex],
      content,
      isStreaming: false
    };

    updateCurrentSession(session => ({ ...session, messages }));
  }, [currentSession, updateCurrentSession]);

  const clearHistory = useCallback(() => {
    setSessions([]);
    setCurrentSession(null);
  }, []);

  const addDocument = useCallback((document: string) => {
    setUploadedDocuments(prev => [...prev, document]);
  }, []);

  const removeDocument = useCallback((document: string) => {
    setUploadedDocuments(prev => prev.filter(d => d !== document));
  }, []);

  const setCurrentSessionFromBackend = useCallback((conv: any) => {
    const messages = (conv.messages || []).map((msg: any) => ({
      id: msg.id || uuidv4(),
      content: msg.content,
      role: msg.role,
      timestamp: parseDate(msg.timestamp),
      isStreaming: false
    }));

    const newSession: ChatSession = {
      id: conv.id,
      title: conv.title,
      messages,
      createdAt: parseDate(conv.created_at),
      documents: conv.uploads?.map((u: any) => u.filename) || []
    };

    setCurrentSession(newSession);
    setSessions(prev => [newSession, ...prev.filter(s => s.id !== newSession.id)]);
  }, []);

  const renameSession = useCallback((sessionId: string, newTitle: string) => {
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
    setCurrentSession(cs => cs?.id === sessionId ? { ...cs, title: newTitle } : cs);
  }, []);

  const createSessionFromPrevious = useCallback(() => {
    if (!currentSession) {
      createSession();
      return;
    }

    const newSession: ChatSession = {
      id: uuidv4(),
      title: currentSession.title ? `${currentSession.title} (Copy)` : 'New Conversation',
      messages: [...currentSession.messages],
      createdAt: new Date(),
      documents: [...currentSession.documents]
    };

    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession);
  }, [currentSession, createSession]);

  return (
    <ChatContext.Provider value={{
      sessions,
      currentSession,
      createSession,
      createSessionFromPrevious,
      selectSession,
      addMessage,
      updateStreamingMessage,
      clearHistory,
      uploadedDocuments,
      addDocument,
      removeDocument,
      setCurrentSessionFromBackend,
      renameSession
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};