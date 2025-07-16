import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
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
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
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

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [uploadedDocuments, setUploadedDocuments] = useState<string[]>([]);

  // Load chat state from localStorage on mount and on storage event
  useEffect(() => {
    const loadState = () => {
      const saved = localStorage.getItem('xor_rag_chat_state');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          // Restore timestamps as Date objects
          const restoredSessions = (parsed.sessions || []).map((s: any) => ({
            ...s,
            createdAt: s.createdAt ? new Date(s.createdAt) : new Date(),
            messages: (s.messages || []).map((m: any) => ({
              ...m,
              timestamp: m.timestamp ? new Date(m.timestamp) : new Date()
            }))
          }));
          setSessions(restoredSessions);
          if (parsed.currentSession) {
            setCurrentSession({
              ...parsed.currentSession,
              createdAt: parsed.currentSession.createdAt ? new Date(parsed.currentSession.createdAt) : new Date(),
              messages: (parsed.currentSession.messages || []).map((m: any) => ({
                ...m,
                timestamp: m.timestamp ? new Date(m.timestamp) : new Date()
              }))
            });
          } else if (restoredSessions.length > 0) {
            setCurrentSession(restoredSessions[0]);
          }
        } catch {}
      }
    };
    loadState();
    window.addEventListener('storage', loadState);
    return () => window.removeEventListener('storage', loadState);
  }, []);

  // Persist chat state to localStorage on every change, handle quota exceeded
  useEffect(() => {
    try {
      const safeSessions = sessions.map(s => ({
        ...s,
        createdAt: s.createdAt instanceof Date ? s.createdAt : new Date(s.createdAt),
        messages: (s.messages || []).map(m => ({
          ...m,
          timestamp: m.timestamp instanceof Date ? m.timestamp : new Date(m.timestamp)
        }))
      }));
      const safeCurrentSession = currentSession ? {
        ...currentSession,
        createdAt: currentSession.createdAt instanceof Date ? currentSession.createdAt : new Date(currentSession.createdAt),
        messages: (currentSession.messages || []).map(m => ({
          ...m,
          timestamp: m.timestamp instanceof Date ? m.timestamp : new Date(m.timestamp)
        }))
      } : null;
      localStorage.setItem('xor_rag_chat_state', JSON.stringify({ sessions: safeSessions, currentSession: safeCurrentSession }));
    } catch (e) {
      if (e instanceof DOMException && e.name === 'QuotaExceededError') {
        alert('Local chat history is too large to save. Please delete old conversations.');
      }
    }
  }, [sessions, currentSession]);

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

    // For assistant: only add a placeholder if the last message is not an assistant streaming message
    if (role === 'assistant') {
      const lastMsg = currentSession.messages[currentSession.messages.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
        // Don't add another placeholder
        return;
      }
    }

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
      title: currentSession.messages.length === 0 && role === 'user'
        ? content.substring(0, 50)
        : currentSession.title
    };

    setSessions(prev => prev.map(s => s.id === currentSession.id ? updatedSession : s));
    setCurrentSession(updatedSession);
  };

  const updateStreamingMessage = (content: string) => {
    if (!currentSession) return;

    // Find the last assistant message with isStreaming: true
    const idx = [...currentSession.messages].reverse().findIndex(
      msg => msg.role === 'assistant' && msg.isStreaming
    );
    if (idx === -1) return;

    const realIdx = currentSession.messages.length - 1 - idx;
    const updatedMessages = currentSession.messages.map((msg, i) =>
      i === realIdx
        ? { ...msg, content, isStreaming: false }
        : msg
    );

    const updatedSession = { ...currentSession, messages: updatedMessages };
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
    setSessions(prev => {
      // Remove any session with the same ID, then add the new one at the top
      const filtered = prev.filter(s => s.id !== newSession.id);
      return [newSession, ...filtered];
    });
  };

  // Ensure renames propagate to both sessions and currentSession
  const renameSession = (sessionId: string, newTitle: string) => {
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
    setCurrentSession(cs => cs && cs.id === sessionId ? { ...cs, title: newTitle } : cs);
  };

  // Create a new session, optionally copying from previous
  const createSessionFromPrevious = () => {
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
  };

  return (
    <ChatContext.Provider value={{
      sessions,
      setSessions,
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

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};