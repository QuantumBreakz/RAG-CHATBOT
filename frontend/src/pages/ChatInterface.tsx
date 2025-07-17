import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Send, Upload, FileText, X, Settings, Trash2, Plus, Bot, User, Sparkles, Pencil, ArrowRight } from 'lucide-react';
import { useChat } from '../contexts/ChatContext';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { useGlobalLoading } from '../App';
import { useStreamingAssistant } from './useStreamingAssistant';
import debounce from 'lodash.debounce';

// --- Persist and Restore Chat State ---
const CHAT_STATE_KEY = 'xor_rag_chat_state';
const SESSIONS_KEY = 'xor_rag_sessions';

// Utility: Memoized message rendering for performance
const ChatInterface: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [documents, setDocuments] = useState<{filename: string, count: number, examples: any[]}[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [conversations, setConversations] = useState<{id: string, title: string, created_at: string}[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isDeletingDocument, setIsDeletingDocument] = useState<string | null>(null);
  const [isDeletingConversation, setIsDeletingConversation] = useState<string | null>(null);
  const [isResettingKB, setIsResettingKB] = useState(false);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [bannerType, setBannerType] = useState<'success' | 'error' | null>(null);
  const [vectorstoreHealthy, setVectorstoreHealthy] = useState<boolean | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState<string>("");
  // Force desktop view: sidebar always open, never collapses
  const sidebarOpen = true;
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  
  const {
    sessions,
    setSessions,
    currentSession,
    createSession,
    createSessionFromPrevious,
    selectSession,
    addMessage,
    clearHistory,
    uploadedDocuments,
    addDocument,
    removeDocument,
    setCurrentSessionFromBackend,
    updateStreamingMessage,
    renameSession
  } = useChat();

  const { loading, setLoading } = useGlobalLoading();

  // Unify operation state
  const [operationState, setOperationState] = useState({
    sending: false,
    uploading: false,
    saving: false,
    loadingDocuments: false,
    loadingConversations: false,
  });

  // Fetch documents from backend on mount (with cleanup)
  useEffect(() => {
    const controller = new AbortController();
    const fetchDocuments = async () => {
      setOperationState((s) => ({ ...s, loadingDocuments: true }));
      setLoading(true);
      try {
        const response = await fetch('/api/documents', { signal: controller.signal });
        const data = await response.json();
        setDocuments(data.documents || []);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setDocuments([]);
          setBannerMessage('Failed to fetch documents.');
          setBannerType('error');
        }
      }
      setOperationState((s) => ({ ...s, loadingDocuments: false }));
      setLoading(false);
    };
    fetchDocuments();
    return () => controller.abort();
  }, []);

  // Fetch conversations from backend on mount (with cleanup)
  useEffect(() => {
    const controller = new AbortController();
    const fetchConversations = async () => {
      setOperationState((s) => ({ ...s, loadingConversations: true }));
      setLoading(true);
      try {
        const response = await fetch('/api/history/list', { signal: controller.signal });
        const data = await response.json();
        setConversations(data.conversations || []);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setConversations([]);
          setBannerMessage('Failed to fetch conversations.');
          setBannerType('error');
        }
      }
      setOperationState((s) => ({ ...s, loadingConversations: false }));
      setLoading(false);
    };
    fetchConversations();
    return () => controller.abort();
  }, []);

  // Load a conversation from backend
  const handleLoadConversation = async (convId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/history/get/${convId}`);
      const data = await response.json();
      if (data.conversation && data.conversation.messages && data.conversation.messages.length > 0) {
        setCurrentSessionFromBackend(data.conversation);
      } else {
        setBannerMessage('Conversation is empty or could not be loaded.');
        setBannerType('error');
      }
    } catch (err) {
      setBannerMessage('Failed to load conversation.');
      setBannerType('error');
    }
    setLoading(false);
  };

  // Delete a conversation from backend
  const handleDeleteConversation = async (convId: string) => {
    if (!window.confirm('Are you sure you want to delete this conversation? This cannot be undone.')) return;
    setIsDeletingConversation(convId);
    setLoading(true);
    try {
      await fetch(`/api/history/delete/${convId}`, { method: 'DELETE' });
      setConversations((prev: {id: string, title: string, created_at: string}[]) => prev.filter((conv: {id: string}) => conv.id !== convId));
      setBannerMessage('Conversation deleted.');
      setBannerType('success');
    } catch (err) {
      setBannerMessage('Failed to delete conversation.');
      setBannerType('error');
    }
    setIsDeletingConversation(null);
    setLoading(false);
  };

  // Export a conversation as JSON
  const handleExportConversation = async (convId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/history/export/${convId}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation_${convId}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setBannerMessage('Failed to export conversation.');
      setBannerType('error');
    }
    setLoading(false);
  };

  // Helper to refresh document list from backend
  const refreshDocuments = async () => {
    setIsLoadingDocuments(true);
    setLoading(true);
    try {
      const response = await fetch('/api/documents');
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
      setDocuments([]);
      setBannerMessage('Failed to fetch documents.');
      setBannerType('error');
    }
    setIsLoadingDocuments(false);
    setLoading(false);
  };

  // Delete document from backend
  const handleDeleteDocument = async (filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? This cannot be undone.`)) return;
    setIsDeletingDocument(filename);
    setLoading(true);
    try {
      await fetch(`/api/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      setBannerMessage(`Document "${filename}" deleted.`);
      setBannerType('success');
      await refreshDocuments();
    } catch (err) {
      setBannerMessage(`Failed to delete document "${filename}".`);
      setBannerType('error');
    }
    setIsDeletingDocument(null);
    setLoading(false);
  };

  // Admin/Status actions
  const handleResetKB = async () => {
    if (!window.confirm('Are you sure you want to reset the knowledge base? This will remove all documents and cannot be undone.')) return;
    setIsResettingKB(true);
    setLoading(true);
    setStatusMessage('Resetting knowledge base...');
    try {
      const response = await fetch('/api/reset_kb', { method: 'POST' });
      if (!response.ok) throw new Error('Reset failed');
      const data = await response.json();
      setStatusMessage(data.status || 'Knowledge base reset.');
      setBannerMessage('Knowledge base reset.');
      setBannerType('success');
      await refreshDocuments();
    } catch (err) {
      setStatusMessage('Failed to reset knowledge base.');
      setBannerMessage('Failed to reset knowledge base.');
      setBannerType('error');
    }
    setIsResettingKB(false);
    setLoading(false);
  };

  const handleHealthCheck = async () => {
    setStatusMessage('Checking backend health...');
    setLoading(true);
    try {
      const response = await fetch('/api/health');
      if (!response.ok) throw new Error('Health check failed');
      const data = await response.json();
      setStatusMessage(data.status === 'ok' ? 'Backend healthy.' : 'Backend not healthy.');
    } catch (err) {
      setStatusMessage('Backend health check failed.');
      setBannerMessage('Backend health check failed.');
      setBannerType('error');
    }
    setLoading(false);
  };

  const handleTestVectorstore = async () => {
    setStatusMessage('Testing vector store...');
    setLoading(true);
    try {
      const response = await fetch('/api/test_vectorstore');
      if (!response.ok) throw new Error('Vectorstore test failed');
      const data = await response.json();
      setStatusMessage(data.message || data.status);
    } catch (err) {
      setStatusMessage('Vector store test failed.');
      setBannerMessage('Vector store test failed.');
      setBannerType('error');
    }
    setLoading(false);
  };

  // Vectorstore health check with cleanup
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();
    const checkVectorstore = async () => {
      try {
        const response = await fetch('/api/test_vectorstore', { signal: controller.signal });
        const data = await response.json();
        if (isMounted) setVectorstoreHealthy(data.status === 'ok');
      } catch (err) {
        if (isMounted) setVectorstoreHealthy(false);
      }
    };
    checkVectorstore();
    const interval = setInterval(checkVectorstore, 30000);
    return () => {
      isMounted = false;
      controller.abort();
      clearInterval(interval);
    };
  }, []);

  // --- Streaming Assistant Hook ---
  const {
    streamingContent,
    progress: streamingProgress,
    status: streamingStatus,
    error: streamingError,
    startStreaming,
    resetStreaming
  } = useStreamingAssistant();

  // Memoized scroll-to-bottom with debounce
  const scrollToBottom = React.useMemo(() => debounce(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, 100), []);

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages, streamingContent, streamingStatus, scrollToBottom]);

  // --- Streaming Assistant Message Bubble Helper ---
  // Returns a message bubble for the currently streaming assistant message
  const renderStreamingAssistantBubble = () => {
    if (streamingStatus !== 'streaming' || !streamingContent) return null;
    return (
      <div className="flex justify-start">
        <div className="flex items-start space-x-3 max-w-2xl">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-elevated border border-border flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <Card variant="elevated" className="p-4">
            <p className="text-sm leading-relaxed whitespace-pre-line">
              {streamingContent || <span className="italic text-gray-400">[Waiting for response...]</span>}
              <span className="ml-1 animate-blink">|</span>
            </p>
            <div className="text-xs mt-2 text-muted-foreground">
              Streaming...
            </div>
          </Card>
        </div>
      </div>
    );
  };

  // Responsive scroll-to-bottom logic with cleanup
  useEffect(() => {
    const handleScroll = () => {
      if (!messagesEndRef.current) return;
      const container = messagesEndRef.current.parentElement;
      if (!container) return;
      const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 40;
      setShowScrollButton(!atBottom);
    };
    const container = messagesEndRef.current?.parentElement;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [currentSession?.messages, streamingContent, streamingStatus]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || operationState.sending) return;

    const userMessage = inputValue.trim();
    setOperationState((s) => ({ ...s, sending: true }));
    setInputValue("");

    // Add user message immediately
    addMessage(userMessage, 'user');

    try {
      // Stream response
      const streamedContent = await startStreaming(userMessage, currentSession?.messages || []);
      // Add assistant response after streaming completes
      addMessage(streamedContent, 'assistant');
      // Save to backend
      if (currentSession) {
        const updatedMessages = [
          ...currentSession.messages,
          { role: 'user', content: userMessage, timestamp: new Date() },
          { role: 'assistant', content: streamedContent, timestamp: new Date() }
        ];
        await fetch('/api/history/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...currentSession,
            messages: updatedMessages
          })
        });
      }
    } catch (error) {
      setBannerMessage('Failed to send message.');
      setBannerType('error');
    } finally {
      setOperationState((s) => ({ ...s, sending: false }));
      // Don't call resetStreaming here
    }
  };

  // Add useEffect to handle pendingMessage after session creation
  useEffect(() => {
    if (pendingMessage && currentSession && currentSession.messages.length === 0) {
      // Add the pending user message and start the assistant response
      setOperationState((s) => ({ ...s, sending: true }));
      addMessage(pendingMessage, 'user');
      addMessage('', 'assistant');
      setPendingMessage(null);
      // Now trigger the LLM fetch as in handleSendMessage
      (async () => {
        // Use the streaming hook
        const streamedContent = await startStreaming(pendingMessage, []);
        updateStreamingMessage(streamedContent);
        // Persist conversation to backend before clearing streaming state
        try {
          await fetch('/api/history/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...currentSession, messages: [
              ...currentSession.messages.slice(0, -1),
              { ...currentSession.messages[currentSession.messages.length - 1], content: streamedContent }
            ] })
          });
          // Optionally refresh conversations
          setTimeout(() => refreshConversations(), 500);
        } catch (err) {
          setBannerMessage('Failed to sync conversation with backend.');
          setBannerType('error');
        }
        setOperationState((s) => ({ ...s, sending: false }));
        resetStreaming();
      })();
    }
  }, [pendingMessage, currentSession, startStreaming, updateStreamingMessage]);

  // --- File Upload Handler: Pass chunk size to backend ---
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    setOperationState((s) => ({ ...s, uploading: true }));
    setLoading(true);
    setUploadProgress(0);

    // Get chunk size from settings in localStorage
    let chunkSize = 1000;
    try {
      const settings = JSON.parse(localStorage.getItem('xor-rag-settings') || '{}');
      if (settings.chunkSize) chunkSize = settings.chunkSize;
    } catch {}

    for (const [idx, file] of Array.from(files).entries()) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('chunk_size', chunkSize.toString()); // Pass chunk size

      try {
        setUploadProgress(Math.round(((idx + 1) / files.length) * 100));
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        const data = await response.json();

        if (data.status?.includes('uploaded and embedded')) {
          setBannerMessage(`Embeddings created for "${file.name}" (${data.num_chunks} chunks).`);
          setBannerType('success');
        } else if (data.status?.includes('already exist')) {
          setBannerMessage(`Embeddings already exist for "${file.name}".`);
          setBannerType('success');
        } else {
          setBannerMessage(`Embedding failed for "${file.name}": ${data.status}`);
          setBannerType('error');
        }
        addDocument(file.name);
      } catch (err) {
        setBannerMessage(`Failed to upload document "${file.name}".`);
        setBannerType('error');
      }
    }
    setOperationState((s) => ({ ...s, uploading: false }));
    setLoading(false);
    setUploadProgress(null);
    setTimeout(() => setBannerMessage(null), 2000);
    await refreshDocuments();
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Add this function to handle title save
  const handleSaveTitle = async () => {
    if (!currentSession) return;
    const updatedTitle = editedTitle.trim() || 'Untitled Conversation';
    // Update in frontend state using renameSession
    renameSession(currentSession.id, updatedTitle);
    setIsEditingTitle(false);
    // Persist to backend
    try {
      await fetch('/api/history/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...currentSession, title: updatedTitle })
      });
      setBannerMessage('Conversation renamed.');
      setBannerType('success');
      // Fetch updated conversation from backend and update state
      const resp = await fetch(`/api/history/get/${currentSession.id}`);
      const data = await resp.json();
      setCurrentSessionFromBackend(data.conversation);
      // Refresh conversations list and update sidebar
      setConversations((prev) => prev.map(conv => conv.id === currentSession.id ? { ...conv, title: updatedTitle } : conv));
      await refreshConversations();
    } catch (err) {
      setBannerMessage('Failed to rename conversation.');
      setBannerType('error');
    }
  };

  // Helper to refresh conversation list from backend
  const refreshConversations = async () => {
    setIsLoadingConversations(true);
    setLoading(true);
    try {
      const response = await fetch('/api/history/list');
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (err) {
      setConversations([]);
      setBannerMessage('Failed to fetch conversations.');
      setBannerType('error');
    }
    setIsLoadingConversations(false);
    setLoading(false);
  };

  // Restore full chat history (sessions, currentSession, conversations) from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(CHAT_STATE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Only restore if sessions are empty
        if (parsed.sessions && Array.isArray(parsed.sessions) && sessions.length === 0) {
          setSessions(parsed.sessions);
        }
        // Only restore if currentSession is null
        if (parsed.currentSession && !currentSession) {
          setCurrentSessionFromBackend(parsed.currentSession);
        }
        if (parsed.conversations && Array.isArray(parsed.conversations) && conversations.length === 0) {
          setConversations(parsed.conversations);
        }
      } catch {}
    }
    // eslint-disable-next-line
  }, []);

  // Persist full chat history to localStorage on every update
  useEffect(() => {
    // Ensure all timestamps are Date objects before saving
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
    localStorage.setItem(
      CHAT_STATE_KEY,
      JSON.stringify({ sessions: safeSessions, currentSession: safeCurrentSession, conversations })
    );
  }, [sessions, currentSession, conversations]);

  // Memoize message rendering for performance
  const memoizedMessages = useMemo(() =>
    currentSession && currentSession.messages.length > 0
      ? currentSession.messages.map((message, idx) => (
          <div
            key={message.id || idx}
            className={`flex w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex items-start space-x-3 max-w-2xl w-full ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`} style={{ margin: '0 auto' }}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                message.role === 'user' 
                  ? 'bg-gradient-to-r from-primary to-primary-dark' 
                  : 'bg-surface-elevated border border-border'
              }`}>
                {message.role === 'user' ? (
                  <User className="h-4 w-4 text-white" />
                ) : (
                  <Bot className="h-4 w-4 text-primary" />
                )}
              </div>
              <Card
                variant={message.role === 'user' ? 'default' : 'elevated'}
                className={`p-4 rounded-lg shadow-sm w-full ${
                  message.role === 'user'
                    ? 'bg-primary text-white border-primary/30'
                    : 'bg-surface-elevated'
                }`}
              >
                <p className="text-sm leading-relaxed">
                  {message.content && message.content.trim() !== '' ? message.content : null}
                </p>
                <div className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'
                }`}>
                  {formatTimestamp(message.timestamp)}
                </div>
              </Card>
            </div>
          </div>
        ))
      : null,
    [currentSession?.messages]
  );

  return (
    <div className="flex h-screen w-screen bg-background">
      {/* Overlay while streaming */}
      {/* Embedding Status Toast/Banner */}
      {/* Sidebar - always visible in desktop view */}
      <div className="bg-surface border-r border-border flex flex-col transition-all duration-300 w-80 flex-none h-screen z-40 fixed left-0 top-0">
        {/* Sidebar close button removed for forced desktop view */}
        {/* Banner for error/success */}
        {bannerMessage && (
          <div className={`p-2 text-xs text-center rounded-b ${bannerType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} shadow`}>{bannerMessage}</div>
        )}
        {/* New Chat Button */}
        <div className="p-4 border-b border-border flex flex-col gap-2">
          <Button 
            onClick={createSession}
            className="w-full group rounded-lg shadow-sm"
            variant="outline"
          >
            <Plus className="mr-2 h-4 w-4 group-hover:rotate-90 transition-transform duration-300" />
            New Conversation
          </Button>
          <Button
            onClick={createSessionFromPrevious}
            className="w-full group rounded-lg shadow-sm"
            variant="outline"
          >
            <Sparkles className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform duration-300" />
            Duplicate Conversation
          </Button>
        </div>
        {/* Chat Sessions (History) */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4 flex items-center">
            <Sparkles className="mr-2 h-4 w-4" />
            Recent Conversations
          </h3>
          {sessions.length > 0 ? (
            sessions.map((conv) => (
              <Card
                key={conv.id}
                hover
                className={`p-4 cursor-pointer transition-all duration-300 rounded-lg shadow-sm ${currentSession?.id === conv.id ? 'border-2 border-primary' : ''}`}
                onClick={() => selectSession(conv.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-foreground truncate mb-1">
                      {conv.title}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {conv.createdAt ? new Date(conv.createdAt).toLocaleString() : ''}
                    </div>
                  </div>
                  {/* Optionally add export/delete buttons here */}
                </div>
              </Card>
            ))
          ) : (
            <div className="text-xs text-muted-foreground">No conversations found.</div>
          )}
        </div>
        {/* Document Context */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-muted-foreground flex items-center">
              <FileText className="mr-2 h-4 w-4" />
              Knowledge Base
            </h3>
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="ghost"
              size="sm"
              className="p-2"
            >
              <Upload className="h-4 w-4" />
            </Button>
          </div>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {operationState.loadingDocuments ? (
              <div className="text-xs text-muted-foreground">Loading documents...</div>
            ) : documents.length > 0 ? (
              documents.map((doc: {filename: string, count: number, examples: any[]}, index: number) => (
                <Card key={index} className="p-3 group flex items-center justify-between rounded-lg shadow-sm">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="text-xs text-foreground truncate">{doc.filename}</span>
                  </div>
                  <Button
                    onClick={() => handleDeleteDocument(doc.filename)}
                    variant="ghost"
                    size="sm"
                    className="p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    disabled={isDeletingDocument === doc.filename}
                  >
                    <X className="h-3 w-3 text-muted-foreground hover:text-red-500" />
                  </Button>
              </Card>
              ))
            ) : (
            <Card className="p-6 text-center rounded-lg shadow-sm">
              <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">No documents uploaded</p>
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="ghost"
                size="sm"
                className="mt-2 text-xs"
              >
                Upload files
              </Button>
            </Card>
          )}
          </div>
        </div>
        {/* Settings & Admin */}
        <div className="p-4 border-t border-border">
          <div className="flex space-x-2 mb-2">
            {/* <Button
              variant="outline"
              size="sm"
              onClick={clearHistory}
              className="flex-1 group rounded-lg shadow-sm"
              disabled={isResettingKB}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear
            </Button> */}
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleHealthCheck}
              disabled={isResettingKB}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Health
            </Button>
          </div>
          <div className="flex space-x-2 mb-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleResetKB}
              disabled={isResettingKB}
            >
              <X className="mr-2 h-4 w-4" />
              Reset KB
            </Button>
          </div>
          {/* Vectorstore health status */}
          <div className="mt-2 text-xs flex items-center space-x-2">
            <span className={`w-2 h-2 rounded-full ${vectorstoreHealthy === null ? 'bg-gray-300' : vectorstoreHealthy ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span>
              Vectorstore: {vectorstoreHealthy === null ? 'Checking...' : vectorstoreHealthy ? 'Healthy' : 'Unavailable'}
            </span>
          </div>
          {statusMessage && (
            <div className="text-xs text-muted-foreground mt-2">{statusMessage}</div>
          )}
        </div>
        {/* Persistent error banner if vectorstore is down */}
        {vectorstoreHealthy === false && (
          <div className="p-2 text-xs text-center bg-red-100 text-red-800 font-semibold rounded-b shadow">
            Vectorstore is unavailable. Some features may not work.
          </div>
        )}
      </div>
      {/* Main Chat Area - always visible, flush with sidebar */}
      <div className="flex-1 flex flex-col items-stretch justify-between min-h-screen w-0 ml-80" style={{ minWidth: 0 }}>
        {/* Chat Header */}
        <div className="bg-surface border-b border-border p-4 md:p-6 flex items-center justify-between sticky top-0 z-30 shadow-sm w-full">
          <div className="flex items-center gap-3">
            <Bot className="h-6 w-6 text-primary" />
            {currentSession ? (
              isEditingTitle ? (
                <input
                  className="text-xl font-bold bg-surface border-b border-primary focus:outline-none px-2 py-1 rounded"
                  value={editedTitle}
                  autoFocus
                  onChange={e => setEditedTitle(e.target.value)}
                  onBlur={handleSaveTitle}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleSaveTitle();
                    if (e.key === 'Escape') setIsEditingTitle(false);
                  }}
                  style={{ width: '16rem' }}
                />
              ) : (
                <>
                  <span className="text-xl font-bold truncate max-w-xs md:max-w-md">{currentSession.title || 'XOR RAG Assistant'}</span>
                  <button
                    className="ml-2 text-primary hover:text-primary-dark focus:outline-none focus:ring-2 focus:ring-primary rounded"
                    onClick={() => {
                      setEditedTitle(currentSession.title || '');
                      setIsEditingTitle(true);
                    }}
                    title="Rename Conversation"
                    aria-label="Rename Conversation"
                  >
                    <Pencil className="w-4 h-4 inline" />
                  </button>
                </>
              )
            ) : (
              <span className="text-xl font-bold text-muted-foreground">No conversation loaded</span>
            )}
          </div>
          <div className="flex items-center space-x-3">
            {operationState.uploading && (
              <div className="flex items-center space-x-2 text-sm text-primary">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                <span>Processing...</span>
              </div>
            )}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
              <span className="text-sm text-muted-foreground">Online</span>
            </div>
          </div>
        </div>
        {/* Messages */}
        <div className="flex-1 flex flex-col items-stretch justify-end overflow-y-auto p-2 sm:p-4 md:p-6 space-y-4 md:space-y-6 bg-background relative custom-scrollbar w-full" style={{minHeight: '60vh'}} role="log" aria-live="polite" aria-label="Chat messages">
          <div className="flex flex-col items-stretch w-full justify-end flex-1">
            {/* Always render all chat bubbles for currentSession.messages */}
            {memoizedMessages ? (
              <>
                {memoizedMessages}
                {/* Streaming Assistant Bubble */}
                {renderStreamingAssistantBubble()}
              </>
            ) : (
              // Only show welcome card if there are truly no messages
              <div className="flex items-center justify-center h-full w-full flex-1">
                <Card variant="elevated" glow className="p-12 text-center max-w-lg rounded-lg shadow-lg mx-auto">
                  <div className="text-6xl mb-6">🤖</div>
                  <h3 className="text-2xl font-bold mb-4 text-foreground">
                    Welcome to XOR RAG
                  </h3>
                  <p className="text-muted-foreground mb-6 leading-relaxed">
                    Start a conversation or upload documents to begin. Your AI assistant is ready to help 
                    with intelligent document-based questions and analysis.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Button 
                      onClick={() => fileInputRef.current?.click()}
                      variant="outline"
                      className="group rounded-lg shadow-sm"
                    >
                      <Upload className="mr-2 h-4 w-4 group-hover:-translate-y-1 transition-transform duration-300" />
                      Upload Documents
                    </Button>
                    <Button 
                      onClick={createSession}
                      variant="primary"
                      className="group rounded-lg shadow-sm"
                    >
                      Start Chatting
                    </Button>
                  </div>
                </Card>
              </div>
            )}
          </div>
          {operationState.sending && streamingStatus !== 'streaming' && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-2xl">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-elevated border border-border flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <Card variant="elevated" className="p-4 rounded-lg shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-sm text-muted-foreground">Thinking...</span>
                  </div>
                </Card>
              </div>
            </div>
          )}
          {/* Floating scroll-to-bottom button */}
          {showScrollButton && (
            <button
              className="fixed bottom-24 right-6 z-40 bg-primary text-white rounded-full p-3 shadow-lg hover:bg-primary-dark transition"
              onClick={() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })}
              aria-label="Scroll to bottom"
            >
              <ArrowRight className="rotate-90 h-5 w-5" />
            </button>
          )}
          <div ref={messagesEndRef} />
        </div>
        {/* Input Area - always at the bottom */}
        <div className="bg-surface border-t border-border p-2 sm:p-4 md:p-6 flex items-end gap-2 md:gap-4 w-full sticky bottom-0 z-20">
          <form onSubmit={handleSendMessage} className="flex items-end w-full gap-2 md:gap-4">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx,.doc,.txt"
              multiple
              className="hidden"
            />
            <div className="flex-1 relative">
              <Card variant="elevated" className="overflow-hidden rounded-lg shadow-sm">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask me anything about your documents..."
                  className="w-full p-4 bg-transparent text-foreground placeholder-muted-foreground focus:outline-none resize-none min-h-[60px] max-h-32 rounded-lg"
                  disabled={operationState.sending || streamingStatus === 'streaming'}
                  rows={1}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
              </Card>
            </div>
            <Button
              type="submit"
              disabled={!inputValue.trim() || operationState.sending || streamingStatus === 'streaming'}
              className="p-4 group rounded-full shadow-md"
              size="lg"
            >
              <Send className="h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;