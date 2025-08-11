import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
  sources?: any[];
  contextMetadata?: any;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  documents: string[];
  sources?: any[];
}

interface ChatContextType {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  setSessions: (sessions: ChatSession[]) => void;
  createSession: () => void;
  selectSession: (sessionId: string) => void;
  addMessage: (content: string, role: 'user' | 'assistant', extras?: { sources?: any[]; contextMetadata?: any }) => void;
  beginStreamingMessage: () => void;
  appendStreamingContent: (delta: string) => void;
  finalizeStreamingMessage: (content: string, extras?: { sources?: any[]; contextMetadata?: any }) => void;
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
  
  // Use ref to always get the current session value
  const currentSessionRef = useRef<ChatSession | null>(null);
  
  // Update ref whenever currentSession changes
  useEffect(() => {
    currentSessionRef.current = currentSession;
    console.log('Ref updated to match currentSession:', currentSession?.id);
  }, [currentSession]);

  // Load state from localStorage
  const loadState = useCallback(() => {
    try {
      console.log('Loading state from localStorage...');
      const saved = localStorage.getItem(STORAGE_KEY);
      console.log('Raw saved data:', saved);
      
      if (!saved) {
        console.log('No saved data found in localStorage');
        return;
      }

      const parsed = JSON.parse(saved);
      console.log('Parsed data:', parsed);
      console.log('Sessions count:', parsed.sessions?.length || 0);
      console.log('Current session exists:', !!parsed.currentSession);
      
      const restoredSessions = (parsed.sessions || []).map(deserializeSession);
      console.log('Restored sessions:', restoredSessions.map((s: ChatSession) => ({
        id: s.id,
        title: s.title,
        messageCount: s.messages.length,
        firstMessage: s.messages[0]?.content?.substring(0, 50)
      })));
      
      setSessions(restoredSessions);
      
      if (parsed.currentSession) {
        const currentSession = deserializeSession(parsed.currentSession);
        console.log('Setting current session:', {
          id: currentSession.id,
          title: currentSession.title,
          messageCount: currentSession.messages.length,
          messages: currentSession.messages.map(m => ({ role: m.role, content: m.content.substring(0, 30) }))
        });
        setCurrentSession(currentSession);
      } else if (restoredSessions.length > 0) {
        console.log('No current session in saved data, setting first session as current');
        setCurrentSession(restoredSessions[0]);
      }
    } catch (error) {
      console.error('Failed to load chat state:', error);
    }
  }, []);

  // Save state to localStorage
  const saveState = useCallback(() => {
    try {
      // Use ref to get the latest currentSession to avoid stale closures
      const currentSessionToSave = currentSessionRef.current;
      const state = {
        sessions: sessions.map(serializeSession),
        currentSession: currentSessionToSave ? serializeSession(currentSessionToSave) : null
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      console.log('Saved state to localStorage:', {
        sessionsCount: sessions.length,
        currentSessionId: currentSessionToSave?.id,
        currentSessionMessages: currentSessionToSave?.messages?.length || 0
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        alert('Local chat history is too large to save. Please delete old conversations.');
      }
      console.error('Failed to save chat state:', error);
    }
  }, [sessions]); // Remove currentSession from dependencies to avoid stale closures

  // Update current session and sync with sessions array
  const updateCurrentSession = useCallback((updater: (session: ChatSession) => ChatSession) => {
    const session = currentSessionRef.current;
    if (!session) {
      console.warn('updateCurrentSession called but no currentSession exists');
      return;
    }
    
    console.log('updateCurrentSession called for session:', session.id);
    console.log('Current messages count before update:', session.messages.length);
    const updated = updater(session);
    console.log('Session updated, new message count:', updated.messages.length);
    console.log('Last message content:', updated.messages[updated.messages.length - 1]?.content);
    
    // Update both current session and sessions array
    setCurrentSession(updated);
    setSessions(prev => {
      const newSessions = prev.map(s => s.id === session.id ? updated : s);
      console.log('Sessions array updated, total sessions:', newSessions.length);
      return newSessions;
    });
    console.log('Session state updated');
  }, []);

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
    console.log('createSession called');
    const newSession: ChatSession = {
      id: uuidv4(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date(),
      documents: [...uploadedDocuments]
    };
    console.log('Created new session:', newSession.id);
    
    // Update both the state and the ref immediately
    setSessions(prev => {
      console.log('Updating sessions array, previous count:', prev.length);
      const newSessions = [newSession, ...prev];
      console.log('New sessions count:', newSessions.length);
      return newSessions;
    });
    setCurrentSession(newSession);
    // Update the ref immediately
    currentSessionRef.current = newSession;
    console.log('Set current session to:', newSession.id);
    console.log('Updated ref to:', currentSessionRef.current?.id);
    
    // Trigger immediate save after creating session
    setTimeout(() => saveState(), 0);
  }, [uploadedDocuments, saveState]);

  const selectSession = useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) setCurrentSession(session);
  }, [sessions]);

  const addMessage = useCallback((content: string, role: 'user' | 'assistant', extras?: { sources?: any[]; contextMetadata?: any }) => {
    const session = currentSessionRef.current;
    if (!session) {
      console.warn('addMessage called but no currentSession exists, will retry in 50ms');
      // Retry after a short delay in case the session is still being created
      setTimeout(() => {
        const retrySession = currentSessionRef.current;
        if (retrySession) {
          console.log('Retrying addMessage with session:', retrySession.id);
          addMessage(content, role, extras);
        } else {
          console.error('Failed to add message - no session available after retry');
        }
      }, 50);
      return;
    }

    console.log('addMessage called with role:', role, 'content length:', content.length);
    console.log('Current session messages count:', session.messages.length);
    console.log('Current session ID:', session.id);

    // Skip if trying to add assistant message when last message is already streaming
    // BUT allow if we're explicitly creating a streaming message
    if (role === 'assistant') {
      const lastMsg = session.messages[session.messages.length - 1];
      if (lastMsg?.role === 'assistant' && lastMsg.isStreaming && content.length > 0) {
        console.log('Skipping addMessage - last message is already streaming and has content');
        return;
      }
    }

    const newMessage: Message = {
      id: uuidv4(),
      content,
      role,
      timestamp: new Date(),
      isStreaming: role === 'assistant',
      sources: extras?.sources || [],
      contextMetadata: extras?.contextMetadata || null
    };

    console.log('Creating new message:', newMessage.id, 'role:', newMessage.role, 'isStreaming:', newMessage.isStreaming);

    updateCurrentSession(session => {
      console.log('Updating session with new message, current count:', session.messages.length);
      const updated = {
        ...session,
        messages: [...session.messages, newMessage],
        title: session.messages.length === 0 && role === 'user' 
          ? content.substring(0, 50) 
          : session.title
      };
      console.log('Updated session messages count:', updated.messages.length);
      console.log('Last message in updated session:', updated.messages[updated.messages.length - 1]);
      
      // Trigger immediate save after updating
      setTimeout(() => saveState(), 0);
      
      return updated;
    });
  }, [updateCurrentSession, saveState]);

  const beginStreamingMessage = useCallback(() => {
    const session = currentSessionRef.current;
    if (!session) {
      console.warn('beginStreamingMessage called but no currentSession exists');
      return;
    }
    console.log('beginStreamingMessage called for session:', session.id);
    console.log('Current messages count before creating streaming message:', session.messages.length);
    const newMessage: Message = {
      id: uuidv4(),
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      isStreaming: true,
    };
    console.log('Creating streaming message with ID:', newMessage.id);
    updateCurrentSession(session => {
      console.log('Adding streaming message to session, current count:', session.messages.length);
      const updated = { ...session, messages: [...session.messages, newMessage] };
      console.log('Session updated with streaming message, new count:', updated.messages.length);
      return updated;
    });
  }, [updateCurrentSession]);

  const appendStreamingContent = useCallback((delta: string) => {
    const session = currentSessionRef.current;
    if (!session || !delta) return;
    const messages = [...session.messages];
    // Find the last streaming assistant message
    let idx = -1;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant' && messages[i].isStreaming) {
        idx = i;
        break;
      }
    }
    if (idx === -1) return;
    messages[idx] = { ...messages[idx], content: (messages[idx].content || '') + delta };
    updateCurrentSession(session => ({ ...session, messages }));
  }, [updateCurrentSession]);

  const finalizeStreamingMessage = useCallback((content: string, extras?: { sources?: any[]; contextMetadata?: any }) => {
    const session = currentSessionRef.current;
    if (!session) return;
    const messages = [...session.messages];
    // Find the last streaming assistant message
    let idx = -1;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant' && messages[i].isStreaming) {
        idx = i;
        break;
      }
    }
    if (idx === -1) return;
    
    // Preserve existing content if no new content is provided
    const finalContent = content || messages[idx].content || '';
    
    messages[idx] = { 
      ...messages[idx], 
      content: finalContent, 
      isStreaming: false,
      sources: extras?.sources ?? messages[idx].sources,
      contextMetadata: extras?.contextMetadata ?? messages[idx].contextMetadata,
    };
    updateCurrentSession(session => ({ ...session, messages }));
    
    // Trigger immediate save after finalizing
    setTimeout(() => saveState(), 0);
  }, [updateCurrentSession, saveState]);

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
      isStreaming: false,
      sources: msg.sources || [],
      contextMetadata: msg.contextMetadata || null
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
      setSessions,
      createSession,
      createSessionFromPrevious,
      selectSession,
      addMessage,
      beginStreamingMessage,
      appendStreamingContent,
      finalizeStreamingMessage,
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