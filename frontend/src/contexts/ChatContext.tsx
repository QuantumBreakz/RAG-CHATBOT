import React, { createContext, useContext, useState, ReactNode } from 'react';
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
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [uploadedDocuments, setUploadedDocuments] = useState<string[]>([]);

  const createSession = () => {
    const newSession: ChatSession = {
      id: uuidv4(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date(),
      documents: [...uploadedDocuments]
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession);
  };

  const selectSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSession(session);
    }
  };

  const addMessage = (content: string, role: 'user' | 'assistant') => {
    if (!currentSession) return;

    const newMessage: Message = {
      id: uuidv4(),
      content,
      role,
      timestamp: new Date(),
      isStreaming: role === 'assistant'
    };

    const updatedSession = {
      ...currentSession,
      messages: [...currentSession.messages, newMessage],
      title: currentSession.messages.length === 0 ? content.substring(0, 50) : currentSession.title
    };

    setSessions(prev => prev.map(s => s.id === currentSession.id ? updatedSession : s));
    setCurrentSession(updatedSession);
  };

  const updateStreamingMessage = (content: string) => {
    if (!currentSession) return;

    const updatedSession = {
      ...currentSession,
      messages: currentSession.messages.map(msg => 
        msg.isStreaming ? { ...msg, content, isStreaming: false } : msg
      )
    };

    setSessions(prev => prev.map(s => s.id === currentSession.id ? updatedSession : s));
    setCurrentSession(updatedSession);
  };

  const clearHistory = () => {
    setSessions([]);
    setCurrentSession(null);
  };

  const addDocument = (document: string) => {
    setUploadedDocuments(prev => [...prev, document]);
  };

  const removeDocument = (document: string) => {
    setUploadedDocuments(prev => prev.filter(d => d !== document));
  };

  // Set current session from backend conversation object
  const setCurrentSessionFromBackend = (conv: any) => {
    const messages = (conv.messages || []).map((msg: any) => ({
      id: msg.id || uuidv4(),
      content: msg.content,
      role: msg.role,
      timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
      isStreaming: false
    }));
    const newSession: ChatSession = {
      id: conv.id,
      title: conv.title,
      messages,
      createdAt: conv.created_at ? new Date(conv.created_at) : new Date(),
      documents: conv.uploads ? conv.uploads.map((u: any) => u.filename) : []
    };
    setCurrentSession(newSession);
    setSessions(prev => [newSession, ...prev.filter(s => s.id !== newSession.id)]);
  };

  return (
    <ChatContext.Provider value={{
      sessions,
      currentSession,
      createSession,
      selectSession,
      addMessage,
      updateStreamingMessage,
      clearHistory,
      uploadedDocuments,
      addDocument,
      removeDocument,
      setCurrentSessionFromBackend
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};